"""Fail unsafe production configuration before serving requests."""

import pytest
from pydantic import ValidationError

from app.core.config import DEV_ACCESS_SECRET, Settings
from app.main import create_app


@pytest.mark.parametrize(
    "secret", [DEV_ACCESS_SECRET, "", "short", "change-me-to-a-long-random-value"]
)
def test_production_rejects_weak_secret(secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_ACCESS_SECRET"):
        Settings(_env_file=None, app_env="production", jwt_access_secret=secret)


def test_production_configuration() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        jwt_access_secret="a" * 48,
        cors_origin="https://fleng.example",
        database_url="postgres://u:p@db/fleng",
    )
    assert settings.secure_cookies
    assert settings.cookie_samesite == "lax"
    assert settings.database_url == "postgresql+asyncpg://u:p@db/fleng"
    assert not settings.trusted_proxy_ips


@pytest.mark.parametrize("origin", ["*", "http://fleng.example", "https://fleng.example/path"])
def test_production_rejects_unsafe_origin(origin: str) -> None:
    with pytest.raises(ValidationError, match="HTTPS origins"):
        Settings(
            _env_file=None, app_env="production", jwt_access_secret="a" * 48, cors_origin=origin
        )


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="Secure refresh"):
        Settings(
            _env_file=None, app_env="production", jwt_access_secret="a" * 48, cookie_secure=False
        )
    with pytest.raises(ValidationError, match="SameSite=None"):
        Settings(_env_file=None, cookie_samesite="none", cookie_secure=False)


def test_production_requires_frontend(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        jwt_access_secret="a" * 48,
        cors_origin="",
        frontend_dir="/tmp/fleng-nonexistent-frontend",
    )
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    with pytest.raises(RuntimeError, match="frontend directory"):
        create_app()
