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
    redis_url: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    mail_mode: Literal["outbox", "smtp"] = "outbox"
    mail_server: str = "localhost"
    mail_port: int = 1025
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@matchmaker.local"
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = False
    outbox_dir: Path = ROOT / ".local" / "outbox"

    @model_validator(mode="after")
    def validate_runtime(self):
        if len(self.jwt_secret.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        if self.environment == "production":
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError("Production requires PostgreSQL")
            if not self.redis_url or self.mail_mode != "smtp":
                raise ValueError("Production requires Redis and SMTP")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
