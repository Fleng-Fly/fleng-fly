"""Validate and import a sourced JSONL vocabulary release into a prepared SQLite test DB."""

import argparse
import asyncio
import unicodedata
from pathlib import Path
from typing import Annotated, cast

from pydantic import Field, HttpUrl
from sqlalchemy import RowMapping, Table, select, text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.levels import LearningLevel
from app.db.curriculum import WordSpec, stable_id
from app.db.models import Course, CourseVocabularyItem, Lesson


def normalize_headword(word: str) -> str:
    apostrophes = {0x2018: 39, 0x2019: 39, 0x02BC: 39}
    return " ".join(unicodedata.normalize("NFKC", word).casefold().translate(apostrophes).split())


class SourcedWord(WordSpec):
    alternative_translations: list[Annotated[str, Field(min_length=1, max_length=300)]]
    pronunciation: str = Field(min_length=1, max_length=120)
    part_of_speech: str = Field(min_length=1, max_length=50)
    level: LearningLevel
    category: str = Field(min_length=1, max_length=120)
    example: str = Field(min_length=1, max_length=1000)
    example_translation: str = Field(min_length=1, max_length=1000)
    course_slug: str
    lesson_slug: str
    source_url: HttpUrl
    license_id: str = Field(min_length=1, max_length=100)


async def import_words(database: Path, dataset: Path, *, apply: bool = False) -> int:
    if not database.is_file():
        raise ValueError("Prepare a dedicated test database before importing")
    engine = create_async_engine(URL.create("sqlite+aiosqlite", database=str(database.resolve())))
    table = cast(Table, CourseVocabularyItem.__table__)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("PRAGMA foreign_keys=ON"))
            await connection.execute(text("BEGIN IMMEDIATE" if apply else "BEGIN"))
            lessons = {
                (course_slug, lesson_slug): (course_id, lesson_id, level)
                for course_slug, lesson_slug, course_id, lesson_id, level in (
                    await connection.execute(
                        select(Course.slug, Lesson.slug, Course.id, Lesson.id, Course.level)
                        .join(Lesson, Lesson.course_id == Course.id)
                        .where(Course.is_published.is_(True), Lesson.is_published.is_(True))
                    )
                )
            }
            existing: dict[str, list[RowMapping]] = {}
            for row in (await connection.execute(select(table))).mappings():
                existing.setdefault(normalize_headword(row["word"]), []).append(row)
            seen = set()
            batch = []
            added = 0
            with dataset.open(encoding="utf-8") as source:
                for line_number, line in enumerate(source, 1):
                    if not line.strip():
                        continue
                    try:
                        entry = SourcedWord.model_validate_json(line)
                        word = normalize_headword(entry.word)
                        if not word or len(word) > 120 or word in seen:
                            raise ValueError("Empty, oversized or duplicate normalized headword")
                        seen.add(word)
                        scope = lessons.get((entry.course_slug, entry.lesson_slug))
                        if scope is None or scope[2] != entry.level:
                            raise ValueError(
                                "Published course and lesson must match the entry level"
                            )
                        details = entry.model_dump(
                            mode="json",
                            exclude={
                                "word",
                                "translation",
                                "example",
                                "pronunciation",
                                "course_slug",
                                "lesson_slug",
                                "level",
                            },
                        )
                        values = {
                            "id": stable_id("sourced-word", word),
                            "course_id": scope[0],
                            "lesson_id": scope[1],
                            "word": word,
                            "translation": entry.translation,
                            "example": entry.example,
                            "pronunciation": entry.pronunciation,
                            "lexical_details": details,
                        }
                        if word in existing:
                            matches = existing[word]
                            if len(matches) == 1 and all(
                                matches[0][k] == v for k, v in values.items()
                            ):
                                continue
                            raise ValueError("Entry overlaps existing vocabulary")
                        added += 1
                        if apply:
                            batch.append(values)
                            if len(batch) >= 500:
                                await connection.execute(table.insert(), batch)
                                batch.clear()
                    except ValueError as exc:
                        raise ValueError(f"{dataset.name}:{line_number}: {exc}") from exc
            if batch:
                await connection.execute(table.insert(), batch)
            if apply:
                await connection.commit()
            return added
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--test-database", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    count = asyncio.run(import_words(args.test_database, args.dataset, apply=args.apply))
    print(f"{count} words {'inserted' if args.apply else 'validated for insertion'}")


if __name__ == "__main__":
    main()
