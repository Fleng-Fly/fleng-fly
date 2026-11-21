"""The Reading migration is additive, keeps existing data and is reversible (SQLite)."""

import uuid
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from alembic import command
from app.db.base import Base

PREVIOUS = "20261120_1200"
READING_TABLES = {
    "reading_categories",
    "reading_articles",
    "reading_questions",
    "reading_answers",
    "reading_attempts",
    "reading_user_progress",
    "reading_bookmarks",
    "reading_topic_preferences",
}


def test_reading_tables_are_added_without_touching_existing_data_then_rolled_back(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(f"sqlite:///{tmp_path / 'reading.db'}")
    user = uuid.uuid4().hex
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, PREVIOUS)
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, created_at, updated_at) VALUES "
                "(:user, 'a@example.com', 'x', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"user": user},
        )
        connection.commit()
        before = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master"))}
        assert not READING_TABLES & before

        command.upgrade(config, "head")
        after = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master"))}
        assert READING_TABLES <= after
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        connection.commit()

        command.downgrade(config, PREVIOUS)
        remaining = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master"))}
        assert not READING_TABLES & remaining
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1
        connection.commit()
        command.upgrade(config, "head")
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1
    engine.dispose()
