"""Refuse ephemeral Render storage before registration and keep provider URL secrets private."""

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import BACKEND_ROOT, Settings
from app.db.storage import DatabaseConfigurationError, validate_render_storage
from tests.test_production_sqlite import production_env


def hosted(url):
    return Settings(
        _env_file=None,
        app_env="production",
        database_url=url,
        jwt_access_secret="disposable-durability-fixture-key-32-characters",
        cors_origin="https://fleng.example",
        render_external_url="https://fleng.example",
    )


@pytest.mark.parametrize(
    "url",
    [
        "sqlite+aiosqlite:///./data/fleng.db",
        "sqlite+aiosqlite:////var/data/fleng.db",
        "sqlite+aiosqlite:///:memory:",
    ],
)
def test_render_rejects_sqlite_without_real_persistent_mount(url, monkeypatch):
    monkeypatch.setattr(Path, "is_mount", lambda _: False)
    with pytest.raises(DatabaseConfigurationError, match="ephemeral"):
        validate_render_storage(hosted(url))


def test_sqlite_requires_both_mounted_disk_and_path_beneath_it(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "is_mount", lambda p: p == Path("/var/data"))
    validate_render_storage(hosted("sqlite+aiosqlite:////var/data/fleng.db"))
    with pytest.raises(DatabaseConfigurationError, match="ephemeral"):
        validate_render_storage(hosted(f"sqlite+aiosqlite:///{tmp_path}/fleng.db"))
    validate_render_storage(Settings(_env_file=None))
    validate_render_storage(hosted("postgresql://test:test@localhost/fleng"))


def test_render_stops_before_creating_disposable_account_database(tmp_path):
    path = tmp_path / "should-not-exist" / "fleng.db"
    env = {**production_env(path), "RENDER_EXTERNAL_URL": "https://fleng.example"}
    result = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "run.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 1
    assert "ephemeral storage" in result.stderr and "PostgreSQL" in result.stderr
    assert env["JWT_ACCESS_SECRET"] not in result.stderr
    assert not path.exists()


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+asyncpg"])
async def test_provider_sslmode_is_translated_to_asyncpg_without_losing_password(scheme):
    settings = Settings(
        _env_file=None, database_url=f"{scheme}://test:p%40ss@localhost/fleng?sslmode=require"
    )
    url = make_url(settings.database_url)
    assert url.password == "p@ss" and url.query == {"ssl": "require"}
    engine = create_async_engine(settings.database_url)
    try:
        _, arguments = engine.sync_engine.dialect.create_connect_args(url)
        assert arguments["ssl"] == "require" and "sslmode" not in arguments
    finally:
        await engine.dispose()


def test_unsupported_provider_options_do_not_print_connection_credentials():
    with pytest.raises(ValueError) as error:
        Settings(
            _env_file=None,
            database_url=(
                "postgresql://private-user:private-db-password@localhost/fleng"
                "?sslmode=require&channel_binding=require"
            ),
        )
    assert "channel_binding" in str(error.value)
    assert "private-db-password" not in str(error.value)
    assert "private-user" not in str(error.value)
    with pytest.raises(ValueError, match="not both"):
        Settings(
            _env_file=None,
            database_url="postgresql://test:test@localhost/fleng?sslmode=require&ssl=disable",
        )
