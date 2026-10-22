"""File-backed SQLite preparation must work outside backend/ and preserve data."""

import os
import sqlite3
import subprocess
import sys
import uuid

import pytest

from app.core.config import BACKEND_ROOT, Settings


def test_sqlite_paths_do_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    default = Settings(_env_file=None)
    expected = f"sqlite+aiosqlite:///{BACKEND_ROOT / 'data' / 'fleng.db'}"
    assert default.database_url == expected
    assert Settings(database_url="sqlite:///./data/fleng.db").database_url == expected
    assert Settings(database_url="sqlite+aiosqlite:///:memory:").database_url.endswith(":memory:")


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+asyncpg"])
def test_postgres_url_is_still_supported(scheme):
    settings = Settings(database_url=f"{scheme}://user:password@localhost:5432/fleng")
    assert settings.database_url == "postgresql+asyncpg://user:password@localhost:5432/fleng"


def test_sqlite_prepare_migrates_seeds_and_preserves_data(tmp_path):
    path = tmp_path / "new-directory" / "fleng.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{path}",
        "APP_ENV": "development",
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
    user_id = uuid.uuid4().hex
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == (
            "20261018_1200"
        )
        counts = [
            db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("courses", "lessons", "exercises")
        ]
        assert all(count > 0 for count in counts)
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, updated_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (user_id, "preserved@example.com", "test-fixture"),
        )
    run("-m", "app.db.prepare")
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
