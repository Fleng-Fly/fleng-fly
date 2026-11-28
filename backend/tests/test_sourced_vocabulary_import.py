import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.db.import_vocabulary import LEVEL_TARGETS, audit_release, count_release, import_words
from app.db.models import Course, CourseVocabularyItem, Lesson


async def test_sourced_vocabulary_import_is_atomic_and_repeatable(tmp_path):
    database = tmp_path / "vocabulary.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database.as_posix()}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        course = (
            await connection.execute(
                Course.__table__.insert()
                .values(
                    slug="fixture-course",
                    title="Fixture",
                    description="",
                    level="A0",
                    is_published=True,
                )
                .returning(Course.id)
            )
        ).scalar_one()
        await connection.execute(
            Lesson.__table__.insert().values(
                course_id=course,
                slug="fixture-lesson",
                title="Fixture",
                summary="",
                theory="",
                is_published=True,
            )
        )
    dataset = tmp_path / "fixture.jsonl"
    entry = {
        "word": "Example’s Term",
        "translation": "приклад",
        "alternative_translations": ["зразок"],
        "pronunciation": "/fixture/",
        "example": "Example's term.",
        "example_translation": "Тестовий приклад.",
        "part_of_speech": "noun",
        "category": "fixture",
        "level": "A0",
        "course_slug": "fixture-course",
        "lesson_slug": "fixture-lesson",
        "source_url": "https://example.test/fixture",
        "license_id": "test-fixture",
    }
    row = json.dumps(entry)
    dataset.write_text(row + "\n" + row, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate normalized headword"):
        await import_words(database, dataset, apply=True)
    dataset.write_text(row, encoding="utf-8")
    assert await import_words(database, dataset) == 1
    async with engine.connect() as connection:
        assert (await connection.execute(select(CourseVocabularyItem.id))).all() == []
    assert await import_words(database, dataset, apply=True) == 1
    assert await import_words(database, dataset, apply=True) == 0
    counts = await audit_release(database)
    assert counts["A0"] == sum(counts.values()) == 1
    async with engine.connect() as connection:
        headword = await connection.scalar(select(CourseVocabularyItem.word))
        assert headword == "example's term"
    await engine.dispose()


def test_release_quotas_and_cross_level_deduplication():
    assert sum(LEVEL_TARGETS.values()) == 25_000
    assert LEVEL_TARGETS["C2"] == 5500
    counts = count_release([("C2", "Test’s Word"), ("A1", "test's  word"), ("C2", "Another")])
    assert counts["A1"] == counts["C2"] == 1
    assert sum(counts.values()) == 2
