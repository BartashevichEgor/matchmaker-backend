import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import IntegrityError

from app import schemas as s
from app.api.deps import CurrentUser, Db
from app.core.config import get_settings
from app.core.limits import limit
from app.core.security import DUMMY_HASH, code_digest, decode_token, password_hash, token
from app.models import EmailCode, Profile, RefreshSession, User
from app.services.mail import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])
CSRF_COOKIE_NAME = "matchmaker_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"


def throttle(request: Request, action: str, email: str):
    address = request.client.host if request.client else "unknown"
    limit(f"{action}:ip:{address}", 30, 300)
    limit(f"{action}:email:{email}", 5, 300)


def make_code(db, user, purpose):
    code = f"{secrets.randbelow(1000000):06d}"
    db.merge(
        EmailCode(
            user_id=user.id,
            purpose=purpose,
            digest=code_digest(user.id, purpose, code),
            expires_at=int(time.time()) + 600,
            attempts=0,
        )
    )
    return code


def make_verification_credentials(db, user):
    code = make_code(db, user, "verify")
    link_token = secrets.token_urlsafe(48)
    db.merge(
        EmailCode(
            user_id=user.id,
            purpose="verify_link",
            digest=code_digest(user.id, "verify_link", link_token),
            expires_at=int(time.time()) + 86400,
            attempts=0,
        )
    )
    return code, link_token


def consume_credential(db, user, purpose, value):
    record = db.scalar(
        select(EmailCode).where(EmailCode.user_id == user.id, EmailCode.purpose == purpose).with_for_update()
    )
    if not record or record.expires_at <= time.time() or record.attempts >= 5:
        raise HTTPException(400, "Invalid or expired verification credential")
    if not hmac.compare_digest(record.digest, code_digest(user.id, purpose, value)):
        record.attempts += 1
        db.commit()
        raise HTTPException(400, "Invalid or expired verification credential")
    db.delete(record)


def complete_verification(db, user, consumed_purpose):
    other_purpose = "verify_link" if consumed_purpose == "verify" else "verify"
    db.query(EmailCode).filter(EmailCode.user_id == user.id, EmailCode.purpose == other_purpose).delete(
        synchronize_session=False
    )
    user.is_verified = True
    db.commit()


def _client_metadata(request: Request):
    settings = get_settings()
    address = request.client.host if request.client else "unknown"
    client_ip_hash = hmac.new(
        settings.jwt_secret.get_secret_value().encode(), address.encode(), hashlib.sha256
    ).hexdigest()
    user_agent = (request.headers.get("user-agent") or "").strip()[:300] or None
    return user_agent, client_ip_hash


def issue_tokens(db, user, request: Request):
    settings = get_settings()
    session_id = uuid4().hex
    user_agent, client_ip_hash = _client_metadata(request)
    db.execute(
        delete(RefreshSession).where(
            RefreshSession.user_id == user.id,
            or_(RefreshSession.revoked.is_(True), RefreshSession.expires_at <= int(time.time())),
        )
    )
    db.add(
        RefreshSession(
            id=session_id,
            user_id=user.id,
            expires_at=int(time.time()) + settings.refresh_days * 86400,
            user_agent=user_agent,
            client_ip_hash=client_ip_hash,
        )
    )
    return s.MobileTokens(
        access_token=token(user, "access", session_id),
        refresh_token=token(user, "refresh", session_id),
        expires_in=settings.access_minutes * 60,
        refresh_expires_in=settings.refresh_days * 86400,
        session_id=session_id,
    )


def authenticate(data: s.Login, db):
    user = db.scalar(select(User).where(User.email == data.email))
    valid = password_hash.verify(data.password, user.hashed_password if user else DUMMY_HASH)
    if not valid or not user or not user.is_active:
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_verified:
        raise HTTPException(403, "Confirm your email first")
    return user


def rotate_refresh(db, refresh_token: str, request: Request):
    payload = decode_token(refresh_token, "refresh")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active or not user.is_verified or user.token_version != payload["ver"]:
        raise HTTPException(401, "Session is no longer valid")
    changed = db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == payload["jti"],
            RefreshSession.user_id == user.id,
            RefreshSession.revoked.is_(False),
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > int(time.time()),
        )
        .values(
            revoked=True,
            revoked_at=datetime.now(UTC),
            revocation_reason="rotated",
            last_used_at=datetime.now(UTC),
        )
    )
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "Refresh token expired or already used")
    result = issue_tokens(db, user, request)
    db.commit()
    return result


