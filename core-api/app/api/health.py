from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.api.deps import Db
from app.core.config import get_settings
from app.core.limits import redis_client

router = APIRouter(tags=["System"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/health")
def health(db: Db) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT version_num FROM alembic_version"))
        cache = redis_client()
        if cache:
            cache.ping()
    except Exception:
        raise HTTPException(503, "A dependency is unavailable or migrations are missing") from None
    return {
        "status": "ok",
        "database": db.bind.dialect.name,
        "cache": "redis" if cache else "local-memory",
        "environment": get_settings().environment,
        "mail": get_settings().mail_mode,
    }
