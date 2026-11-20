from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    environment: Literal["local", "test", "production"] = "local"
    database_url: str = f"sqlite:///{(ROOT / 'local.db').as_posix()}"
    jwt_secret: SecretStr
    jwt_issuer: str = "matchmaker"
    access_minutes: int = Field(default=15, ge=1, le=60)
    refresh_days: int = Field(default=7, ge=1, le=30)
    max_request_body_bytes: int = Field(default=2_000_000, ge=1_024, le=10_000_000)
    redis_url: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    mail_mode: Literal["outbox", "smtp"] = "outbox"
    mail_server: str = "localhost"
    mail_port: int = 1025
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = False
    outbox_dir: Path = ROOT / ".local" / "outbox"
    web_base_url: str = "http://localhost:5173"
    refresh_cookie_name: str = "matchmaker_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    @model_validator(mode="after")
    def validate_runtime(self):
        if len(self.jwt_secret.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        if self.mail_starttls and self.mail_ssl_tls:
            raise ValueError("MAIL_STARTTLS and MAIL_SSL_TLS cannot both be enabled")
        if self.environment == "production":
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError("Production requires PostgreSQL")
            if not self.redis_url or self.mail_mode != "smtp":
                raise ValueError("Production requires Redis and SMTP")
            if not self.refresh_cookie_secure or not self.web_base_url.startswith("https://"):
                raise ValueError("Production web auth requires HTTPS and secure refresh cookies")
            if self.mail_use_credentials and not (self.mail_starttls or self.mail_ssl_tls):
                raise ValueError("Production SMTP credentials require TLS")
        if self.refresh_cookie_samesite == "none" and not self.refresh_cookie_secure:
            raise ValueError("SameSite=None requires secure refresh cookies")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
