import smtplib
import ssl

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import Db
from app.core.config import get_settings
from app.core.limits import redis_client

router = APIRouter(tags=["System"])
SMTP_PROBE_TIMEOUT_SECONDS = 2


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/health", response_model=None)
@router.get("/api/health", include_in_schema=False, response_model=None)
def health(db: Db):
    """Return only an operational health signal; never expose dependency errors."""
    settings = get_settings()
    dependencies = {"database": "UP", "cache": "UP", "mail": "UP"}
    try:
        # This query deliberately goes through the configured SQLAlchemy engine:
        # it verifies a real connection for both PostgreSQL and SQLite.
        db.execute(text("SELECT 1"))
    except Exception:
        dependencies["database"] = "DOWN"
    try:
        cache = redis_client()
    except Exception:
        dependencies["cache"] = "DOWN"
    else:
        if cache:
            try:
                cache.ping()
            except Exception:
                dependencies["cache"] = "DOWN"
        else:
            dependencies["cache"] = "local-memory"

    if settings.mail_mode == "outbox":
        dependencies["mail"] = "outbox"
    else:
        try:
            if settings.mail_ssl_tls:
                with smtplib.SMTP_SSL(
                    settings.mail_server,
                    settings.mail_port,
                    timeout=SMTP_PROBE_TIMEOUT_SECONDS,
                    context=ssl.create_default_context(),
                ) as smtp:
                    smtp.ehlo()
                    if settings.mail_use_credentials:
                        smtp.login(settings.mail_username, settings.mail_password.get_secret_value())
                    smtp.noop()
            else:
                with smtplib.SMTP(
                    settings.mail_server, settings.mail_port, timeout=SMTP_PROBE_TIMEOUT_SECONDS
                ) as smtp:
                    smtp.ehlo()
                    if settings.mail_starttls:
                        smtp.starttls(context=ssl.create_default_context())
                        smtp.ehlo()
                    if settings.mail_use_credentials:
                        smtp.login(settings.mail_username, settings.mail_password.get_secret_value())
                    smtp.noop()
        except Exception:
            dependencies["mail"] = "DOWN"

    ready = all(value not in {"DOWN"} for value in dependencies.values())
    response = {
        "status": "UP" if ready else "DOWN",
        "dependencies": dependencies,
        "environment": settings.environment,
    }
    if ready:
        response["database"] = db.bind.dialect.name
    return response if ready else JSONResponse(status_code=503, content=response)
