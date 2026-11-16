"""Real migrated snapshots: preservation, refusal, rollback and opt-in asyncpg rehearsal."""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.core.config import BACKEND_ROOT, Settings
from app.db.backup import backup_sqlite
from app.db.models import Course, RefreshToken, User
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.db.transfer import check_schema, copy_rows, read_rows, transfer, validate_rows
from app.main import create_app
from tests.test_auth import PASSWORD
from tests.test_learning_extensions import headers


def migrated(path):
    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def setup(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: "2026-11-14 12:00:00")

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        connection.commit()
    return engine


@pytest.fixture
def snapshot(tmp_path):
    source = tmp_path / "source.sqlite3"
    engine = migrated(source)
    user_id, first, successor = uuid4(), uuid4(), uuid4()
    stamp = datetime(2025, 1, 2, 3, 4, 5, 123456, tzinfo=UTC)
    with engine.begin() as connection:
        connection.execute(
            User.__table__.insert().values(
                id=user_id,
                email="transfer@example.com",
                password_hash="test-only-hash",
                created_at=stamp,
                updated_at=stamp,
            )
        )
        connection.execute(
            RefreshToken.__table__.insert().values(
                id=successor,
                user_id=user_id,
                token_hash="successor",
                expires_at=stamp,
                created_at=stamp,
            )
        )
        connection.execute(
            RefreshToken.__table__.insert().values(
                id=first,
                user_id=user_id,
                token_hash="first",
                expires_at=stamp,
                replaced_by_id=successor,
                created_at=stamp,
            )
        )
        connection.execute(
            Course.__table__.insert().values(
                id=uuid4(),
                slug="unpublished-transfer",
                title="Draft",
                description="Draft",
                level="A0",
                is_published=False,
                created_at=stamp,
                updated_at=stamp,
            )
        )
    backup = tmp_path / "backup.sqlite3"
    backup_sqlite(source, backup)
    reader = create_engine(f"sqlite:///file:{backup}?mode=ro&uri=true")
    with reader.connect() as connection:
        check_schema(connection)
        rows = read_rows(connection)
    reader.dispose()
    engine.dispose()
    return source, rows


def test_typed_transfer_preserves_rows_and_refuses_repeat(snapshot, tmp_path):
    _, rows = snapshot
    engine = migrated(tmp_path / "destination.sqlite3")
    try:
        with engine.begin() as connection:
            counts = copy_rows(connection, rows)
            assert counts["users"] == 1
            assert counts["refresh_tokens"] == 2
            assert read_rows(connection) == rows
            assert rows["users"][0]["created_at"].tzinfo == UTC
            assert not rows["courses"][0]["is_published"]
            with pytest.raises(ValueError, match="occupied"):
                copy_rows(connection, rows)
    finally:
        engine.dispose()


def test_transfer_dry_run_rolls_back(snapshot, tmp_path):
    _, rows = snapshot
    engine = migrated(tmp_path / "dry.sqlite3")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            copy_rows(connection, rows)
            transaction.rollback()
            assert connection.scalar(select(text("count(*)")).select_from(User.__table__)) == 0
    finally:
        engine.dispose()


@pytest.mark.parametrize("damage", ["revision", "table", "column", "seed", "foreign-key"])
def test_transfer_refuses_incompatible_data(snapshot, tmp_path, damage):
    _, rows = snapshot
    engine = migrated(tmp_path / "bad.sqlite3")
    try:
        with engine.begin() as connection:
            if damage == "revision":
                connection.execute(text("UPDATE alembic_version SET version_num='wrong'"))
            elif damage == "table":
                connection.execute(text("CREATE TABLE unknown_data (id INT)"))
            elif damage == "column":
                connection.execute(text("ALTER TABLE users ADD COLUMN unexpected TEXT"))
            elif damage == "seed":
                connection.execute(text("UPDATE achievements SET threshold=999"))
            else:
                rows["refresh_tokens"][0]["user_id"] = uuid4()
            with pytest.raises(ValueError):
                copy_rows(connection, rows)
            assert connection.scalar(text("SELECT count(*) FROM users")) == 0
    finally:
        engine.dispose()


def test_reconciliation_failure_rolls_back(snapshot, tmp_path):
    _, rows = snapshot
    engine = migrated(tmp_path / "rollback.sqlite3")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TRIGGER mutate_user AFTER INSERT ON users BEGIN "
                    "UPDATE users SET email='mutated@example.com' WHERE id=NEW.id; END"
                )
            )
        with engine.connect() as connection:
            transaction = connection.begin()
            with pytest.raises(ValueError, match="reconciliation"):
                copy_rows(connection, rows)
            transaction.rollback()
            assert connection.scalar(text("SELECT count(*) FROM users")) == 0
    finally:
        engine.dispose()