def revoke_refresh(db, refresh_token: str, reason: str):
    payload = decode_token(refresh_token, "refresh")
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == payload["jti"],
            RefreshSession.user_id == int(payload["sub"]),
            RefreshSession.revoked.is_(False),
        )
        .values(
            revoked=True,
            revoked_at=datetime.now(UTC),
            revocation_reason=reason,
            last_used_at=datetime.now(UTC),
        )
    )
    db.commit()


def revoke_all_sessions(db, user, reason: str):
    now = datetime.now(UTC)
    db.execute(update(User).where(User.id == user.id).values(token_version=User.token_version + 1))
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id, RefreshSession.revoked.is_(False))
        .values(revoked=True, revoked_at=now, revocation_reason=reason)
    )
    db.commit()


def _web_tokens(tokens: s.MobileTokens):
    return s.WebTokens(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        csrf_token=secrets.token_urlsafe(32),
    )


def _set_refresh_cookie(response: Response, refresh_token: str):
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_days * 86400,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/v1/auth/web",
    )


def _clear_refresh_cookie(response: Response):
    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/v1/auth/web",
    )


def _set_csrf_cookie(response: Response, csrf_token: str):
    settings = get_settings()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.refresh_days * 86400,
        httponly=False,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/v1/auth/web",
    )


def _clear_csrf_cookie(response: Response):
    settings = get_settings()
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        httponly=False,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/v1/auth/web",
    )


def _check_web_origin(request: Request):
    origin = request.headers.get("origin")
    allowed = {item.rstrip("/") for item in get_settings().cors_origins}
    if not origin or origin.rstrip("/") not in allowed:
        raise HTTPException(403, "Origin is not allowed")


def _check_web_csrf(request: Request):
    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    header = request.headers.get(CSRF_HEADER_NAME)
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(403, "CSRF token is missing or invalid")


def frontend_user(user):
    return s.FrontendUser(
        id=str(user.id),
        username=user.username,
        email=user.email,
        onboarding_mode=user.onboarding_mode,
        created_at=user.created_at,
    )


