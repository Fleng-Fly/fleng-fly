"""Real SQLite migration with foreign-key cascades enabled and populated children."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, event, insert, select, text

from alembic import command
from app.db.models import (
    Course,
    CourseVocabularyItem,
    Exercise,
    ExerciseSubmission,
    Lesson,
    LessonProgress,
    Profile,
    Progress,
    User,
    VocabularyItem,
)


def test_a0_constraint_keeps_foreign_key_children(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'a0.db'}")

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("now", 0, lambda: datetime.now(UTC).isoformat())

    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    user, course, lesson, exercise = [uuid4() for _ in range(4)]
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "20261110_1200")
        connection.execute(
            insert(User).values(id=user, email="kept@example.com", password_hash="x")
        )
        connection.execute(insert(Profile).values(user_id=user, display_name="Keep", xp=12))
        connection.execute(insert(Progress).values(user_id=user, lessons_started=1))
        connection.execute(
            insert(Course).values(
                id=course, slug="keep", title="Keep", description="Keep", level="A1"
            )
        )
        connection.execute(
            insert(Lesson).values(
                id=lesson,
                course_id=course,
                slug="keep-lesson",
                title="Keep",
                summary="Keep",
                theory="Keep",
                estimated_minutes=10,
            )
        )
        connection.execute(
            insert(Exercise).values(
                id=exercise,
                lesson_id=lesson,
                slug="keep-q",
                type="text",
                prompt="Keep",
                accepted_answers=["keep"],
            )
        )
        connection.execute(
            insert(ExerciseSubmission).values(
                user_id=user, exercise_id=exercise, answer="keep", completed=True, xp_awarded=True
            )
        )
        connection.execute(insert(LessonProgress).values(user_id=user, lesson_id=lesson))
        connection.execute(
            insert(VocabularyItem).values(
                user_id=user, lesson_id=lesson, word="keep", translation="зберігати"
            )
        )
        connection.execute(
            insert(CourseVocabularyItem).values(
                course_id=course, word="keep", translation="зберігати"
            )
        )
        connection.commit()
        tables = [
            Course,
            Lesson,
            Exercise,
            ExerciseSubmission,
            LessonProgress,
            VocabularyItem,
            CourseVocabularyItem,
            Profile,
            Progress,
        ]
        before = {
            table: connection.execute(
                select(*(column for column in table.__table__.c if column.name != "letter_tiles"))
            ).all()
            for table in tables
        }
        connection.commit()
        command.upgrade(config, "20261110_1400")
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert {
            table: connection.execute(
                select(*(column for column in table.__table__.c if column.name != "letter_tiles"))
            ).all()
            for table in tables
        } == before
        connection.execute(
            insert(Course).values(slug="intro", title="Intro", description="Intro", level="A0")
        )
        connection.commit()
        with pytest.raises(RuntimeError, match="A0 courses exist"):
            command.downgrade(config, "20261110_1200")
        connection.rollback()
        connection.execute(text("DELETE FROM courses WHERE slug = 'intro'"))
        connection.commit()
        command.downgrade(config, "20261110_1200")
        command.upgrade(config, "20261110_1400")
        assert {
            table: connection.execute(
                select(*(column for column in table.__table__.c if column.name != "letter_tiles"))
            ).all()
            for table in tables
        } == before
        connection.commit()
        command.upgrade(config, "head")
        command.check(config)
    engine.dispose()
