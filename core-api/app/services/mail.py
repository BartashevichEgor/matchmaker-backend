from uuid import uuid4

from fastapi import HTTPException
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    MultipartSubtypeEnum,
)
from loguru import logger

from app.core.config import get_settings
from app.services.mail_templates import password_reset_email, verification_email


async def _send(email: str, subject: str, plain: str, html: str):
    settings = get_settings()
    if settings.mail_mode == "outbox":
        settings.outbox_dir.mkdir(parents=True, exist_ok=True)
        path = settings.outbox_dir / f"{uuid4().hex}.txt"
        path.write_text(f"To: {email}\nSubject: {subject}\n{plain}", encoding="utf-8")
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
                subject=subject,
                recipients=[email],
                body=html,
                alternative_body=plain,
                subtype=MessageType.html,
                multipart_subtype=MultipartSubtypeEnum.alternative,
            )
        )
    except Exception:
        logger.error("Email delivery failed")
        raise HTTPException(503, "Email unavailable. Please try again later.") from None


async def send_verification_email(email: str, code: str, link_token: str):
    message = verification_email(email, code, link_token)
    await _send(email, message.subject, message.plain, message.html)


async def send_password_reset_email(email: str, code: str):
    message = password_reset_email(email, code)
    await _send(email, message.subject, message.plain, message.html)
