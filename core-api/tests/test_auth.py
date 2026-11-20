import time

import jwt
from sqlalchemy import select

from app.core.config import get_settings
from app.models import EmailCode, RefreshSession, User
from tests.conftest import read_code, read_link_token

PASSWORD = "ValidPassword123!"


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

    refreshed = client.post("/api/v1/auth/web/refresh", headers=origin)
    assert refreshed.status_code == 200
    assert "refresh_token" not in refreshed.json()
    assert db.scalar(select(RefreshSession).where(RefreshSession.id == payload["sid"])).revoked

    logout = client.post("/api/v1/auth/web/logout", headers=origin)
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
    assert response.status_code == 429 and response.headers["retry-after"] == "300"


def test_admin_escalation_rejected(client, account):
    _, headers, _ = account()
    assert client.patch("/api/v1/profiles/me", headers=headers, json={"is_admin": True}).status_code == 422
    assert (
        client.post("/api/v1/admin/skills", headers=headers, json={"name": "Unauthorized"}).status_code == 403
    )