async def test_transfer_requires_explicit_postgres_target(snapshot, tmp_path):
    source, _ = snapshot
    with pytest.raises(ValueError, match="PostgreSQL"):
        await transfer(source, tmp_path / "never.sqlite3", "sqlite:///:memory:", "public")
    assert not (tmp_path / "never.sqlite3").exists()


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="No disposable PostgreSQL URL")
async def test_asyncpg_transfer_and_learner_restore(tmp_path):
    """Full transfer round trip uses real API-generated learner data, not production."""
    source = tmp_path / "learner.sqlite3"
    sync_engine = migrated(source)
    sync_engine.dispose()
    source_engine = create_async_engine(f"sqlite+aiosqlite:///{source}")

    @event.listens_for(source_engine.sync_engine, "connect")
    def sqlite_setup(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: "2026-11-14 12:00:00")

    target_url = Settings(database_url=os.environ["TEST_DATABASE_URL"]).database_url
    schema = "fleng_transfer_" + uuid4().hex
    target_engine = create_async_engine(
        target_url, connect_args={"server_settings": {"search_path": schema}}
    )
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    app = create_app()

    def use_database(engine):
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def database():
            async with factory() as session:
                yield session

        app.dependency_overrides[get_db] = database
        return factory

    try:
        factory = use_database(source_engine)
        async with factory() as session:
            await seed_catalog(session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
            auth = await headers(c)
            lesson = (await c.get("/api/v1/lessons/the-verb-to-be")).json()
            submission = {"exerciseId": lesson["exercises"][0]["id"], "answer": "b"}
            assert (
                await c.post("/api/v1/lessons/the-verb-to-be/submit", headers=auth, json=submission)
            ).json()["xpAwarded"] > 0
            assert (
                await c.post(
                    "/api/v1/vocabulary",
                    headers=auth,
                    json={"word": "restore", "translation": "відновити"},
                )
            ).status_code == 201
            cards = (
                await c.post(
                    "/api/v1/vocabulary/flashcards/sessions",
                    headers=auth,
                    json={"source": "my_words"},
                )
            ).json()
            user = (await c.get("/api/v1/users/me", headers=auth)).json()
            progress = (await c.get("/api/v1/progress/me", headers=auth)).json()
            assert (await c.post("/api/v1/auth/refresh")).status_code == 200
            await source_engine.dispose()
            async with target_engine.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

                def migrate(sync):
                    config.attributes["connection"] = sync
                    command.upgrade(config, "head")

                await connection.run_sync(migrate)
            dry = await transfer(source, tmp_path / "dry-backup.sqlite3", target_url, schema)
            assert not dry["applied"]
            async with target_engine.connect() as connection:
                assert await connection.scalar(text("SELECT count(*) FROM users")) == 0
            applied = await transfer(
                source, tmp_path / "apply-backup.sqlite3", target_url, schema, apply=True
            )
            assert applied["applied"] and applied["row_counts"] == dry["row_counts"]
            use_database(target_engine)
            # Resume the original cookie before login can replace it.
            assert (await c.post("/api/v1/auth/refresh")).status_code == 200
            assert (
                await c.post(
                    "/api/v1/auth/login",
                    json={"email": "learner@example.com", "password": PASSWORD},
                )
            ).status_code == 200
            assert (await c.get("/api/v1/users/me", headers=auth)).json() == user
            assert (await c.get("/api/v1/progress/me", headers=auth)).json() == progress
            assert (
                await c.post("/api/v1/lessons/the-verb-to-be/submit", headers=auth, json=submission)
            ).json()["xpAwarded"] == 0
            route = "/api/v1/vocabulary/flashcards/sessions/" + cards["sessionId"]
            assert (await c.get(route, headers=auth)).json() == cards
            async with target_engine.connect() as connection:
                await connection.run_sync(lambda sync: validate_rows(read_rows(sync)))
            with pytest.raises(ValueError, match="occupied"):
                await transfer(source, tmp_path / "repeat.sqlite3", target_url, schema, apply=True)
    finally:
        app.dependency_overrides.clear()
        await source_engine.dispose()
        async with target_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await target_engine.dispose()


async def test_transfer_reads_private_snapshot_before_connecting(snapshot, tmp_path, monkeypatch):
    source, _ = snapshot
    backup = tmp_path / "snapshot with spaces?#.sqlite3"

    def no_network(*args, **kwargs):
        raise RuntimeError("snapshot validated; network deliberately unavailable")

    monkeypatch.setattr("app.db.transfer.create_async_engine", no_network)
    with pytest.raises(RuntimeError, match="snapshot validated"):
        await transfer(source, backup, "postgresql+asyncpg://test:test@localhost/staging", "public")
    assert backup.is_file() and backup.stat().st_mode & 0o077 == 0