@router.post("/register", response_model=s.Message, status_code=201)
async def register(data: s.Register, request: Request, db: Db):
    throttle(request, "register", data.email)
    if db.scalar(select(User.id).where(User.email == data.email)):
        raise HTTPException(409, "Email already registered")
    if db.scalar(select(User.id).where(User.username == data.username)):
        raise HTTPException(409, "Username already taken")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=password_hash.hash(data.password),
        onboarding_mode=data.mode,
    )
    db.add(user)
    try:
        db.flush()
        db.add(Profile(user_id=user.id))
        code, link_token = make_verification_credentials(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email or username already registered") from None
    await send_verification_email(user.email, code, link_token)
    return s.Message(message="Account created. Check your email to verify it.")


@router.post("/verify-email", response_model=s.Message)
def verify_email(data: s.Verify, request: Request, db: Db):
    throttle(request, "verify", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not user.is_active:
        raise HTTPException(400, "Invalid or expired verification credential")
    consume_credential(db, user, "verify", data.code)
    complete_verification(db, user, "verify")
    return s.Message(message="Email confirmed. You can sign in.")


@router.post("/verify-email-link", response_model=s.Message)
def verify_email_link(data: s.VerifyLinkInput, request: Request, db: Db):
    throttle(request, "verify-link", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not user.is_active:
        raise HTTPException(400, "Invalid or expired verification credential")
    consume_credential(db, user, "verify_link", data.token)
    complete_verification(db, user, "verify_link")
    return s.Message(message="Email confirmed. You can sign in.")


@router.post("/resend-verification", response_model=s.Message)
async def resend(data: s.EmailInput, request: Request, db: Db):
    throttle(request, "resend", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if user and user.is_active and not user.is_verified:
        code, link_token = make_verification_credentials(db, user)
        db.commit()
        await send_verification_email(user.email, code, link_token)
    return s.Message(message="If verification is needed, a new email has been sent.")


@router.post("/login", response_model=s.Tokens)
@router.post("/mobile/login", response_model=s.MobileTokens)
def mobile_login(data: s.Login, request: Request, db: Db):
    throttle(request, "login", data.email)
    user = authenticate(data, db)
    result = issue_tokens(db, user, request)
    db.commit()
    return result


@router.post("/web/login", response_model=s.WebTokens)
def web_login(data: s.Login, request: Request, response: Response, db: Db):
    _check_web_origin(request)
    throttle(request, "login", data.email)
    user = authenticate(data, db)
    result = issue_tokens(db, user, request)
    db.commit()
    _set_refresh_cookie(response, result.refresh_token)
    web_tokens = _web_tokens(result)
    _set_csrf_cookie(response, web_tokens.csrf_token)
    return web_tokens


@router.post("/refresh", response_model=s.Tokens)
@router.post("/mobile/refresh", response_model=s.MobileTokens)
def mobile_refresh(data: s.RefreshInput, db: Db, request: Request):
    limit(f"refresh:{request.client.host if request.client else 'unknown'}", 60, 300)
    return rotate_refresh(db, data.refresh_token, request)


@router.post("/web/refresh", response_model=s.WebTokens)
def web_refresh(request: Request, response: Response, db: Db):
    _check_web_origin(request)
    _check_web_csrf(request)
    limit(f"refresh:{request.client.host if request.client else 'unknown'}", 60, 300)
    value = request.cookies.get(get_settings().refresh_cookie_name)
    if not value:
        raise HTTPException(401, "Refresh cookie is missing")
    result = rotate_refresh(db, value, request)
    _set_refresh_cookie(response, result.refresh_token)
    web_tokens = _web_tokens(result)
    _set_csrf_cookie(response, web_tokens.csrf_token)
    return web_tokens


@router.post("/mobile/logout", response_model=s.Message)
def mobile_logout(data: s.RefreshInput, db: Db):
    revoke_refresh(db, data.refresh_token, "logout")
    return s.Message(message="Session ended.")


@router.post("/web/logout", response_model=s.Message)
def web_logout(request: Request, response: Response, db: Db):
    _check_web_origin(request)
    _check_web_csrf(request)
    value = request.cookies.get(get_settings().refresh_cookie_name)
    if value:
        try:
            revoke_refresh(db, value, "logout")
        except HTTPException:
            db.rollback()
    _clear_refresh_cookie(response)
    _clear_csrf_cookie(response)
    return s.Message(message="Session ended.")


@router.post("/logout", response_model=s.Message)
@router.post("/web/logout-all", response_model=s.Message)
def logout_all(user: CurrentUser, db: Db, response: Response):
    revoke_all_sessions(db, user, "logout_all")
    _clear_refresh_cookie(response)
    _clear_csrf_cookie(response)
    return s.Message(message="All sessions ended.")


@router.get("/sessions", response_model=list[s.SessionRead])
def sessions(user: CurrentUser, db: Db):
    return db.scalars(
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked.is_(False),
            RefreshSession.expires_at > int(time.time()),
        )
        .order_by(RefreshSession.created_at.desc())
        .limit(100)
    ).all()


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: str, user: CurrentUser, db: Db):
    changed = db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == session_id,
            RefreshSession.user_id == user.id,
            RefreshSession.revoked.is_(False),
        )
        .values(
            revoked=True,
            revoked_at=datetime.now(UTC),
            revocation_reason="user_revoked",
        )
    )
    if changed.rowcount != 1:
        raise HTTPException(404, "Session not found")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/session", response_model=s.FrontendUser)
def session(user: CurrentUser):
    return frontend_user(user)


@router.post("/forgot-password", response_model=s.Message)
async def forgot(data: s.EmailInput, request: Request, db: Db):
    throttle(request, "forgot", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if user and user.is_active:
        code = make_code(db, user, "reset")
        db.commit()
        await send_password_reset_email(user.email, code)
    return s.Message(message="If the account exists, a reset email has been sent.")


@router.post("/reset-password", response_model=s.Message)
def reset(data: s.ResetPassword, request: Request, db: Db):
    throttle(request, "reset", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not user.is_active:
        raise HTTPException(400, "Invalid or expired verification credential")
    consume_credential(db, user, "reset", data.code)
    user.hashed_password = password_hash.hash(data.password)
    revoke_all_sessions(db, user, "password_reset")
    return s.Message(message="Password changed. Sign in again.")
