"""Typed, validated application configuration.

Values come from environment variables and an optional `.env` file at the
repository root. No `os.environ` reads live in feature modules.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+asyncpg://fleng:fleng@localhost:5432/fleng"
# Only acceptable in development; `model_validator` refuses it in production.
DEV_ACCESS_SECRET = "dev-insecure-access-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    port: int = 3001
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

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Accept plain `postgresql://` URLs and use the asyncpg driver."""
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
