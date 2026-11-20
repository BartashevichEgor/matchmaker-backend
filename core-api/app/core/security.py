import hashlib
import hmac
import time
from uuid import uuid4

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("unused-timing-placeholder-password")


def token(user, kind: str, session_id: str | None = None):
    settings = get_settings()
    lifetime = settings.access_minutes * 60 if kind == "access" else settings.refresh_days * 86400
    payload = {
        "sub": str(user.id),
        "type": kind,
        "ver": user.token_version,
        "iat": int(time.time()),
        "exp": int(time.time()) + lifetime,
        "jti": session_id if kind == "refresh" and session_id else uuid4().hex,
        "iss": settings.jwt_issuer,
        "aud": "matchmaker-api",
    }
    if kind == "access":
        if not session_id:
            raise ValueError("Access tokens require a session id")
        payload["sid"] = session_id
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def decode_token(value: str, kind: str):
    settings = get_settings()
    try:
        data = jwt.decode(
            value,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience="matchmaker-api",
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "type", "ver", "exp", "iat", "jti"]},
        )
        if data["type"] != kind or int(data["sub"]) <= 0:
            raise ValueError("Wrong token type")
        if kind == "access" and not data.get("sid"):
            raise ValueError("Missing session id")
        return data
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}) from None


def code_digest(user_id: int, purpose: str, code: str):
    secret = get_settings().jwt_secret.get_secret_value().encode()
    return hmac.new(secret, f"{user_id}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()
