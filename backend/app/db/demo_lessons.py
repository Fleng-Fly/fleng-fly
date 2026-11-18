"""Additive vocabulary and practice for the seeded demo lessons.

The two demo courses (English Foundations, Everyday Conversations) are created by the
catalog seed and are listed first. Without this step they would keep three exercises per
lesson and no words, so finishing them would never fill the personal dictionary. The
content in `content/demo-lessons-extras.json` brings them to the same standard as the
curriculum lessons: ten words per lesson and ten exercises (3 existing + 7 new).

Rows are added once under stable ids; an existing row that differs aborts the import
instead of changing learners' graded content. Lessons that do not exist are skipped.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import stable_id
from app.db.models import CourseVocabularyItem, Exercise, Lesson
from app.db.practice import PracticeSpec

CONTENT = Path(__file__).with_name("content") / "demo-lessons-extras.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DemoWord(_Strict):
    word: str = Field(min_length=1, max_length=120)
    translation: str = Field(min_length=1, max_length=300)
    example: str = Field(min_length=1, max_length=1000)


class DemoLesson(_Strict):
    vocabulary: list[DemoWord] = Field(min_length=8, max_length=15)
    practice: list[PracticeSpec] = Field(min_length=4, max_length=12)


class DemoContent(_Strict):
    version: Literal[1]
    review_status: Literal["authored", "reviewed"]
    note: str
    lessons: dict[str, DemoLesson]


def load_demo_content(path: Path = CONTENT) -> DemoContent:
    return DemoContent.model_validate_json(path.read_text(encoding="utf-8"))


async def import_demo_lessons(db: AsyncSession, content: DemoContent | None = None) -> dict:
    """Add missing words and exercises to the demo lessons that exist. Commits on success."""
    content = content or load_demo_content()
    words_added = words_existing = practice_added = practice_existing = 0
    for slug, spec in content.lessons.items():
        lesson = await db.scalar(select(Lesson).where(Lesson.slug == slug))
        if lesson is None:
            continue
        for item in spec.vocabulary:
            values = {
                "id": stable_id("demo-word", f"{slug}:{item.word}"),
                "course_id": lesson.course_id,
                "lesson_id": lesson.id,
                "word": item.word,
                "translation": item.translation,
                "example": item.example,
            }
            word_row = await db.get(CourseVocabularyItem, values["id"])
            if word_row is not None:
                if any(getattr(word_row, key) != value for key, value in values.items()):
                    raise ValueError(f"Existing demo word differs; refusing overwrite: {item.word}")
                words_existing += 1
                continue
            if await db.scalar(
                select(CourseVocabularyItem.id).where(
                    CourseVocabularyItem.course_id == lesson.course_id,
                    CourseVocabularyItem.word == item.word,
                )
            ):
                raise ValueError(f"Demo word owned by other content: {item.word}")
            db.add(CourseVocabularyItem(**values))
            words_added += 1

        start = (
            await db.scalar(
                select(func.max(Exercise.position)).where(
                    Exercise.lesson_id == lesson.id, Exercise.slug.not_like("%-extra-%")
                )
            )
            or 0
        )
        for index, practice in enumerate(spec.practice, start=1):
            exercise_slug = f"{slug}-extra-{index}"
            values = {
                "id": stable_id("exercise", exercise_slug),
                "lesson_id": lesson.id,
                "slug": exercise_slug,
                "position": start + index,
                "type": "self_check" if practice.kind == "write" else "text",
                "prompt": practice.prompt,
                "points": 1,
                "accepted_answers": practice.accepted_answers or None,
                "model_answer": practice.model_answer,
                "explanation": practice.explanation,
            }
            exercise_row = await db.get(Exercise, values["id"])
            if exercise_row is not None:
                if any(getattr(exercise_row, key) != value for key, value in values.items()):
                    raise ValueError(f"Existing demo practice differs; refusing: {exercise_slug}")
                practice_existing += 1
                continue
            if await db.scalar(select(Exercise.id).where(Exercise.slug == exercise_slug)):
                raise ValueError(f"Practice slug owned by other content: {exercise_slug}")
            db.add(Exercise(**values))
            practice_added += 1
    await db.commit()
    return {
        "words_added": words_added,
        "words_existing": words_existing,
        "practice_added": practice_added,
        "practice_existing": practice_existing,
    }
