"""Opt-in PostgreSQL checks for the OAuth-identity and personal-dictionary migrations.

Each test works in its own throw-away schema of the disposable `TEST_DATABASE_URL` database;
the application schema is never touched.
"""

import asyncio
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alembic import command
from app.core.config import Settings
from app.db.base import Base
from app.db.models import (
    Course,
    CourseVocabularyItem,
    Exercise,
    Lesson,
    LessonProgress,
    User,
    VocabularyItem,
)
from app.modules.vocabulary.service import collect_lesson_words

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL PostgreSQL is not configured"
)

BEFORE_OAUTH = "20261117_1200"
BEFORE_DICTIONARY = "20261118_1200"
HEAD = "20261124_1200"
TABLES = "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"


def _config() -> Config:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


async def _engine_with_schema():
    url = Settings(database_url=os.environ["TEST_DATABASE_URL"]).database_url
    assert url.startswith("postgresql+asyncpg://")
    schema = "fleng_dictionary_" + uuid.uuid4().hex
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    async with engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    return engine, schema


async def _drop(engine, schema: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    await engine.dispose()


async def _migrate(engine, action, revision: str):
    config = _config()

    def run(sync_connection):
        config.attributes["connection"] = sync_connection
        getattr(command, action)(config, revision)

    async with engine.begin() as connection:
        await connection.run_sync(run)


async def _columns(connection, table: str) -> set[str]:
    rows = await connection.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :t"
        ),
        {"t": table},
    )
    return {row[0] for row in rows}


async def _indexes(connection, table: str) -> set[str]:
    rows = await connection.execute(
        text(
            "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() AND tablename=:t"
        ),
        {"t": table},
    )
    return {row[0] for row in rows}


async def test_upgrade_from_previous_schema_keeps_words_and_rolls_back_cleanly():
    engine, schema = await _engine_with_schema()
    ids = {name: uuid.uuid4() for name in ("user", "course", "lesson", "word", "loose")}
    try:
        await _migrate(engine, "upgrade", BEFORE_DICTIONARY)
        async with engine.begin() as connection:
            assert "oauth_identities" in {row[0] for row in await connection.execute(text(TABLES))}
            assert "course_id" not in await _columns(connection, "vocabulary_items")
            await connection.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, created_at, updated_at) "
                    "VALUES (:user, 'a@example.com', 'x', now(), now())"
                ),
                ids,
            )
            await connection.execute(
                text(
                    "INSERT INTO courses (id, slug, title, description, level, position,"
                    " is_published, created_at, updated_at) VALUES (:course, 'c', 'C', 'd',"
                    " 'A1', 1, true, now(), now())"
                ),
                ids,
            )
            await connection.execute(
                text(
                    "INSERT INTO lessons (id, course_id, slug, title, summary, theory, position,"
                    " estimated_minutes, is_published, created_at, updated_at) VALUES (:lesson,"
                    " :course, 'l', 'L', 's', 't', 1, 5, true, now(), now())"
                ),
                ids,
            )
            for key, lesson in (("word", ids["lesson"]), ("loose", None)):
                await connection.execute(
                    text(
                        "INSERT INTO vocabulary_items (id, user_id, lesson_id, word, translation,"
                        " example, learned, due_at, created_at) VALUES (:id, :user, :lesson, :w,"
                        " 't', '', true, now(), now())"
                    ),
                    {"id": ids[key], "user": ids["user"], "lesson": lesson, "w": key},
                )

        await _migrate(engine, "upgrade", HEAD)
        async with engine.begin() as connection:
            rows = {
                row.word: row
                for row in await connection.execute(
                    text(
                        "SELECT word, course_id, source, learned, repetitions FROM vocabulary_items"
                    )
                )
            }
            assert rows["word"].course_id == ids["course"]  # backfilled from the lesson
            assert rows["loose"].course_id is None
            assert rows["word"].source == "manual" and rows["word"].learned is True
            assert rows["word"].repetitions == 0
            assert {"ix_vocabulary_items_course_id", "ix_vocabulary_items_lesson_id"} <= (
                await _indexes(connection, "vocabulary_items")
            )
            assert "ix_course_vocabulary_items_lesson_id" in await _indexes(
                connection, "course_vocabulary_items"
            )
            drift = await connection.run_sync(
                lambda sync: compare_metadata(MigrationContext.configure(sync), Base.metadata)
            )
            assert drift == []

        # Constraints are enforced by PostgreSQL itself.
        with pytest.raises(IntegrityError):
            async with engine.begin() as connection:
                await connection.execute(
                    text("UPDATE vocabulary_items SET source = 'bogus' WHERE word = 'word'")
                )
        # Deleting the course keeps the word (SET NULL), deleting the user removes it (CASCADE).
        async with engine.begin() as connection:
            await connection.execute(text("DELETE FROM courses WHERE id = :course"), ids)
            kept = await connection.scalar(
                text("SELECT count(*) FROM vocabulary_items WHERE course_id IS NULL")
            )
            assert kept == 2

        # Roll back one step: data stays, new columns/indexes go.
        await _migrate(engine, "downgrade", BEFORE_DICTIONARY)
        async with engine.begin() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM vocabulary_items")) == 2
            columns = await _columns(connection, "vocabulary_items")
            assert not {"course_id", "source", "pronunciation", "repetitions"} & columns
            assert "ix_vocabulary_items_course_id" not in await _indexes(
                connection, "vocabulary_items"
            )
        # And the OAuth migration too (back to the pre-feature schema), then forward again.
        await _migrate(engine, "downgrade", BEFORE_OAUTH)
        async with engine.begin() as connection:
            tables = {row[0] for row in await connection.execute(text(TABLES))}
            assert "oauth_identities" not in tables
            assert await connection.scalar(text("SELECT count(*) FROM users")) == 1
        await _migrate(engine, "upgrade", "head")
        async with engine.begin() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM vocabulary_items")) == 2
            assert await connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
    finally:
        await _drop(engine, schema)


