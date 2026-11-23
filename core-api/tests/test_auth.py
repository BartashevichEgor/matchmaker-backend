import time

import jwt
from sqlalchemy import select

from app.api import auth as auth_api
from app.core.config import get_settings
from app.core.limits import _local
from app.models import EmailCode, RefreshSession, User
from tests.conftest import read_code, read_link_token

PASSWORD = "ValidPassword123!"


def test_request_body_limit_rejects_oversized_payload(client):
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/register",
        content=b"{" + b"x" * settings.max_request_body_bytes + b"}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_registration_validation_and_no_password_leak(client):
    for body in (
        {"username": "valid-user", "email": "invalid", "password": PASSWORD, "password_confirm": PASSWORD},
        {
            "username": "valid-user",
            "email": "a@example.com",
            "password": "short",
            "password_confirm": "short",
        },
        {
            "username": "valid-user",
            "email": "a@example.com",
            "password": PASSWORD,
            "password_confirm": "different",
        },
        {"username": "   ", "email": "a@example.com", "password": PASSWORD, "password_confirm": PASSWORD},
    ):
        response = client.post("/api/v1/auth/register", json=body)
        assert response.status_code == 422
        assert PASSWORD not in response.text
        assert '"input"' not in response.text


def test_registration_requires_and_persists_mode(client, db):
    base = {"username": "mode-user", "email": "mode@example.com", "password": PASSWORD}
    assert client.post("/api/v1/auth/register", json=base).status_code == 422
    assert client.post("/api/v1/auth/register", json={**base, "mode": "both"}).status_code == 422
    response = client.post("/api/v1/auth/register", json={**base, "mode": "project"})
    assert response.status_code == 201
    assert db.scalar(select(User).where(User.email == base["email"])).onboarding_mode == "project"


def test_react_register_payload_and_session_shape(client, db):
    data = {
        "username": "  Web User  ",
        "email": "web@example.com",
        "password": "password",
        "mode": "developer",
    }
    assert client.post("/api/v1/auth/register", json=data).status_code == 201
    code = read_code(data["email"])
    assert (
        client.post("/api/v1/auth/verify-email", json={"email": data["email"], "code": code}).status_code
        == 200
    )
    login = client.post("/api/v1/auth/login", json={"email": data["email"], "password": data["password"]})
    assert login.status_code == 200
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(db.scalar(select(User.id).where(User.email == data["email"])))
    assert body["username"] == "Web User"
    assert body["email"] == data["email"]
    assert isinstance(body["createdAt"], str)


def test_registration_duplicate_and_unverified_login(client, db):
    data = {
        "username": "test-user",
        "email": "User@Example.com",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        "mode": "developer",
    }
    assert client.post("/api/v1/auth/register", json=data).status_code == 201
    assert client.post("/api/v1/auth/register", json=data).status_code == 409
    same_name = {**data, "email": "another@example.com"}
    response = client.post("/api/v1/auth/register", json=same_name)
    assert response.status_code == 409 and response.json()["detail"] == "Username already taken"
    response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": PASSWORD})
    assert response.status_code == 403
    user = db.scalar(select(User))
    assert user.hashed_password != PASSWORD and user.hashed_password.startswith("$argon2")
    assert user.email == "user@example.com"
    assert user.username == "test-user"


def test_verification_single_use_and_limits(client, db):
    email = "verify@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "verify-user",
            "email": email,
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "mode": "developer",
        },
    )
    code = read_code(email)
    assert client.post("/api/v1/auth/verify-email", json={"email": email, "code": code}).status_code == 200
    assert client.post("/api/v1/auth/verify-email", json={"email": email, "code": code}).status_code == 400
    assert db.scalar(select(EmailCode)) is None


def test_verification_rejects_after_five_failed_attempts(client):
    email = "attempts@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"username": "attempts-user", "email": email, "password": PASSWORD, "mode": "developer"},
    )
    code = read_code(email)
    wrong_code = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert (
            client.post("/api/v1/auth/verify-email", json={"email": email, "code": wrong_code}).status_code
            == 400
        )
    _local.clear()
    assert client.post("/api/v1/auth/verify-email", json={"email": email, "code": code}).status_code == 400


