"""Opt-in real PostgreSQL migration/drift test. Never uses the application schema."""

import os
import uuid
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.core.config import Settings
from app.db.base import Base


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL PostgreSQL is not configured"
)
async def test_postgres_migration_chain_and_drift():
    url = Settings(database_url=os.environ["TEST_DATABASE_URL"]).database_url
    assert url.startswith("postgresql+asyncpg://")
    schema = "fleng_migration_" + uuid.uuid4().hex
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    try:
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

            def migrate(sync_connection):
                config.attributes["connection"] = sync_connection
                command.upgrade(config, "head")
                context = MigrationContext.configure(sync_connection)
                assert compare_metadata(context, Base.metadata) == []

            await connection.run_sync(migrate)
            assert await connection.scalar(text("SELECT count(*) FROM achievements")) == 5
            assert (
                await connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "20261018_1200"
            )
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
