"""Prepare persistent storage; migrate only empty PostgreSQL schemas automatically."""

import asyncio
import logging
import uuid

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.core.config import BACKEND_ROOT, get_settings
from app.db.base import Base
from app.db.curriculum import import_curriculum, load_curriculum
from app.db.demo_lessons import import_demo_lessons
from app.db.diagnostics import log_sqlite_snapshot
from app.db.extension import extension_sha, import_extension, load_extensions
from app.db.models import Course
from app.db.practice import import_practice, import_vocabulary_practice
from app.db.seed import seed_catalog
from app.db.session import SessionLocal, engine
from app.db.storage import DatabaseConfigurationError, validate_render_storage

# Owner explicitly authorized publication on 2026-11-14. Linguistic review remains incomplete.
# A different content SHA needs a new release decision; never derive this approval dynamically.
OWNER_AUTHORIZED_CURRICULUM_SHA = "27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013"


# Extension files (more lessons for the published courses) are imported and published only when
# their exact SHA is listed here. An empty set means every extension stays out of the catalog.
# Add a SHA only as an explicit release decision after reviewing that content.
OWNER_AUTHORIZED_EXTENSION_SHAS: frozenset[str] = frozenset()


async def populate_catalog(db: AsyncSession) -> None:
    if await db.scalar(select(Course.id).limit(1)) is None:
        await seed_catalog(db)
        print("Demo catalog loaded.")
    else:
        print("Catalog already present; use npm run db:seed to update demo content.")
    content = load_curriculum()
    result = await import_curriculum(
        db,
        content,
        apply=True,
        owner_authorized_sha=OWNER_AUTHORIZED_CURRICULUM_SHA,
    )
    print(
        "A0–B2 catalog published (owner authorized; linguistic review incomplete): "
        f"{result['new_rows']} new rows, {result['existing_rows']} existing rows."
    )
    practice = await import_practice(db, content)
    print(f"Lesson practice: {practice['added']} added, {practice['existing']} already present.")
    for name, extension in load_extensions():
        digest = extension_sha(extension)
        if digest not in OWNER_AUTHORIZED_EXTENSION_SHAS:
            print(f"Curriculum extension {name} is not authorized for publication; skipped.")
            continue
        added = await import_extension(db, extension, base=content, publish_sha=digest)
        print(f"Curriculum extension {name}: {added['added_rows']} new rows published.")
    await import_vocabulary_practice(db, content)
    demo = await import_demo_lessons(db)
    print(
        f"Demo lessons: {demo['words_added']} words and {demo['practice_added']} exercises added, "
        f"{demo['words_existing'] + demo['practice_existing']} already present."
    )


async def ensure_catalog() -> None:
    try:
        async with SessionLocal() as db:
            await populate_catalog(db)
    finally:
        await engine.dispose()


def prepare_postgres_schema(connection: Connection) -> None:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    views = inspector.get_view_names() + inspector.get_materialized_view_names()
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    if not tables and not views:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        print("Empty PostgreSQL schema migrated to head.")
    else:
        heads = ScriptDirectory.from_config(config).get_heads()
        if "alembic_version" not in tables or len(heads) != 1:
            raise DatabaseConfigurationError(
                "Existing PostgreSQL schema is not a known Fleng release. "
                "Startup refused; preserve the data and migrate explicitly."
            )
        if list(connection.scalars(text("SELECT version_num FROM alembic_version"))) != heads:
            raise DatabaseConfigurationError(
                "Existing PostgreSQL schema needs an explicit Alembic release migration. "
                "Startup did not upgrade, reset or replace it."
            )
    for table in Base.metadata.sorted_tables:
        connection.execute(select(table).limit(0))


async def prepare_postgres() -> None:
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SET LOCAL lock_timeout = '30s'"))
            # Coordinate overlapping deploys; initialization/catalog publication commit together.
            await connection.execute(text("SELECT pg_advisory_xact_lock(1179403591)"))
            await connection.run_sync(prepare_postgres_schema)
            async with AsyncSession(
                bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            ) as db:
                await populate_catalog(db)
        print("PostgreSQL ready; existing users and progress preserved.")
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
    validate_render_storage(settings)
    url = make_url(settings.database_url)
    if url.get_backend_name() == "postgresql":
        asyncio.run(prepare_postgres())
        return
    if url.get_backend_name() != "sqlite":
        raise DatabaseConfigurationError("Use SQLite locally or PostgreSQL for durable hosting")
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
