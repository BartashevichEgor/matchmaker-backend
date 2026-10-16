import hmac
import secrets
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app import schemas as s
from app.api.deps import CurrentUser, Db
from app.core.config import get_settings
from app.core.limits import limit
from app.core.security import DUMMY_HASH, code_digest, decode_token, password_hash, token
from app.models import EmailCode, Profile, RefreshSession, User
from app.services.mail import send_code

router = APIRouter(prefix="/auth", tags=["Auth"])


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


def consume_code(db, user, purpose, code):
    record = db.scalar(
        select(EmailCode)
        .where(
            EmailCode.user_id == user.id,
            EmailCode.purpose == purpose,
        )
        .with_for_update()
    )
    if not record or record.expires_at <= time.time() or record.attempts >= 5:
        raise HTTPException(400, "Invalid or expired code")
    if not hmac.compare_digest(record.digest, code_digest(user.id, purpose, code)):
        record.attempts += 1
        db.commit()
        raise HTTPException(400, "Invalid or expired code")
    db.delete(record)


def issue_tokens(db, user):
    settings = get_settings()
    session_id = uuid4().hex
    db.add(
        RefreshSession(
            id=session_id,
            user_id=user.id,
            expires_at=int(time.time()) + settings.refresh_days * 86400,
        )
    )
    return s.Tokens(
        access_token=token(user, "access"),
        refresh_token=token(user, "refresh", session_id),
        expires_in=settings.access_minutes * 60,
    )


@router.post("/register", response_model=s.Message, status_code=201)
async def register(data: s.Register, request: Request, db: Db):
    throttle(request, "register", data.email)
    if db.scalar(select(User.id).where(User.email == data.email)):
        raise HTTPException(409, "Email already registered")
    if db.scalar(select(User.id).where(User.username == data.username)):
        raise HTTPException(409, "Username already taken")
    user = User(username=data.username, email=data.email, hashed_password=password_hash.hash(data.password))
    db.add(user)
    try:
        db.flush()
        db.add(Profile(user_id=user.id))
        code = make_code(db, user, "verify")
        db.commit()
    except IntegrityError:
        db.rollback()
        # The pre-check provides a precise answer in the usual case.  This
        # fallback covers two concurrent registrations without exposing SQL.
        raise HTTPException(409, "Email or username already registered") from None
    await send_code(user.email, code, "verify")
    return s.Message(message="Account created. Check your email for a verification code.")


@router.post("/verify-email", response_model=s.Message)
def verify_email(data: s.Verify, request: Request, db: Db):
    throttle(request, "verify", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not user.is_active:
        raise HTTPException(400, "Invalid or expired code")
    consume_code(db, user, "verify", data.code)
    user.is_verified = True
    db.commit()
    return s.Message(message="Email confirmed. You can sign in.")


@router.post("/resend-verification", response_model=s.Message)
async def resend(data: s.EmailInput, request: Request, db: Db):
    throttle(request, "resend", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if user and user.is_active and not user.is_verified:
        code = make_code(db, user, "verify")
        db.commit()
        await send_code(user.email, code, "verify")
    return s.Message(message="If verification is needed, a new code has been sent.")


@router.post("/login", response_model=s.Tokens)
def login(data: s.Login, request: Request, db: Db):
    throttle(request, "login", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    valid = password_hash.verify(data.password, user.hashed_password if user else DUMMY_HASH)
    if not valid or not user or not user.is_active:
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_verified:
        raise HTTPException(403, "Confirm your email first")
    result = issue_tokens(db, user)
    db.commit()
    return result


@router.post("/refresh", response_model=s.Tokens)
def refresh(data: s.RefreshInput, db: Db, request: Request):
    limit(f"refresh:{request.client.host if request.client else 'unknown'}", 60, 300)
    payload = decode_token(data.refresh_token, "refresh")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active or not user.is_verified or user.token_version != payload["ver"]:
        raise HTTPException(401, "Session is no longer valid")
    # An atomic update makes a refresh token single-use, including concurrent requests.
    changed = db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == payload["jti"],
            RefreshSession.user_id == user.id,
            RefreshSession.revoked.is_(False),
            RefreshSession.expires_at > int(time.time()),
        )
        .values(revoked=True)
    )
    if changed.rowcount != 1:
        raise HTTPException(401, "Refresh token expired or already used")
    result = issue_tokens(db, user)
    db.commit()
    return result


@router.post("/logout", response_model=s.Message)
def logout(user: CurrentUser, db: Db):
    # Increment in SQL to avoid lost updates under concurrent logout requests.
    db.execute(update(User).where(User.id == user.id).values(token_version=User.token_version + 1))
    db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    db.commit()
    return s.Message(message="All sessions ended.")


@router.post("/forgot-password", response_model=s.Message)
async def forgot(data: s.EmailInput, request: Request, db: Db):
    throttle(request, "forgot", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if user and user.is_active:
        code = make_code(db, user, "reset")
        db.commit()
        await send_code(user.email, code, "reset")
    return s.Message(message="If the account exists, a reset code has been sent.")


@router.post("/reset-password", response_model=s.Message)
def reset(data: s.ResetPassword, request: Request, db: Db):
    throttle(request, "reset", data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not user.is_active:
        raise HTTPException(400, "Invalid or expired code")
    consume_code(db, user, "reset", data.code)
    user.hashed_password = password_hash.hash(data.password)
    db.execute(update(User).where(User.id == user.id).values(token_version=User.token_version + 1))
    db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    db.commit()
    return s.Message(message="Password changed. Sign in again.")
