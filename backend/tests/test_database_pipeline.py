"""Release checks use Alembic, real files/connections and disposable PG schemas."""

import os
import sqlite3
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.core.config import BACKEND_ROOT, Settings
from app.db.backup import backup_sqlite
from app.db.base import Base
from app.db.curriculum import import_curriculum, load_curriculum
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.main import create_app
from tests.test_learning_extensions import headers


async def test_migrated_database_import_and_learner_persistence(tmp_path):
    pg_url = os.environ.get("TEST_DATABASE_URL")
    schema = "fleng_pipeline_" + uuid4().hex
    path = tmp_path / "pipeline.sqlite3"
    url = Settings(database_url=pg_url).database_url if pg_url else (f"sqlite+aiosqlite:///{path}")
    if pg_url:
        assert url.startswith("postgresql+asyncpg://")
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}} if pg_url else {}
    )
    if not pg_url:

        @event.listens_for(engine.sync_engine, "connect")
        def sqlite_setup(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.create_function("now", 0, lambda: "2026-11-14 12:00:00")

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    try:
        async with engine.connect() as connection:
            if pg_url:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                await connection.commit()

            def migrate(sync):
                config.attributes["connection"] = sync
                command.upgrade(config, "head")
                command.upgrade(config, "head")
                assert compare_metadata(MigrationContext.configure(sync), Base.metadata) == []

            await connection.run_sync(migrate)
            await connection.commit()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        app = create_app()

        async def database():
            async with factory() as session:
                yield session

        app.dependency_overrides[get_db] = database
        async with factory() as session:
            await seed_catalog(session)
            original_ids = set((await session.scalars(select(Course.id))).all())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
            auth = await headers(c)
            lesson = (await c.get("/api/v1/lessons/the-verb-to-be")).json()
            submitted = await c.post(
                "/api/v1/lessons/the-verb-to-be/submit",
                headers=auth,
                json={"exerciseId": lesson["exercises"][0]["id"], "answer": "b"},
            )
            assert submitted.status_code == 200
            assert submitted.json()["xpAwarded"] > 0
            word = await c.post(
                "/api/v1/vocabulary",
                headers=auth,
                json={"word": "persist", "translation": "зберігати", "lessonId": lesson["id"]},
            )
            assert word.status_code == 201
            cards = await c.post(
                "/api/v1/vocabulary/flashcards/sessions",
                headers=auth,
                json={"source": "my_words"},
            )
            assert cards.status_code == 201
            snapshot = cards.json()
            assert snapshot["total"] == 1
            user = (await c.get("/api/v1/users/me", headers=auth)).json()
            progress = (await c.get("/api/v1/progress/me", headers=auth)).json()
            async with factory() as session:
                await seed_catalog(session)
                imported = await import_curriculum(session, load_curriculum(), apply=True)
                assert imported["new_rows"] == 955
                assert (await import_curriculum(session, load_curriculum(), apply=True))[
                    "new_rows"
                ] == 0
            # Dispose the pool; all assertions below reopen physical DB connections.
            await engine.dispose()
            assert (await c.get("/api/v1/users/me", headers=auth)).json() == user
            assert (await c.get("/api/v1/progress/me", headers=auth)).json() == progress
            assert (await c.get("/api/v1/lessons/the-verb-to-be")).json() == lesson
            assert (await c.post("/api/v1/auth/refresh")).status_code == 200
            route = "/api/v1/vocabulary/flashcards/sessions/" + snapshot["sessionId"]
            resumed = await c.get(route, headers=auth)
            assert resumed.status_code == 200
            assert resumed.json() == snapshot
            assert (await c.post(route + "/complete", headers=auth)).json()["testReady"]
            assert (await c.get(route + "/test-words", headers=auth)).json()["cards"] == snapshot[
                "cards"
            ]
            assert len((await c.get("/api/v1/courses")).json()) == 2
            for course in load_curriculum().courses:
                assert (await c.get("/api/v1/courses/" + course.slug)).status_code == 404
                for draft in course.lessons:
                    assert (await c.get("/api/v1/lessons/" + draft.slug)).status_code == 404
        async with factory() as session:
            assert original_ids.issubset(set((await session.scalars(select(Course.id))).all()))
            for model, count in [
                (Course, 7),
                (Lesson, 56),
                (Exercise, 418),
                (CourseVocabularyItem, 500),
            ]:
                assert await session.scalar(select(func.count()).select_from(model)) == count
            # Check every declared FK, including optional and self-referencing links.
            for table in Base.metadata.sorted_tables:
                for fk in table.foreign_keys:
                    parent = fk.column
                    child = fk.parent
                    missing = select(child).where(
                        child.is_not(None), ~select(parent).where(parent == child).exists()
                    )
                    # Alias self-references so correlation cannot hide dangling links.
                    if parent.table is table:
                        target = table.alias()
                        missing = select(child).where(
                            child.is_not(None),
                            ~select(target.c[parent.name])
                            .where(target.c[parent.name] == child)
                            .exists(),
                        )
                    assert (await session.execute(missing)).first() is None
            if not pg_url:
                assert (await session.execute(text("PRAGMA foreign_key_check"))).all() == []
    finally:
        if pg_url:
            async with engine.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


def test_online_backup_round_trip_and_refusal(tmp_path):
    source = tmp_path / "source.sqlite3"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE users (id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO users VALUES ('preserve-user-id')")
        db.commit()
        destination = tmp_path / "backup.sqlite3"
        assert backup_sqlite(source, destination) == {"users": 1}
        assert destination.stat().st_mode & 0o077 == 0
        with sqlite3.connect(destination) as restored:
            assert restored.execute("SELECT id FROM users").fetchone() == ("preserve-user-id",)
        with pytest.raises(FileExistsError):
            backup_sqlite(source, destination)
        with pytest.raises(FileExistsError):
            backup_sqlite(source, source)
        assert db.execute("SELECT count(*) FROM users").fetchone() == (1,)
    absent = tmp_path / "absent.sqlite3"
    with pytest.raises(FileNotFoundError):
        backup_sqlite(absent, tmp_path / "never-created.sqlite3")
    assert not absent.exists()
