"""Typed, validated application configuration.

Values come from environment variables and an optional `.env` file at the
repository root. No `os.environ` reads live in feature modules.
"""

from decimal import Decimal
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
        hide_input_in_errors=True,
    )

    app_env: str = "development"
    port: int = Field(default=3001, ge=1, le=65535)
    # Listen address of `run.py`. Unset = loopback (safe behind nginx/systemd); the
    # Render platform, which routes to the container's public interface, keeps 0.0.0.0.
    host: str | None = None
    trusted_proxy_ips: str = ""
    http_max_body_bytes: int = Field(default=131072, ge=1024, le=1048576)
    database_url: str = DEFAULT_DATABASE_URL
    cors_origin: str = "http://localhost:3000"
    # Render supplies this server-side value even when TLS terminates upstream.
    # Never derive the public origin from client-controlled forwarding headers.
    render_external_url: str = ""
    # Static frontend directory served by this app. `None` uses the repository
    # `frontend/` directory (resolved relative to this file).
    frontend_dir: str | None = None

    auth_login_ip_per_minute: int = Field(default=20, ge=1)
    auth_login_email_per_minute: int = Field(default=10, ge=1)
    auth_register_ip_per_hour: int = Field(default=10, ge=1)

    # ── Authentication ──────────────────────────────────────────────────────
    jwt_access_secret: str = DEV_ACCESS_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # A rotated refresh token may be retried this long (seconds) when its successor was never
    # used: covers a rotation response lost to a navigation or network drop. 0 = strict reuse
    # detection only.
    refresh_reuse_grace_seconds: int = Field(default=10, ge=0, le=60)
    refresh_cookie_name: str = "fleng_refresh"
    refresh_cookie_path: str = "/api/v1/auth"
    # `None` derives from `APP_ENV`: secure cookies in production only.
    cookie_secure: bool | None = None
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Google sign-in (OAuth 2.0 authorization code + PKCE). All three values are
    # required to enable it; leaving any unset keeps the feature off.
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    # Exact callback registered in Google Cloud Console, e.g.
    # https://example.com/api/v1/auth/google/callback. Never derived from request headers.
    google_redirect_uri: str = ""

    # Learning dates use one server policy; clients cannot move the streak clock.
    learning_timezone: str = "UTC"
    reset_token_minutes: int = Field(default=30, ge=1, le=1440)
    reset_rate_per_hour: int = Field(default=5, ge=1)
    reset_delivery: Literal["disabled", "smtp"] = "disabled"
    email_change_url: str = "http://localhost:3001/settings.html"
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
    # Opt-in for the single router id `openrouter/auto`. Its per-request model (and price) is
    # chosen by OpenRouter, so the two AI_*_PRICE_* values are then a hard price CEILING (sent as
    # provider.max_price and used for worst-case holds), and spend is settled from the
    # provider-reported usage.cost only. See docs/ai.md.
    ai_allow_auto_router: bool = False
    ai_max_output_tokens: int = Field(default=800, ge=1, le=8192)
    ai_max_input_tokens: int = Field(default=24000, ge=1, le=128000)
    ai_request_timeout: float = Field(default=30, gt=0, le=300)
    # Longest learner-authored text accepted per request (chat message, explain answer).
    ai_max_message_length: int = Field(default=500, ge=1, le=16000)
    ai_max_response_chars: int = Field(default=16000, ge=1, le=64000)
    ai_history_messages: int = Field(default=20, ge=2, le=100)
    ai_history_chars: int = Field(default=16000, ge=1, le=100000)
    ai_messages_per_conversation: int = Field(default=200, ge=2, le=1000)
    ai_conversations_per_user: int = Field(default=50, ge=1, le=500)
    ai_requests_per_minute: int = Field(default=10, ge=1)
    # Requests per learner per UTC day, counted from persistent ai_usage rows.
    ai_daily_user_limit: int = Field(default=30, ge=1)
    # Per-learner reservation cap. Default = 30 requests x (24000 input + 800 output)
    # so it never pre-empts AI_DAILY_USER_LIMIT; the USD budget is the spend bound.
    ai_daily_token_budget: int = Field(default=750000, ge=1)
    # Global (all workers) in-flight provider requests, and the per-learner bound.
    ai_concurrency: int = Field(default=4, ge=1, le=100)
    ai_max_concurrent_requests: int = Field(default=1, ge=1, le=10)
    # Global provider spend per UTC day, shared by every process via the database.
    ai_daily_budget_usd: Decimal = Field(default=Decimal("1.00"), ge=0, le=100000)
    # Known OpenRouter tariff of OPENROUTER_MODEL in USD per million tokens. They are
    # sent as provider.max_price and used for worst-case reservations. Unset prices
    # keep AI unavailable: an unknown price is never treated as free.
    ai_input_price_per_mtok_usd: Decimal | None = Field(default=None, ge=0, le=10000)
    ai_output_price_per_mtok_usd: Decimal | None = Field(default=None, ge=0, le=10000)

    @field_validator("ai_input_price_per_mtok_usd", "ai_output_price_per_mtok_usd", mode="before")
    @classmethod
    def _blank_price_is_unset(cls, value: object) -> object:
        """An empty `AI_*_PRICE_*=` line (as in the env templates) means "not set", not a crash."""
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("render_external_url")
    @classmethod
    def _render_origin(cls, value: str) -> str:
        from urllib.parse import urlsplit

        if value:
            parts = urlsplit(value)
            if (
                parts.scheme != "https"
                or not parts.hostname
                or "*" in parts.netloc
                or parts.username
                or parts.password
                or parts.path
                or parts.query
                or parts.fragment
            ):
                raise ValueError("RENDER_EXTERNAL_URL must be an exact HTTPS origin")
        return value

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
            or parts.password
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
            if database == ":memory:":
                # render_as_string() would percent-encode ":memory:" into a file name.
                return "sqlite+aiosqlite:///:memory:"
            if not database:
                return url.set(drivername="sqlite+aiosqlite").render_as_string(hide_password=False)
            path = Path(database).expanduser()
            if not path.is_absolute():
                path = BACKEND_ROOT / path
            url = url.set(database=path.resolve().as_posix())
            return url.set(drivername="sqlite+aiosqlite").render_as_string(hide_password=False)
        if value.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
            url = make_url(value).set(drivername="postgresql+asyncpg")
            query = dict(url.query)
            if "sslmode" in query:
                if "ssl" in query:
                    raise ValueError("Use ssl or sslmode in DATABASE_URL, not both")
                query["ssl"] = query.pop("sslmode")
            if "channel_binding" in query:
                raise ValueError(
                    "Use the provider's asyncpg connection string with ssl=require; "
                    "asyncpg does not support libpq channel_binding parameters"
                )
            return url.set(query=query).render_as_string(hide_password=False)
        return value

    @model_validator(mode="after")
    def _reject_dev_secrets_in_production(self) -> "Settings":
        if self.is_production:
            if (
                len(self.jwt_access_secret.strip()) < 32
                or self.jwt_access_secret == DEV_ACCESS_SECRET
                or self.jwt_access_secret.startswith("change-me")
            ):
                raise ValueError(
                    "JWT_ACCESS_SECRET must be a random secret of at least 32 characters"
                )
            if not self.secure_cookies:
                raise ValueError("Production requires Secure refresh cookies")
            from urllib.parse import urlsplit

            for origin in self.cors_origins:
                parts = urlsplit(origin)
                if (
                    parts.scheme != "https"
                    or not parts.hostname
                    or parts.username
                    or parts.password
                    or parts.path
                    or parts.query
                    or parts.fragment
                ):
                    raise ValueError("Production CORS origins must be exact HTTPS origins")
        if self.cookie_samesite == "none" and not self.secure_cookies:
            raise ValueError("SameSite=None requires Secure cookies")
        return self

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origin.split(",") if origin.strip()]
        if self.render_external_url and self.render_external_url not in origins:
            origins.append(self.render_external_url)
        return origins

    @property
    def bind_host(self) -> str:
        if self.host:
            return self.host
        return "0.0.0.0" if self.render_external_url else "127.0.0.1"

    @property
    def google_enabled(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret.get_secret_value()
            and self.google_redirect_uri
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure


@lru_cache
def get_settings() -> Settings:
    return Settings()
