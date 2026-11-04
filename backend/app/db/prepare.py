"""Prepare file-backed SQLite before serving requests; never reset existing data."""

import asyncio
import logging
import uuid

from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from alembic import command
from app.core.config import BACKEND_ROOT, get_settings
from app.db.base import Base
from app.db.diagnostics import log_sqlite_snapshot
from app.db.models import Course
from app.db.seed import seed_catalog
from app.db.session import SessionLocal, engine


async def ensure_catalog() -> None:
    try:
        async with SessionLocal() as db:
            if await db.scalar(select(Course.id).limit(1)) is None:
                await seed_catalog(db)
                print("Demo catalog loaded.")
            else:
                print("Catalog already present; use npm run db:seed to update demo content.")
    finally:
        await engine.dispose()


async def check_sqlite() -> None:
    """Verify real write access, including journal creation, without changing rows."""
    try:
        async with engine.connect() as connection:
            version = await connection.scalar(text("SELECT sqlite_version()"))
            foreign_keys = await connection.scalar(text("PRAGMA foreign_keys"))
            logging.getLogger("fleng").info(
                "SQLite connection version=%s foreign_keys=%s", version, foreign_keys
            )
            if tuple(map(int, version.split("."))) < (3, 35, 0):
                raise RuntimeError("SQLite >= 3.35 is required for auth RETURNING statements")
            if foreign_keys != 1:
                raise RuntimeError("SQLite foreign keys must be enabled")
            await connection.execute(text("SELECT now()"))
            await connection.execute(text("BEGIN IMMEDIATE"))
            # Transactional DDL exercises journal/directory permissions, then rolls back.
            probe = "_fleng_write_probe_" + uuid.uuid4().hex
            await connection.execute(text(f'CREATE TABLE "{probe}" (id INT)'))
            await connection.rollback()
    finally:
        await engine.dispose()


async def check_schema() -> None:
    """Fail startup on missing tables/columns even if Alembic was incorrectly stamped."""
    try:
        await log_sqlite_snapshot(engine, "after_migrations")
        async with engine.connect() as connection:
            for table in Base.metadata.sorted_tables:
                await connection.execute(select(table).limit(0))
    finally:
        await engine.dispose()


def main() -> None:
    settings = get_settings()
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite":
        print("PostgreSQL: run Alembic migrations explicitly before starting the service.")
        return
    if not url.database or url.database == ":memory:":
        raise RuntimeError("Startup preparation requires a file-backed SQLite database")
    print(f"Preparing SQLite: {url.database}", flush=True)
    asyncio.run(check_sqlite())
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    print("SQLite write check passed; upgrading Alembic to head.", flush=True)
    command.upgrade(config, "head")
    print("Checking SQLite tables and columns.", flush=True)
    asyncio.run(check_schema())
    asyncio.run(ensure_catalog())


if __name__ == "__main__":
    main()