async def test_oauth_identity_constraints_on_postgresql():
    engine, schema = await _engine_with_schema()
    try:
        await _migrate(engine, "upgrade", "head")
        ids = {name: uuid.uuid4() for name in ("u1", "u2")}
        async with engine.begin() as connection:
            for key, email in (("u1", "one@example.com"), ("u2", "two@example.com")):
                await connection.execute(
                    text(
                        "INSERT INTO users (id, email, password_hash, created_at, updated_at) "
                        "VALUES (:id, :email, 'x', now(), now())"
                    ),
                    {"id": ids[key], "email": email},
                )

        async def link(user: str, subject: str):
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO oauth_identities (id, user_id, provider, subject, email)"
                        " VALUES (:id, :user, 'google', :subject, 'x@example.com')"
                    ),
                    {"id": uuid.uuid4(), "user": ids[user], "subject": subject},
                )

        await link("u1", "sub-1")
        with pytest.raises(IntegrityError):  # the same Google account on a second user
            await link("u2", "sub-1")
        with pytest.raises(IntegrityError):  # a second Google account on the same user
            await link("u1", "sub-2")
        # Concurrent attempts to claim one subject: exactly one wins.
        results = await asyncio.gather(
            link("u2", "sub-race"), link("u2", "sub-race"), return_exceptions=True
        )
        assert sum(isinstance(r, IntegrityError) for r in results) == 1
        async with engine.begin() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM oauth_identities")) == 2
            await connection.execute(text("DELETE FROM users WHERE id = :u1"), ids)  # CASCADE
            assert await connection.scalar(text("SELECT count(*) FROM oauth_identities")) == 1
    finally:
        await _drop(engine, schema)


async def test_concurrent_lesson_collection_adds_each_word_exactly_once():
    engine, schema = await _engine_with_schema()
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as db:
            user = User(email="collect@example.com", password_hash="x")
            course = Course(slug="c", title="C", description="d", level="A1", is_published=True)
            lesson = Lesson(
                course=course, slug="l", title="L", summary="s", theory="t", position=1,
                estimated_minutes=5, is_published=True,
            )  # fmt: skip
            exercise = Exercise(
                lesson=lesson, slug="q", position=1, type="single_choice", prompt="p", points=1,
                options=[{"id": "a", "text": "A"}], correct_option_id="a",
            )  # fmt: skip
            db.add_all([user, course, lesson, exercise])
            await db.flush()
            for number in range(10):
                db.add(
                    CourseVocabularyItem(
                        course_id=course.id, lesson_id=lesson.id, word=f"Word{number}",
                        translation="t", example="", pronunciation=None,
                    )
                )  # fmt: skip
            db.add(
                LessonProgress(
                    user_id=user.id, lesson_id=lesson.id, status="completed",
                    completed_at=datetime.now(UTC),
                )
            )  # fmt: skip
            await db.commit()
            user_id, lesson_id = user.id, lesson.id

        async def collect() -> None:
            async with sessions() as db:
                await collect_lesson_words(db, user_id, lesson_id)
                await db.commit()

        await asyncio.gather(*(collect() for _ in range(5)))
        async with sessions() as db:
            words = (await db.scalars(select(VocabularyItem.word))).all()
            assert sorted(words) == sorted(f"word{n}" for n in range(10))
            item = (await db.scalars(select(VocabularyItem))).first()
            assert item is not None and item.source == "lesson" and item.course_id is not None
        await collect()  # repeating is a no-op
        async with sessions() as db:
            assert len((await db.scalars(select(VocabularyItem.id))).all()) == 10
    finally:
        await _drop(engine, schema)
