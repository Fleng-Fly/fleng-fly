"""Typed, validated application configuration.

Values come from environment variables and an optional `.env` file at the
repository root. No `os.environ` reads live in feature modules.
"""

from functools import lru_cache
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+asyncpg://fleng:fleng@localhost:5432/fleng"
DEFAULT_DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


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
    dev_user_id: UUID = DEFAULT_DEV_USER_ID

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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origin.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
