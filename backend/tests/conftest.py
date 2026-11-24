"""Shared test fixtures.

Auth/progress tests run against a real SQLAlchemy engine backed by an in-memory
SQLite database (the environment has no PostgreSQL). This exercises the ORM,
constraints and transactions for real, without a server. Set TEST_DATABASE_URL
to run the same suite against PostgreSQL using a unique,
isolated schema per test. No existing schema is modified.
"""

import os
import uuid
from collections.abc import AsyncGenerator

# Settings also read <repo>/.env and backend/.env. A developer's local .env (real Google OAuth
# values, AI_ENABLED, AI_ALLOW_AUTO_ROUTER, provider keys, prices...) must never change test
# outcomes, so dotenv files are not read at all. Explicit process environment variables (as CI
# sets them) and per-test overrides still apply.
from app.core.config import Settings  # noqa: E402

Settings.model_config["env_file"] = None
for _name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
    os.environ[_name] = ""

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import models  # noqa: E402, F401  (register all models on Base.metadata)
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    test_url = os.environ.get("TEST_DATABASE_URL")
    schema = "fleng_test_" + uuid.uuid4().hex
    if test_url:
        from app.core.config import Settings

        url = Settings(database_url=test_url).database_url
        if not url.startswith("postgresql+asyncpg://"):
            raise ValueError("TEST_DATABASE_URL must use PostgreSQL")
        engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        if not test_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    if test_url:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.clear()
