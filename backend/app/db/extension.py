"""Additive curriculum extensions: more lessons appended to the published A0–B2 courses.

`curriculum-a0-b2.json` is a pinned release (owner-authorized SHA, immutable rows). Extension
files (`content/curriculum-extension-<level>.json`) never edit it: they append lessons after
the last existing lesson of a course, each with its own SHA. New rows are created once with
stable identities; an existing row that differs aborts the import instead of changing what
learners already saw. Lessons stay unpublished unless the caller passes the exact SHA of the
content (an explicit release decision), so importing never publishes by accident.

Quality gates stricter than the base curriculum apply to new lessons: every word has an example
sentence, explanations explain, readings are real paragraphs, answers are not always option 1.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Self, cast

from pydantic import Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import (
    ContentModel,
    Curriculum,
    LessonSpec,
    load_curriculum,
    stable_id,
)
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson
from app.db.practice import KINDS, PracticeSpec

CONTENT_DIR = Path(__file__).with_name("content")
MAX_LESSONS_PER_COURSE = 20
RowModel = type[Course] | type[Lesson] | type[Exercise] | type[CourseVocabularyItem]


class ExtensionLesson(LessonSpec):
    # Typed practice (fill the gap, word order, translate, write), same formats as the
    # practice supplement of the base lessons.
    practice: list[PracticeSpec]

    @model_validator(mode="after")
    def quality(self) -> Self:
        if [item.kind for item in self.practice] != list(KINDS):
            raise ValueError(f"{self.slug}: use each practice format once, in order")
        if any(not word.example.strip() for word in self.vocabulary):
            raise ValueError(f"{self.slug}: every word needs an example sentence")
        if len(self.reading.split()) < 55:
            raise ValueError(f"{self.slug}: the reading text must be a real paragraph (55+ words)")
        for exercise in self.exercises:
            correct = next(o.text for o in exercise.options if o.id == exercise.correct_option_id)
            if (
                exercise.explanation.strip().casefold()
                in (
                    f"correct choice: {correct}".casefold(),
                    correct.casefold(),
                )
                or len(exercise.explanation.strip()) < 20
            ):
                raise ValueError(f"{exercise.slug}: the explanation must explain, not repeat")
        if len({e.correct_option_id for e in self.exercises}) < 3:
            raise ValueError(f"{self.slug}: vary the position of the correct option")
        return self


class ExtensionCourse(ContentModel):
    slug: str
    lessons: list[ExtensionLesson] = Field(min_length=1, max_length=MAX_LESSONS_PER_COURSE - 10)


class Extension(ContentModel):
    version: Literal[1]
    status: Literal["draft"]
    courses: list[ExtensionCourse] = Field(min_length=1)

    def validate_against(self, base: Curriculum) -> None:
        """Continue each base course: positions, prerequisite chain, unique keys and words."""
        base_courses = {course.slug: course for course in base.courses}
        slugs = {lesson.slug for c in base.courses for lesson in c.lessons}
        slugs |= {e.slug for c in base.courses for lesson in c.lessons for e in lesson.exercises}
        titles = {lesson.title.casefold() for c in base.courses for lesson in c.lessons}
        for course in self.courses:
            if course.slug not in base_courses:
                raise ValueError(f"Unknown course: {course.slug}")
            base_course = base_courses[course.slug]
            previous = base_course.lessons[-1].slug
            expected = len(base_course.lessons)
            course_words = {
                w.word: w.translation for ln in base_course.lessons for w in ln.vocabulary
            }
            for lesson in course.lessons:
                expected += 1
                if lesson.position != expected:
                    raise ValueError(f"{lesson.slug}: position must be {expected}")
                if lesson.prerequisites != [previous]:
                    raise ValueError(f"{lesson.slug}: prerequisite must be {previous}")
                if not lesson.slug.startswith(course.slug + "-") or lesson.slug in slugs:
                    raise ValueError(f"{lesson.slug}: invalid or duplicate lesson slug")
                if lesson.title.casefold() in titles:
                    raise ValueError(f"{lesson.slug}: duplicate lesson title")
                slugs.add(lesson.slug)
                titles.add(lesson.title.casefold())
                previous = lesson.slug
                for exercise in lesson.exercises:
                    if not exercise.slug.startswith(lesson.slug + "-") or exercise.slug in slugs:
                        raise ValueError(f"{exercise.slug}: invalid or duplicate exercise slug")
                    slugs.add(exercise.slug)
                fresh = 0
                for word in lesson.vocabulary:
                    if word.word in course_words:
                        if course_words[word.word] != word.translation:
                            raise ValueError(f"{lesson.slug}: conflicting translation: {word.word}")
                    else:
                        fresh += 1
                        course_words[word.word] = word.translation
                if fresh < 8:
                    raise ValueError(f"{lesson.slug}: teach at least 8 words new to the course")


def load_extensions(directory: Path = CONTENT_DIR) -> list[tuple[str, Extension]]:
    return [
        (path.name, Extension.model_validate_json(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("curriculum-extension-*.json"))
    ]


def extension_sha(extension: Extension) -> str:
    return hashlib.sha256(
        json.dumps(extension.model_dump(), ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def rows(
    extension: Extension, base: Curriculum, only: set[str] | None = None
) -> list[tuple[RowModel, Any, dict[str, Any]]]:
    """Canonical rows in FK order (optionally only some courses); words carry their lesson."""
    base_words = {
        course.slug: {w.word for lesson in course.lessons for w in lesson.vocabulary}
        for course in base.courses
    }
    planned: list[tuple[RowModel, Any, dict[str, Any]]] = []
    for course in extension.courses:
        if only is not None and course.slug not in only:
            continue
        course_id = stable_id("course", course.slug)
        seen = set(base_words[course.slug])
        for lesson in course.lessons:
            lesson_id = stable_id("lesson", lesson.slug)
            planned.append(
                (
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
            )
            for exercise in lesson.exercises:
                planned.append(
                    (
                        Exercise,
                        stable_id("exercise", exercise.slug),
                        dict(lesson_id=lesson_id, **exercise.model_dump(exclude={"phase"})),
                    )
                )
            start = len(lesson.exercises)
            for index, item in enumerate(lesson.practice, start=1):
                slug = f"{lesson.slug}-extra-{index}"
                planned.append(
                    (
                        Exercise,
                        stable_id("exercise", slug),
                        dict(
                            lesson_id=lesson_id,
                            slug=slug,
                            position=start + index,
                            type="self_check" if item.kind == "write" else "text",
                            prompt=item.prompt,
                            points=1,
                            accepted_answers=item.accepted_answers or None,
                            model_answer=item.model_answer,
                            explanation=item.explanation,
                        ),
                    )
                )
            for word in lesson.vocabulary:
                if word.word in seen:
                    continue
                seen.add(word.word)
                planned.append(
                    (
                        CourseVocabularyItem,
                        stable_id("word", course.slug + "/" + word.word),
                        dict(course_id=course_id, lesson_id=lesson_id, **word.model_dump()),
                    )
                )
    return planned


async def import_extension(
    db: AsyncSession,
    extension: Extension,
    *,
    base: Curriculum | None = None,
    publish_sha: str | None = None,
) -> dict:
    """Add missing rows; refuse to change existing ones. Commits on success.

    New lessons are published only when `publish_sha` equals this content's SHA.
    """
    extension = Extension.model_validate(extension.model_dump())
    base = base or load_curriculum()
    extension.validate_against(base)
    digest = extension_sha(extension)
    if publish_sha is not None and publish_sha != digest:
        raise ValueError("Publication SHA does not match this extension")
    present_courses = set(
        await db.scalars(
            select(Course.slug).where(Course.slug.in_([c.slug for c in extension.courses]))
        )
    )
    planned = rows(extension, base, present_courses)
    added = existing = 0
    for model, identity, values in planned:
        found = await db.get(model, identity)
        if found is not None:
            if any(getattr(found, key) != value for key, value in values.items()):
                raise ValueError(f"Existing content differs; refusing overwrite: {identity}")
            existing += 1
            if publish_sha is not None and isinstance(found, Lesson):
                found.is_published = True
            continue
        if model is CourseVocabularyItem:
            taken = await db.scalar(
                select(model.id).where(
                    model.course_id == values["course_id"], model.word == values["word"]
                )
            )
        else:
            slug_model = cast(type[Course] | type[Lesson] | type[Exercise], model)
            taken = await db.scalar(select(slug_model.id).where(slug_model.slug == values["slug"]))
        if taken is not None:
            raise ValueError(f"Source key owned by other content: {identity}")
        row = model(id=identity, **values)
        if isinstance(row, Lesson):
            row.is_published = publish_sha is not None
        db.add(row)
        await db.flush()
        added += 1
    await db.commit()
    return {
        "sha256": digest,
        "lessons": sum(len(c.lessons) for c in extension.courses),
        "added_rows": added,
        "existing_rows": existing,
        "published": publish_sha is not None,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="No database connection")
    parser.add_argument("--apply-draft", action="store_true", help="Import unpublished")
    parser.add_argument("--publish-sha", help="Import AND publish; must equal the file's SHA")
    args = parser.parse_args()
    base = load_curriculum()
    loaded = load_extensions()
    for name, extension in loaded:
        extension.validate_against(base)
        print(
            json.dumps(
                dict(
                    file=name,
                    valid=True,
                    sha256=extension_sha(extension),
                    lessons=sum(len(c.lessons) for c in extension.courses),
                )
            )
        )
    if args.validate_only or not (args.apply_draft or args.publish_sha):
        return
    from app.core.config import get_settings
    from app.db.session import SessionLocal

    if get_settings().is_production:
        raise SystemExit("Refusing to import extensions from this CLI in production")
    async with SessionLocal() as db:
        for name, extension in loaded:
            publish = args.publish_sha if args.publish_sha == extension_sha(extension) else None
            result = await import_extension(db, extension, base=base, publish_sha=publish)
            print(json.dumps(dict(file=name, **result)))


if __name__ == "__main__":
    asyncio.run(main())
