"""The personal-dictionary migration keeps existing words and is reversible (SQLite)."""

import uuid
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from alembic import command
from app.db.base import Base

PREVIOUS = "20261118_1200"


def test_existing_words_keep_data_and_gain_course_then_roll_back(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(f"sqlite:///{tmp_path / 'dictionary.db'}")
    ids = {name: uuid.uuid4().hex for name in ("user", "course", "lesson", "word", "loose")}
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, PREVIOUS)
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, created_at, updated_at) VALUES "
                "(:user, 'a@example.com', 'x', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            ids,
        )
        connection.execute(
            text(
                "INSERT INTO courses (id, slug, title, description, level, position, is_published,"
                " created_at, updated_at) VALUES (:course, 'c', 'C', 'd', 'A1', 1, 1,"
                " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            ids,
        )
        connection.execute(
            text(
                "INSERT INTO lessons (id, course_id, slug, title, summary, theory, position,"
                " estimated_minutes, is_published, created_at, updated_at) VALUES (:lesson,"
                " :course, 'l', 'L', 's', 't', 1, 5, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            ids,
        )
        for key, lesson in (("word", ids["lesson"]), ("loose", None)):
            connection.execute(
                text(
                    "INSERT INTO vocabulary_items (id, user_id, lesson_id, word, translation,"
                    " example, learned, due_at, created_at) VALUES (:id, :user, :lesson, :w, 't',"
                    " '', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {"id": ids[key], "user": ids["user"], "lesson": lesson, "w": key},
            )
        connection.commit()

        command.upgrade(config, "20261118_1400")
        rows = {
            row.word: row
            for row in connection.execute(
                text("SELECT word, course_id, source, learned, repetitions FROM vocabulary_items")
            )
        }
        assert rows["word"].course_id == ids["course"]  # backfilled from the lesson
        assert rows["loose"].course_id is None
        assert rows["word"].source == "manual" and rows["word"].learned == 1
        assert rows["word"].repetitions == 0
        command.upgrade(config, "20261120_1200")  # later revision; models include its columns
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []

        connection.commit()
        command.downgrade(config, PREVIOUS)
        assert connection.scalar(text("SELECT count(*) FROM vocabulary_items")) == 2
        info = connection.execute(text("PRAGMA table_info(vocabulary_items)"))
        columns = {row[1] for row in info}
        assert "course_id" not in columns and "source" not in columns
        connection.commit()
        command.upgrade(config, "head")
        assert connection.scalar(text("SELECT count(*) FROM vocabulary_items")) == 2
    engine.dispose()
