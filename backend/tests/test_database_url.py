"""DATABASE_URL normalisation keeps SQLAlchemy driver names exact."""

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import BACKEND_ROOT, Settings


@pytest.mark.parametrize(
    "raw",
    ["sqlite:///:memory:", "sqlite+aiosqlite:///:memory:", "sqlite://", "sqlite+aiosqlite://"],
)
async def test_sqlite_memory_urls_use_exact_async_driver(raw: str) -> None:
    normalized = Settings(database_url=raw).database_url
    url = make_url(normalized)
    assert url.drivername == "sqlite+aiosqlite"
    assert url.database in (None, ":memory:")
    # ":memory:" must stay literal, not be percent-encoded into a file name.
    assert "%" not in normalized
    assert normalized.startswith("sqlite+aiosqlite://")
    assert "+aiosqlite+" not in normalized

    engine = create_async_engine(url)
    try:
        assert engine.dialect.driver == "aiosqlite"
    finally:
        await engine.dispose()


@pytest.mark.parametrize("raw", ["sqlite:///./data/x.db", "sqlite+aiosqlite:///./data/x.db"])
def test_sqlite_relative_file_resolves_against_backend(raw: str) -> None:
    url = make_url(Settings(database_url=raw).database_url)
    assert url.drivername == "sqlite+aiosqlite"
    assert url.database == (BACKEND_ROOT / "data" / "x.db").resolve().as_posix()


def test_sqlite_absolute_file_is_preserved(tmp_path) -> None:
    target = tmp_path / "fleng.sqlite3"
    url = make_url(Settings(database_url=f"sqlite+aiosqlite:///{target}").database_url)
    assert url.drivername == "sqlite+aiosqlite"
    assert url.database == target.resolve().as_posix()
