"""Typed, validated application configuration.

Values come from environment variables and an optional `.env` file at the
repository root. No `os.environ` reads live in feature modules.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./data/fleng.db"
# Only acceptable in development; `model_validator` refuses it in production.
DEV_ACCESS_SECRET = "dev-insecure-access-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", BACKEND_ROOT.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    port: int = 3001
    http_max_body_bytes: int = Field(default=131072, ge=1024, le=1048576)
    database_url: str = DEFAULT_DATABASE_URL
    cors_origin: str = "http://localhost:3000"
    # Static frontend directory served by this app. `None` uses the repository
    # `frontend/` directory (resolved relative to this file).
    frontend_dir: str | None = None

    # ── Authentication ──────────────────────────────────────────────────────
    jwt_access_secret: str = DEV_ACCESS_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    refresh_cookie_name: str = "fleng_refresh"
    refresh_cookie_path: str = "/api/v1/auth"
    # `None` derives from `APP_ENV`: secure cookies in production only.
    cookie_secure: bool | None = None
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Learning dates use one server policy; clients cannot move the streak clock.
    learning_timezone: str = "UTC"
    reset_token_minutes: int = Field(default=30, ge=1, le=1440)
    reset_rate_per_hour: int = Field(default=5, ge=1)
    reset_delivery: Literal["disabled", "smtp"] = "disabled"
    reset_url: str = "http://localhost:3001/reset-password.html"
    smtp_host: str = "localhost"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = "noreply@example.com"
    smtp_starttls: bool = True

    ai_enabled: bool = False
    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = ""
    ai_structured_outputs: bool = False
    ai_max_output_tokens: int = Field(default=800, ge=1, le=8192)
    ai_request_timeout: float = Field(default=30, gt=0, le=300)
    ai_max_input_chars: int = Field(default=4000, ge=1, le=16000)
    ai_max_response_chars: int = Field(default=16000, ge=1, le=64000)
    ai_history_messages: int = Field(default=20, ge=2, le=100)
    ai_history_chars: int = Field(default=16000, ge=1, le=100000)
    ai_messages_per_conversation: int = Field(default=200, ge=2, le=1000)
    ai_conversations_per_user: int = Field(default=50, ge=1, le=500)
    ai_requests_per_minute: int = Field(default=10, ge=1)
    ai_daily_requests: int = Field(default=100, ge=1)
    ai_daily_token_budget: int = Field(default=100000, ge=1)
    ai_concurrency: int = Field(default=4, ge=1, le=100)

    @field_validator("learning_timezone")
    @classmethod
    def _timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown learning timezone") from exc
        return value

    @field_validator("openrouter_base_url")
    @classmethod
    def _provider_url(cls, value: str) -> str:
        from urllib.parse import urlsplit

        parts = urlsplit(value)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or parts.username
            or parts.query
            or parts.fragment
        ):
            raise ValueError("OpenRouter base URL must be an HTTPS URL")
        return value.rstrip("/")

    @field_validator("openrouter_model")
    @classmethod
    def _model(cls, value: str) -> str:
        import re

        if value and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.:/-]+", value):
            raise ValueError("Use a provider/model identifier")
        return value

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Use async drivers and resolve local SQLite files against backend/."""
        if value.startswith(("sqlite://", "sqlite+aiosqlite://")):
            url = make_url(value)
            database = url.database
            if not database or database == ":memory:":
                return value.replace("sqlite://", "sqlite+aiosqlite://", 1)
            path = Path(database).expanduser()
            if not path.is_absolute():
                path = BACKEND_ROOT / path
            url = url.set(database=str(path.resolve()))
            return url.set(drivername="sqlite+aiosqlite").render_as_string(hide_password=False)
        if value.startswith("postgresql+asyncpg://"):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def _reject_dev_secrets_in_production(self) -> "Settings":
        if self.app_env == "production" and self.jwt_access_secret == DEV_ACCESS_SECRET:
            raise ValueError("JWT_ACCESS_SECRET must be set in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origin.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure


@lru_cache
def get_settings() -> Settings:
    return Settings()
