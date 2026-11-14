"""Logical pg_dump/pg_restore drill on two newly created disposable databases only."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.core.config import BACKEND_ROOT, Settings
from app.db.base import Base
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.db.transfer import check_schema, keyed, read_rows, validate_rows
from app.main import create_app
from tests.test_auth import PASSWORD
from tests.test_learning_extensions import headers


async def client_command(program, url, *arguments):
    parsed = make_url(url)
    # Avoid credentials in arguments/process listings or subprocess error output.
    environment = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    environment.update(
        PGHOST=parsed.host or "localhost",
        PGPORT=str(parsed.port or 5432),
        PGUSER=parsed.username or "",
        PGPASSWORD=parsed.password or "",
        PGDATABASE=parsed.database or "",
        PGCONNECT_TIMEOUT="10",
        PGSSLMODE="disable" if parsed.host in {"localhost", "127.0.0.1", "::1"} else "require",
    )
    process = await asyncio.create_subprocess_exec(
        program,
        *arguments,
        env=environment,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        code = await asyncio.wait_for(process.wait(), timeout=120)
    except TimeoutError:
        process.kill()
        await process.wait()
        raise RuntimeError(f"{program} timed out; private artifact may be incomplete") from None
    if code:
        raise RuntimeError(f"{program} failed; output suppressed to protect credentials/data")


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="No disposable PostgreSQL URL")
async def test_logical_backup_restore_and_authentication():
    # Configured PG testing MUST fail if the required drill dependencies are absent.
    assert shutil.which("pg_dump") and shutil.which("pg_restore"), "Install PostgreSQL 16 clients"
    url = Settings(database_url=os.environ["TEST_DATABASE_URL"]).database_url
    parsed = make_url(url)
    names = ["fleng_recovery_" + uuid4().hex for _ in range(2)]
    admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
    engines = [create_async_engine(parsed.set(database=name)) for name in names]
    app = create_app()
    created = []

    def use_database(engine):
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def database():
            async with factory() as session:
                yield session

        app.dependency_overrides[get_db] = database
        return factory

    try:
        async with admin.connect() as connection:
            for name in names:
                await connection.execute(text(f'CREATE DATABASE "{name}"'))
                created.append(name)
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
        async with engines[0].begin() as connection:

            def migrate(sync):
                config.attributes["connection"] = sync
                command.upgrade(config, "head")

            await connection.run_sync(migrate)
        factory = use_database(engines[0])
        async with factory() as session:
            await seed_catalog(session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
            auth = await headers(c)
            lesson = (await c.get("/api/v1/lessons/the-verb-to-be")).json()
            submission = {"exerciseId": lesson["exercises"][0]["id"], "answer": "b"}
            assert (
                await c.post("/api/v1/lessons/the-verb-to-be/submit", headers=auth, json=submission)
            ).json()["xpAwarded"] > 0
            expected = (await c.get("/api/v1/users/me", headers=auth)).json()
            progress = (await c.get("/api/v1/progress/me", headers=auth)).json()
            assert (
                await c.post(
                    "/api/v1/vocabulary",
                    headers=auth,
                    json={"word": "backup", "translation": "копія"},
                )
            ).status_code == 201
            cards = (
                await c.post(
                    "/api/v1/vocabulary/flashcards/sessions",
                    headers=auth,
                    json={"source": "my_words"},
                )
            ).json()
            async with engines[0].connect() as connection:
                before = await connection.run_sync(read_rows)
            # New mode-0700 directory and exclusively created mode-0600 archive.
            with tempfile.TemporaryDirectory(prefix="fleng-recovery-") as directory:
                archive = Path(directory) / "backup.dump"
                descriptor = os.open(archive, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
                await client_command(
                    "pg_dump",
                    parsed.set(database=names[0]).render_as_string(hide_password=False),
                    "--format=custom",
                    "--no-owner",
                    "--no-acl",
                    f"--file={archive}",
                )
                await client_command(
                    "pg_restore",
                    parsed.set(database=names[1]).render_as_string(hide_password=False),
                    "--dbname=" + names[1],
                    "--exit-on-error",
                    "--single-transaction",
                    "--no-owner",
                    "--no-acl",
                    str(archive),
                )
            async with engines[1].connect() as connection:
                await connection.run_sync(check_schema)
                after = await connection.run_sync(read_rows)
                validate_rows(after)
                for table in Base.metadata.sorted_tables:
                    assert keyed(table, before[table.name]) == keyed(table, after[table.name])
            use_database(engines[1])
            # Resume the original cookie before login can replace it.
            assert (await c.post("/api/v1/auth/refresh")).status_code == 200
            assert (
                await c.post(
                    "/api/v1/auth/login",
                    json={"email": "learner@example.com", "password": PASSWORD},
                )
            ).status_code == 200
            assert (await c.get("/api/v1/users/me", headers=auth)).json() == expected
            assert (await c.get("/api/v1/progress/me", headers=auth)).json() == progress
            assert (
                await c.post("/api/v1/lessons/the-verb-to-be/submit", headers=auth, json=submission)
            ).json()["xpAwarded"] == 0
            route = "/api/v1/vocabulary/flashcards/sessions/" + cards["sessionId"]
            assert (await c.get(route, headers=auth)).json() == cards
    finally:
        app.dependency_overrides.clear()
        for engine in engines:
            await engine.dispose()
        async with admin.connect() as connection:
            for name in created:
                await connection.execute(text(f'DROP DATABASE "{name}"'))
        await admin.dispose()
