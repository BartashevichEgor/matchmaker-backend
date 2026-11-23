import pytest

from app.core.config import Settings

BASE_PRODUCTION = {
    "environment": "production",
    "jwt_secret": "test-only-secret-not-for-any-real-deployment-12345",
    "database_url": "postgresql+psycopg://user:password@db/matchmaker",
    "redis_url": "redis://redis:6379/0",
    "mail_mode": "smtp",
    "mail_server": "smtp.example.com",
    "refresh_cookie_secure": True,
    "web_base_url": "https://app.example.com",
}


def test_production_rejects_authenticated_plaintext_smtp():
    with pytest.raises(ValueError, match="SMTP credentials require TLS"):
        Settings(**BASE_PRODUCTION, mail_use_credentials=True)


def test_settings_reject_both_smtp_tls_modes():
    with pytest.raises(ValueError, match="cannot both be enabled"):
        Settings(**BASE_PRODUCTION, mail_starttls=True, mail_ssl_tls=True)


def test_production_accepts_authenticated_starttls():
    settings = Settings(**BASE_PRODUCTION, mail_use_credentials=True, mail_starttls=True)
    assert settings.mail_starttls is True
