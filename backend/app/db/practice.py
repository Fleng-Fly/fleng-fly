"""Additive practice for curriculum lessons (`content/curriculum-practice-supplement.json`).

The published curriculum file is pinned by a SHA and never rewritten. This supplement
adds four more exercises per lesson in other formats (typed gap fill, sentence
building, translation, short written answer) using the existing exercise types
(`text`, `self_check`). Rows are added once, keyed by stable slugs/IDs; an existing row
that differs aborts the import instead of changing learners' graded content.
The vocabulary supplement adds ten word pairs and their translation questions
to each lesson after those four exercises.
"""

import re
from pathlib import Path
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Table, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import Curriculum, WordSpec, stable_id
from app.db.models import CourseVocabularyItem, Exercise, Lesson

CONTENT = Path(__file__).with_name("content") / "curriculum-practice-supplement.json"
VOCABULARY_CONTENT = CONTENT.with_name("curriculum-vocabulary-supplement.json")
KINDS = ("fill_gap", "word_order", "translate", "write")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PracticeSpec(_Strict):
    kind: Literal["fill_gap", "word_order", "translate", "write"]
    prompt: str = Field(min_length=1, max_length=2000)
    accepted_answers: list[str] = Field(default_factory=list, max_length=6)
    model_answer: str | None = Field(default=None, max_length=1000)
    explanation: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def answers_fit_kind(self) -> Self:
        if self.kind == "write":
            if not self.model_answer or self.accepted_answers:
                raise ValueError("A written answer needs a model answer only")
        elif not self.accepted_answers or self.model_answer:
            raise ValueError("Typed exercises need accepted answers only")
        if self.kind == "fill_gap" and "___" not in self.prompt:
            raise ValueError("Mark the gap with ___")
        if self.kind == "word_order":
            words = self.prompt.split(":", 1)[1].split(" / ")
            tokens = sorted(w.strip().casefold() for w in words)
            first = re.sub(r"[.,?!]", "", self.accepted_answers[0]).casefold().split()
            if sorted(first) != tokens:
                raise ValueError("The first answer must use exactly the given words")
        if self.kind == "translate" and not self.prompt.startswith("Translate into English:"):
            raise ValueError("Translation prompts start with 'Translate into English:'")
        return self


class PracticeSupplement(_Strict):
    version: Literal[1]
    review_status: Literal["authored", "reviewed"]
    note: str
    lessons: dict[str, list[PracticeSpec]]

    @model_validator(mode="after")
    def four_formats_per_lesson(self) -> Self:
        for slug, items in self.lessons.items():
            if [item.kind for item in items] != list(KINDS):
                raise ValueError(f"{slug}: use each practice format once, in order")
        return self


def load_supplement(path: Path = CONTENT) -> PracticeSupplement:
    return PracticeSupplement.model_validate_json(path.read_text(encoding="utf-8"))


def exercise_rows(content: Curriculum, supplement: PracticeSupplement) -> list[dict]:
    """Exercise rows after each lesson's existing exercises, with stable identities."""
    lessons = {lesson.slug: lesson for course in content.courses for lesson in course.lessons}
    unknown = set(supplement.lessons) - set(lessons)
    if unknown:
        raise ValueError(f"Supplement references unknown lessons: {sorted(unknown)}")
    rows = []
    for slug, items in supplement.lessons.items():
        start = len(lessons[slug].exercises)
        for index, item in enumerate(items, start=1):
            exercise_slug = f"{slug}-extra-{index}"
            rows.append(
                {
                    "id": stable_id("exercise", exercise_slug),
                    "lesson_id": stable_id("lesson", slug),
                    "slug": exercise_slug,
                    "position": start + index,
                    "type": "self_check" if item.kind == "write" else "text",
                    "prompt": item.prompt,
                    "points": 1,
                    "accepted_answers": item.accepted_answers or None,
                    "model_answer": item.model_answer,
                    "explanation": item.explanation,
                }
            )
    return rows


