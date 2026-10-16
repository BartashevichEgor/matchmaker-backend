from uuid import uuid4

from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from loguru import logger

from app.core.config import get_settings


async def send_code(email: str, code: str, purpose: str):
    settings = get_settings()
    body = f"Matchmaker\nPurpose: {purpose}\nCode: {code}\nExpires in 10 minutes.\n"
    if settings.mail_mode == "outbox":
        settings.outbox_dir.mkdir(parents=True, exist_ok=True)
        path = settings.outbox_dir / f"{uuid4().hex}.txt"
        path.write_text(f"To: {email}\n{body}", encoding="utf-8")
        logger.info("Development email saved to local outbox")
        return
    try:
        config = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password.get_secret_value(),
            MAIL_FROM=settings.mail_from,
            MAIL_SERVER=settings.mail_server,
            MAIL_PORT=settings.mail_port,
            MAIL_STARTTLS=settings.mail_starttls,
            MAIL_SSL_TLS=settings.mail_ssl_tls,
            USE_CREDENTIALS=settings.mail_use_credentials,
            VALIDATE_CERTS=True,
        )
        await FastMail(config).send_message(
            MessageSchema(
                subject="Matchmaker verification code",
                recipients=[email],
                body=body,
                subtype=MessageType.plain,
            )
        )
    except Exception:
        logger.error("Email delivery failed")
        raise HTTPException(503, "Email unavailable. Please request a new code later.") from None
