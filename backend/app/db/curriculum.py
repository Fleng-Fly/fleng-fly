"""Validate and import the reviewed, versioned curriculum into existing models.

Default CLI mode is read-only. Draft import and reviewed publication are explicit.
Existing content is immutable here: a conflict aborts rather than rewriting work
with existing submissions. No provider calls, user writes or automatic startup hook.
"""

import argparse
import asyncio
import hashlib
import json
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, Self, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.levels import LearningLevel
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson

CONTENT = Path(__file__).with_name("content") / "curriculum-a0-b2.json"


def stable_id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://fleng.local/curriculum/v1/{kind}/{key}")


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class WordSpec(ContentModel):
    word: str = Field(min_length=1, max_length=120)
    translation: str = Field(min_length=1, max_length=300)
    example: str = Field(max_length=1000)

    @model_validator(mode="after")
    def canonical(self) -> Self:
        self.word = unicodedata.normalize("NFC", self.word).casefold()
        self.translation = unicodedata.normalize("NFC", self.translation)
        return self


class OptionSpec(ContentModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ExerciseSpec(ContentModel):
    slug: str = Field(pattern=r"^fleng-[a-z0-9-]+$")
    phase: Literal["practice", "check"]
    type: Literal["single_choice"]
    prompt: str = Field(min_length=1, max_length=2000)
    options: list[OptionSpec] = Field(min_length=3, max_length=3)
    correct_option_id: str
    explanation: str = Field(min_length=1)
    position: int = Field(ge=1)
    points: Literal[1]

    @model_validator(mode="after")
    def answer_valid(self) -> Self:
        ids = [o.id for o in self.options]
        if len(set(ids)) != len(ids) or self.correct_option_id not in ids:
            raise ValueError("Invalid answer reference")
        if len({o.text.casefold() for o in self.options}) != len(ids):
            raise ValueError("Duplicate options")
        return self


class LessonSpec(ContentModel):
    slug: str = Field(pattern=r"^fleng-[a-z0-9-]+$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    goals: list[str] = Field(min_length=2)
    grammar: str = Field(min_length=1)
    prerequisites: list[str]
    estimated_minutes: int = Field(ge=10, le=60)
    position: int = Field(ge=1)
    theory: str = Field(min_length=180)
    reading: str = Field(min_length=40)
    examples: list[str] = Field(min_length=3)
    vocabulary: list[WordSpec] = Field(min_length=10, max_length=15)
    exercises: list[ExerciseSpec] = Field(min_length=8, max_length=13)

    @model_validator(mode="after")
    def lesson_valid(self) -> Self:
        if any(not s.strip() for s in self.goals + self.examples):
            raise ValueError("Blank goals/examples")
        words = [w.word for w in self.vocabulary]
        if len(set(words)) != len(words):
            raise ValueError("Duplicate lesson vocabulary")
        for phase, low, high in [("practice", 5, 8), ("check", 3, 5)]:
            if not low <= sum(e.phase == phase for e in self.exercises) <= high:
                raise ValueError(f"Invalid {phase} exercise count")
        if [e.position for e in self.exercises] != list(range(1, len(self.exercises) + 1)):
            raise ValueError("Exercise positions must be contiguous")
        return self

    def rendered_theory(self) -> str:
        words = "\n".join(f"- {w.word} — {w.translation}" for w in self.vocabulary)
        return (
            "## Learning goals\n\n"
            + "\n".join(f"- {g}" for g in self.goals)
            + f"\n\n## {self.grammar}\n\n{self.theory}\n\n## Examples\n\n"
            + "\n".join(f"- {e}" for e in self.examples)
            + f"\n\n## Read in context\n\n{self.reading}\n\n## Vocabulary\n\n{words}"
        )


class CourseSpec(ContentModel):
    slug: str
    title: str = Field(min_length=1)
    level: LearningLevel
    description: str = Field(min_length=1)
    position: int
    status: Literal["draft"]
    lessons: list[LessonSpec] = Field(min_length=10, max_length=10)


class Curriculum(ContentModel):
    version: Literal[1]
    status: Literal["draft"]
    translation_language: Literal["uk"]
    courses: list[CourseSpec] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def references_valid(self) -> Self:
        if [c.level for c in self.courses] != ["A0", "A1", "A2", "B1", "B2"]:
            raise ValueError("Courses must progress from A0 to B2")
        seen: set[str] = set()
        previous = None
        for course in self.courses:
            if course.slug != f"fleng-{course.level.lower()}":
                raise ValueError("Course slug/level mismatch")
            if [lesson.position for lesson in course.lessons] != list(range(1, 11)):
                raise ValueError("Lesson positions must be contiguous")
            course_words: dict[str, str] = {}
            for lesson in course.lessons:
                if not lesson.slug.startswith(course.slug + "-"):
                    raise ValueError("Lesson/course mismatch")
                if lesson.prerequisites != ([previous] if previous else []):
                    raise ValueError("Missing, cyclic or out-of-order prerequisite")
                if lesson.slug in seen:
                    raise ValueError("Duplicate lesson slug")
                seen.add(lesson.slug)
                previous = lesson.slug
                for word in lesson.vocabulary:
                    if word.word in course_words and course_words[word.word] != word.translation:
                        raise ValueError("Conflicting translations in course")
                    course_words[word.word] = word.translation
                for exercise in lesson.exercises:
                    if not exercise.slug.startswith(lesson.slug + "-") or exercise.slug in seen:
                        raise ValueError("Invalid/duplicate exercise slug")
                    seen.add(exercise.slug)
        if (
            len({lesson.title.casefold() for course in self.courses for lesson in course.lessons})
            != 50
        ):
            raise ValueError("Duplicate lesson titles")
        return self


def load_curriculum(path: Path = CONTENT) -> Curriculum:
    return Curriculum.model_validate_json(path.read_text(encoding="utf-8"))


def content_sha(content: Curriculum) -> str:
    return hashlib.sha256(
        json.dumps(content.model_dump(), ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


RowModel = type[Course] | type[Lesson] | type[Exercise] | type[CourseVocabularyItem]


def rows(content: Curriculum) -> Iterator[tuple[RowModel, UUID, dict[str, Any]]]:
    """One canonical row per source identity, in FK insertion order."""
    for course in content.courses:
        course_id = stable_id("course", course.slug)
        yield (
            Course,
            course_id,
            dict(
                slug=course.slug,
                title=course.title,
                description=course.description,
                level=course.level,
                position=course.position,
            ),
        )
        words: dict[str, WordSpec] = {}
        for lesson in course.lessons:
            lesson_id = stable_id("lesson", lesson.slug)
            yield (
                Lesson,
                lesson_id,
                dict(
                    slug=lesson.slug,
                    course_id=course_id,
                    title=lesson.title,
                    summary=lesson.summary,
                    theory=lesson.rendered_theory(),
                    position=lesson.position,
                    estimated_minutes=lesson.estimated_minutes,
                ),
            )
            for exercise in lesson.exercises:
                yield (
                    Exercise,
                    stable_id("exercise", exercise.slug),
                    dict(lesson_id=lesson_id, **exercise.model_dump(exclude={"phase"})),
                )
            for word in lesson.vocabulary:
                words.setdefault(word.word, word)
        for word in words.values():
            yield (
                CourseVocabularyItem,
                stable_id("word", course.slug + "/" + word.word),
                dict(course_id=course_id, **word.model_dump()),
            )


async def import_curriculum(
    db: AsyncSession,
    content: Curriculum,
    *,
    apply: bool = False,
    reviewed_sha: str | None = None,
) -> dict:
    # Revalidate even when called directly with mutated models.
    content = Curriculum.model_validate(content.model_dump())
    digest = content_sha(content)
    if reviewed_sha is not None and reviewed_sha != digest:
        raise ValueError("Reviewed content SHA does not match this content")
    planned = list(rows(content))
    additions = []
    existing = []
    for model, identity, values in planned:
        row = await db.get(model, identity)
        if row is not None:
            if any(getattr(row, k) != v for k, v in values.items()):
                raise ValueError(f"Existing content differs; refusing overwrite: {identity}")
            existing.append(row)
        else:
            if model is CourseVocabularyItem:
                collision = await db.scalar(
                    select(model.id).where(
                        model.course_id == values["course_id"], model.word == values["word"]
                    )
                )
            else:
                slug_model = cast(type[Course] | type[Lesson] | type[Exercise], model)
                collision = await db.scalar(
                    select(slug_model.id).where(slug_model.slug == values["slug"])
                )
            if collision is not None:
                raise ValueError(f"Source key owned by other content: {identity}")
            additions.append((model, identity, values))
    report = dict(
        sha256=digest,
        status="reviewed" if reviewed_sha else "draft",
        courses=5,
        lessons=50,
        exercises=sum(
            len(lesson.exercises) for course in content.courses for lesson in course.lessons
        ),
        words=sum(model is CourseVocabularyItem for model, _, _ in planned),
        new_rows=len(additions),
        existing_rows=len(existing),
        applied=apply,
    )
    if not apply:
        return report
    # Preflight finishes before the first write; caller rolls back on any failure.
    for model, identity, values in additions:
        row = model(id=identity, **values)
        if isinstance(row, (Course, Lesson)):
            row.is_published = reviewed_sha is not None
        db.add(row)
        await db.flush()
    if reviewed_sha is not None:
        for row in existing:
            if isinstance(row, (Course, Lesson)):
                row.is_published = True
    await db.commit()
    return report


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="No database connection")
    parser.add_argument("--apply-draft", action="store_true", help="Import unpublished content")
    parser.add_argument(
        "--publish-reviewed-sha", help="Explicit review acknowledgement for this SHA"
    )
    args = parser.parse_args()
    if args.apply_draft and args.publish_reviewed_sha:
        parser.error("Choose draft import OR reviewed publication")
    if args.validate_only and (args.apply_draft or args.publish_reviewed_sha):
        parser.error("Validation cannot apply/publish")
    content = load_curriculum()
    if args.validate_only:
        print(json.dumps(dict(valid=True, sha256=content_sha(content), courses=5, lessons=50)))
        return
    from app.core.config import get_settings
    from app.db.session import SessionLocal, engine

    if get_settings().is_production and (args.apply_draft or args.publish_reviewed_sha):
        raise RuntimeError("Curriculum writes are disabled in production")
    try:
        async with SessionLocal() as db:
            result = await import_curriculum(
                db,
                content,
                apply=bool(args.apply_draft or args.publish_reviewed_sha),
                reviewed_sha=args.publish_reviewed_sha,
            )
            print(json.dumps(result))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