async def import_practice(
    db: AsyncSession, content: Curriculum, supplement: PracticeSupplement | None = None
) -> dict:
    """Add missing supplement exercises to lessons that exist. Commits on success."""
    supplement = supplement or load_supplement()
    rows = exercise_rows(content, supplement)
    present = set(
        await db.scalars(select(Lesson.id).where(Lesson.id.in_({r["lesson_id"] for r in rows})))
    )
    added = existing = 0
    for values in rows:
        if values["lesson_id"] not in present:
            continue
        row = await db.get(Exercise, values["id"])
        if row is not None:
            if any(getattr(row, key) != value for key, value in values.items()):
                raise ValueError(f"Existing practice differs; refusing overwrite: {values['slug']}")
            existing += 1
            continue
        if await db.scalar(select(Exercise.id).where(Exercise.slug == values["slug"])):
            raise ValueError(f"Practice slug owned by other content: {values['slug']}")
        db.add(Exercise(**values))
        added += 1
    await db.commit()
    return {"added": added, "existing": existing}


class VocabularySupplement(_Strict):
    version: Literal[1]
    lessons: dict[str, list[WordSpec]]


def vocabulary_rows(
    content: Curriculum, supplement: PracticeSupplement
) -> tuple[list[dict], list[dict]]:
    """Build ten lesson words and one translation question per word."""
    expansion = VocabularySupplement.model_validate_json(
        VOCABULARY_CONTENT.read_text(encoding="utf-8")
    )
    expected = {lesson.slug for course in content.courses for lesson in course.lessons}
    if set(expansion.lessons) != expected:
        raise ValueError("Vocabulary supplement must cover exactly the curriculum lessons")

    words: list[dict] = []
    exercises: list[dict] = []
    for course in content.courses:
        known = {item.word for lesson in course.lessons for item in lesson.vocabulary}
        course_id = stable_id("course", course.slug)
        for lesson in course.lessons:
            items = expansion.lessons[lesson.slug]
            new_words = {item.word for item in items}
            if len(items) != 10 or len(new_words) != 10 or known & new_words:
                raise ValueError(f"{lesson.slug}: expected ten new course words")
            if len({item.translation.casefold() for item in items}) != 10:
                raise ValueError(f"{lesson.slug}: translations must distinguish the options")
            known.update(new_words)
            lesson_id = stable_id("lesson", lesson.slug)
            start = len(lesson.exercises) + len(supplement.lessons[lesson.slug])
            for index, item in enumerate(items):
                words.append(
                    {
                        "id": stable_id("word", f"{course.slug}/{item.word}"),
                        "course_id": course_id,
                        "lesson_id": lesson_id,
                        **item.model_dump(),
                    }
                )
                to_english = index % 2 == 1
                prompt = (
                    f"Which English expression means «{item.translation}»?"
                    if to_english
                    else f"What is the Ukrainian translation of «{item.word}»?"
                )
                choices = [items[(index + offset) % len(items)] for offset in (3, 7)]
                correct_index = (index + lesson.position) % 3
                choices.insert(correct_index, item)
                slug = f"{lesson.slug}-vocabulary-{index + 1}"
                exercises.append(
                    {
                        "id": stable_id("exercise", slug),
                        "lesson_id": lesson_id,
                        "slug": slug,
                        "position": start + index + 1,
                        "type": "single_choice",
                        "prompt": prompt,
                        "options": [
                            {
                                "id": str(number),
                                "text": choice.word if to_english else choice.translation,
                            }
                            for number, choice in enumerate(choices, start=1)
                        ],
                        "correct_option_id": str(correct_index + 1),
                        "points": 1,
                        "explanation": f"{item.word} — {item.translation}.",
                    }
                )
    return words, exercises


async def import_vocabulary_practice(db: AsyncSession, content: Curriculum) -> None:
    """Install the new words and their questions atomically after the base practice."""
    words, exercises = vocabulary_rows(content, load_supplement())
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    for model, rows in ((CourseVocabularyItem, words), (Exercise, exercises)):
        table = cast(Table, model.__table__)
        query = select(table).where(table.c.id.in_([r["id"] for r in rows]))
        existing = {row["id"]: row for row in (await db.execute(query)).mappings()}
        missing = [values for values in rows if values["id"] not in existing]
        if missing:
            await db.execute(insert(table).on_conflict_do_nothing(index_elements=["id"]), missing)
            existing = {row["id"]: row for row in (await db.execute(query)).mappings()}
        for values in rows:
            row = existing[values["id"]]
            if any(row[key] != value for key, value in values.items()):
                raise ValueError(f"Existing vocabulary content differs: {row['id']}")
    await db.commit()