def test_expired_verification(client, db):
    email = "expired@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "expired-user",
            "email": email,
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "mode": "developer",
        },
    )
    record = db.scalar(select(EmailCode))
    record.expires_at = int(time.time()) - 1
    db.commit()
    assert (
        client.post("/api/v1/auth/verify-email", json={"email": email, "code": read_code(email)}).status_code
        == 400
    )


def test_verification_link_is_single_use(client, db):
    email = "link@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "link-user", "email": email, "password": PASSWORD, "mode": "developer"},
    )
    assert response.status_code == 201
    token = read_link_token(email)
    payload = {"email": email, "token": token}
    assert client.post("/api/v1/auth/verify-email-link", json=payload).status_code == 200
    assert client.post("/api/v1/auth/verify-email-link", json=payload).status_code == 400
    assert db.scalar(select(EmailCode)) is None


def test_verification_link_expiry(client, db):
    email = "expired-link@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"username": "expired-link", "email": email, "password": PASSWORD, "mode": "developer"},
    )
    record = db.scalar(select(EmailCode).where(EmailCode.purpose == "verify_link"))
    record.expires_at = int(time.time()) - 1
    db.commit()
    assert (
        client.post(
            "/api/v1/auth/verify-email-link", json={"email": email, "token": read_link_token(email)}
        ).status_code
        == 400
    )


def test_resend_replaces_verification_credentials(client, monkeypatch):
    email = "resend@example.com"
    codes = iter((123456, 654321))
    monkeypatch.setattr(auth_api.secrets, "randbelow", lambda _: next(codes))
    client.post(
        "/api/v1/auth/register",
        json={"username": "resend-user", "email": email, "password": PASSWORD, "mode": "developer"},
    )
    old_code = read_code(email)
    old_link = read_link_token(email)
    assert client.post("/api/v1/auth/resend-verification", json={"email": email}).status_code == 200
    # The outbox is on a filesystem where multiple writes can share one
    # timestamp, so assert the deterministic code generated by the patched RNG.
    new_code = "654321"
    assert new_code != old_code
    assert (
        client.post("/api/v1/auth/verify-email", json={"email": email, "code": old_code}).status_code == 400
    )
    assert (
        client.post("/api/v1/auth/verify-email-link", json={"email": email, "token": old_link}).status_code
        == 400
    )
    assert (
        client.post("/api/v1/auth/verify-email", json={"email": email, "code": new_code}).status_code == 200
    )


def test_web_cookie_login_refresh_sessions_and_logout(client, account, db):
    user, _, _ = account("web-cookie@example.com")
    origin = {"Origin": "http://localhost:5173"}
    assert (
        client.post(
            "/api/v1/auth/web/login",
            json={"email": user["email"], "password": PASSWORD},
        ).status_code
        == 403
    )
    login = client.post(
        "/api/v1/auth/web/login",
        json={"email": user["email"], "password": PASSWORD},
        headers=origin,
    )
    assert login.status_code == 200
    assert "refresh_token" not in login.json()
    assert login.cookies.get("matchmaker_refresh")
    csrf = login.json()["csrf_token"]
    assert csrf == login.cookies.get(auth_api.CSRF_COOKIE_NAME)
    access = login.json()["access_token"]
    payload = jwt.decode(
        access,
        get_settings().jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        audience="matchmaker-api",
        issuer=get_settings().jwt_issuer,
    )
    assert payload["sid"]

    sessions = client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {access}"})
    assert sessions.status_code == 200
    assert any(item["id"] == payload["sid"] for item in sessions.json())

    assert client.post("/api/v1/auth/web/refresh", headers=origin).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/web/refresh", headers={**origin, auth_api.CSRF_HEADER_NAME: "wrong-token"}
        ).status_code
        == 403
    )
    refreshed = client.post("/api/v1/auth/web/refresh", headers={**origin, auth_api.CSRF_HEADER_NAME: csrf})
    assert refreshed.status_code == 200
    assert "refresh_token" not in refreshed.json()
    assert db.scalar(select(RefreshSession).where(RefreshSession.id == payload["sid"])) is None
    next_csrf = refreshed.json()["csrf_token"]
    assert next_csrf == refreshed.cookies.get(auth_api.CSRF_COOKIE_NAME)
    active_sessions = client.get(
        "/api/v1/auth/sessions", headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"}
    )
    assert active_sessions.status_code == 200
    assert all(item["id"] != payload["sid"] for item in active_sessions.json())

    assert (
        client.post(
            "/api/v1/auth/web/logout", headers={**origin, auth_api.CSRF_HEADER_NAME: csrf}
        ).status_code
        == 403
    )
    logout = client.post("/api/v1/auth/web/logout", headers={**origin, auth_api.CSRF_HEADER_NAME: next_csrf})
    assert logout.status_code == 200
    assert logout.cookies.get("matchmaker_refresh") is None


