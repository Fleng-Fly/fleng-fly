"""Async SQLAlchemy engine, session factory and FastAPI dependency."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

database_url = make_url(settings.database_url)
is_sqlite = database_url.get_backend_name() == "sqlite"
if is_sqlite and database_url.database and database_url.database != ":memory:":
    Path(database_url.database).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"timeout": 30} if is_sqlite else {},
)

if is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def configure_sqlite(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        # Existing Alembic migrations use PostgreSQL's now() as a column default.
        dbapi_connection.create_function(
            "now", 0, lambda: datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        )


SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
