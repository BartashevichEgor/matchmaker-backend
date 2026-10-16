from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db import get_db
from app.models import User

Db = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def current_user(db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(credentials.credentials, "access")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active or user.token_version != payload["ver"]:
        raise HTTPException(401, "Session is no longer valid")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def verified_user(user: CurrentUser):
    if not user.is_verified:
        raise HTTPException(403, "Confirm your email first")
    return user


VerifiedUser = Annotated[User, Depends(verified_user)]


def admin_user(user: VerifiedUser):
    if not user.is_admin:
        raise HTTPException(403, "Administrator access required")
    return user


AdminUser = Annotated[User, Depends(admin_user)]