def test_mobile_transport_and_session_revoke(client, account):
    user, _, _ = account("mobile@example.com")
    login = client.post(
        "/api/v1/auth/mobile/login",
        json={"email": user["email"], "password": PASSWORD},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["refresh_token"] and body["session_id"]
    assert body["refresh_expires_in"] == 7 * 86400

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.delete(f"/api/v1/auth/sessions/{body['session_id']}", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/session", headers=headers).status_code == 401


def test_login_refresh_replay_and_logout(client, account):
    user, headers, tokens = account()
    assert "hashed_password" not in user
    assert client.get("/api/v1/users/me").status_code == 401
    assert (
        client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer " + tokens["refresh_token"]}
        ).status_code
        == 401
    )
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )
    next_refresh = response.json()["refresh_token"]
    next_headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert client.post("/api/v1/auth/logout", headers=next_headers).status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": next_refresh}).status_code == 401


def test_expired_access_token(client, account):
    _, _, tokens = account()
    settings = get_settings()
    payload = jwt.decode(
        tokens["access_token"],
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        audience="matchmaker-api",
        issuer=settings.jwt_issuer,
    )
    payload["exp"] = int(time.time()) - 1
    expired = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + expired}).status_code == 401


def test_access_token_rejected_after_refresh_session_expiry(client, account, db):
    _, headers, tokens = account()
    session = db.get(RefreshSession, tokens["session_id"])
    session.expires_at = int(time.time()) - 1
    db.commit()
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_smtp_failure_keeps_account_for_resend(client, db, monkeypatch):
    async def fail_send(self, message):
        raise OSError("smtp unavailable")

    settings = get_settings()
    original_mode = settings.mail_mode
    settings.mail_mode = "smtp"
    monkeypatch.setattr("app.services.mail.FastMail.send_message", fail_send)
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "smtp-failure",
                "email": "smtp-failure@example.com",
                "password": PASSWORD,
                "mode": "developer",
            },
        )
    finally:
        settings.mail_mode = original_mode
    assert response.status_code == 503
    user = db.scalar(select(User).where(User.email == "smtp-failure@example.com"))
    assert user and not user.is_verified


def test_reset_revokes_sessions(client, account):
    user, headers, tokens = account()
    assert client.post("/api/v1/auth/forgot-password", json={"email": user["email"]}).status_code == 200
    new_password = "ChangedPassword123!"
    data = {
        "email": user["email"],
        "code": read_code(user["email"], "reset"),
        "password": new_password,
        "password_confirm": new_password,
    }
    assert client.post("/api/v1/auth/reset-password", json=data).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json=data).status_code == 400
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert (
        client.post("/api/v1/auth/login", json={"email": user["email"], "password": PASSWORD}).status_code
        == 401
    )
    assert (
        client.post("/api/v1/auth/login", json={"email": user["email"], "password": new_password}).status_code
        == 200
    )


def test_rate_limit(client):
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "no@example.com", "password": "wrong"}
            ).status_code
            == 401
        )
    response = client.post("/api/v1/auth/login", json={"email": "no@example.com", "password": "wrong"})
    assert response.status_code == 429 and response.headers["retry-after"] == "900"
    assert response.json() == {"error": "rate_limited"}


def test_login_rate_limit_normalizes_email_case(client):
    for index in range(5):
        email = "No@Example.com" if index % 2 else "no@example.com"
        response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
        assert response.status_code == 401
    response = client.post("/api/v1/auth/login", json={"email": "NO@example.COM", "password": "wrong"})
    assert response.status_code == 429
    assert response.json() == {"error": "rate_limited"}


def test_admin_escalation_rejected(client, account):
    _, headers, _ = account()
    assert client.patch("/api/v1/profiles/me", headers=headers, json={"is_admin": True}).status_code == 422
    assert (
        client.post("/api/v1/admin/skills", headers=headers, json={"name": "Unauthorized"}).status_code == 403
    )
