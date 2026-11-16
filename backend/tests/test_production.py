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


@pytest.mark.parametrize(
    "origin",
    [
        "http://fleng-fly.onrender.com",
        "https://fleng-fly.onrender.com/",
        "https://user:password@fleng-fly.onrender.com",
        "https://*.onrender.com",
        "https://fleng-fly.onrender.com?query=1",
        "https://fleng-fly.onrender.com#fragment",
        "https://fleng-fly.onrender.com,https://evil.example",
        "*",
        "null",
    ],
)
def test_render_external_url_rejects_non_origins(origin: str) -> None:
    with pytest.raises(ValidationError, match="exact HTTPS origin"):
        Settings(_env_file=None, render_external_url=origin)


@pytest.mark.parametrize(
    "cors",
    [
        "https://fleng.netlify.app",
        " https://fleng-fly.onrender.com, https://fleng.netlify.app ",
        "",
    ],
)
def test_render_runtime_origin_is_merged_once(cors: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://fleng-fly.onrender.com")
    settings = Settings(_env_file=None, cors_origin=cors)
    assert settings.cors_origins.count("https://fleng-fly.onrender.com") == 1
    assert "*" not in settings.cors_origins


@pytest.mark.parametrize("trusted", ["", "10.0.0.7,10.0.1.0/24"])
def test_launcher_uses_only_explicit_proxy_trust(
    trusted: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import run

    settings = Settings(_env_file=None, trusted_proxy_ips=trusted)
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "*")  # Render's Python default.
    monkeypatch.setattr(run, "get_settings", lambda: settings)
    monkeypatch.setattr("app.db.prepare.main", lambda: None)
    called = {}
    monkeypatch.setattr(run.uvicorn, "run", lambda *args, **kwargs: called.update(kwargs))
    run.main()
    assert called["proxy_headers"] is bool(trusted)
    assert called["forwarded_allow_ips"] == trusted
    assert called["workers"] == 1
