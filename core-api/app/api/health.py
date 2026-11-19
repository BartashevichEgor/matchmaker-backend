from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import Db
from app.core.config import get_settings
from app.core.limits import redis_client

router = APIRouter(tags=["System"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/health", response_model=None)
@router.get("/api/health", include_in_schema=False, response_model=None)
def health(db: Db):
    """Return only an operational health signal; never expose dependency errors."""
    try:
        # This query deliberately goes through the configured SQLAlchemy engine:
        # it verifies a real connection for both PostgreSQL and SQLite.
        db.execute(text("SELECT 1"))
        cache = redis_client()
        if cache:
            cache.ping()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "DOWN"})
    return {
        "status": "UP",
        "database": db.bind.dialect.name,
        "cache": "redis" if cache else "local-memory",
        "environment": get_settings().environment,
        "mail": get_settings().mail_mode,
    }
