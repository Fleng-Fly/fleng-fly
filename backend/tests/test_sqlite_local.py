"""File-backed SQLite preparation must work outside backend/ and preserve data."""

import os
import sqlite3
import subprocess
import sys
import uuid

import pytest
from sqlalchemy.engine import make_url

from app.core.config import BACKEND_ROOT, Settings


def test_sqlite_paths_do_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    default = Settings(_env_file=None)
    expected = (BACKEND_ROOT / "data" / "fleng.db").as_posix()
    assert make_url(default.database_url).database == expected
    assert (
        make_url(Settings(database_url="sqlite:///./data/fleng.db").database_url).database
        == expected
    )
    assert Settings(database_url="sqlite+aiosqlite:///:memory:").database_url.endswith(":memory:")


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+asyncpg"])
def test_postgres_url_is_still_supported(scheme):
    settings = Settings(database_url=f"{scheme}://user:password@localhost:5432/fleng")
    assert settings.database_url == "postgresql+asyncpg://user:password@localhost:5432/fleng"


@pytest.mark.parametrize("app_env", ["development", "production"])
def test_sqlite_prepare_migrates_seeds_and_preserves_data(tmp_path, app_env):
    path = tmp_path / "new-directory" / "fleng.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{path}",
        "APP_ENV": app_env,
        "JWT_ACCESS_SECRET": "isolated-production-test-secret-never-deploy",
        "CORS_ORIGIN": "https://fleng.example",
        "COOKIE_SECURE": "true",
        "PYTHONPATH": str(BACKEND_ROOT),
    }

    def run(*args):
        result = subprocess.run(
            [sys.executable, *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    run("-m", "app.db.prepare")
    run("-m", "alembic", "-c", str(BACKEND_ROOT / "alembic.ini"), "check")
    user_id = uuid.uuid4().hex
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == (
            "20261114_1200"
        )
        counts = [
            db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("courses", "lessons", "exercises")
        ]
        assert all(count > 0 for count in counts)
        assert counts[0] == 7
        assert db.execute("SELECT count(*) FROM lessons WHERE is_published=0").fetchone() == (50,)
        assert db.execute("SELECT count(*) FROM course_vocabulary_items").fetchone() == (500,)
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, updated_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (user_id, "preserved@example.com", "test-fixture"),
        )
    run("-m", "app.db.prepare")
    if app_env == "development":
        run("-m", "app.db.seed")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT id FROM users").fetchone()[0] == user_id
        assert [
            db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("courses", "lessons", "exercises")
        ] == counts
    run(
        "-c",
        """
import asyncio
from sqlalchemy import text
from app.db.session import engine
async def check():
    try:
        async with engine.connect() as first, engine.connect() as second:
            for connection in (first, second):
                assert await connection.scalar(text('PRAGMA foreign_keys')) == 1
                assert await connection.scalar(text('SELECT now()'))
    finally:
        await engine.dispose()
asyncio.run(check())
""",
    )
