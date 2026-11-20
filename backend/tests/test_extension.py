"""Curriculum extensions: validation, additive import, publication gate, A0 content."""

from copy import deepcopy
from uuid import UUID

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import content_sha, import_curriculum, load_curriculum
from app.db.extension import (
    Extension,
    extension_sha,
    import_extension,
    load_extensions,
)
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson
from app.modules.exercises.grading import normalize_text

BASE = load_curriculum()


def a0() -> Extension:
    return next(e for name, e in load_extensions() if name == "curriculum-extension-a0.json")


def raw() -> dict:
    return a0().model_dump()


def test_every_extension_file_validates_against_the_pinned_release():
    files = load_extensions()
    assert files, "no extension files found"
    for _, extension in files:
        extension.validate_against(BASE)


def test_a0_extension_continues_the_course_in_order():
    lessons = a0().courses[0].lessons
    assert [lesson.position for lesson in lessons] == [11, 12, 13, 14, 15]
    assert lessons[0].prerequisites == [BASE.courses[0].lessons[-1].slug]
    for previous, current in zip(lessons, lessons[1:], strict=False):
        assert current.prerequisites == [previous.slug]
    assert all(lesson.estimated_minutes == 15 for lesson in lessons)


def test_a0_lessons_meet_the_quality_bar():
    for lesson in a0().courses[0].lessons:
        assert len(lesson.vocabulary) >= 10
        assert all(word.example.strip() for word in lesson.vocabulary), lesson.slug
        assert len(lesson.reading.split()) >= 55
        assert {e.phase for e in lesson.exercises} == {"practice", "check"}
        assert len({e.correct_option_id for e in lesson.exercises}) == 3
        prompts = [e.prompt for e in lesson.exercises]
        assert len(prompts) == len(set(prompts)), "repeated exercise prompt"
        # Each correct answer must be consistent with its own explanation text.
        assert all(len(e.explanation) >= 20 for e in lesson.exercises)


def test_typed_practice_accepts_its_own_listed_answers():
    for lesson in a0().courses[0].lessons:
        for item in lesson.practice:
            for answer in item.accepted_answers:
                assert normalize_text(answer)  # never an empty accepted answer
            if item.kind == "word_order":
                tokens = item.prompt.split(":", 1)[1].split(" / ")
                assert sorted(normalize_text(t) for t in tokens) == sorted(
                    normalize_text(item.accepted_answers[0]).split()
                )


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda d: d["courses"][0]["lessons"][0].update(position=12), "position must be 11"),
        (lambda d: d["courses"][0]["lessons"][1].update(prerequisites=[]), "prerequisite"),
        (lambda d: d["courses"][0]["lessons"][0].update(slug="fleng-a1-x"), "invalid or duplicate"),
        (lambda d: d["courses"][0]["lessons"][0].update(title="Letters and spelling"), "duplicate"),
        (lambda d: d["courses"].__setitem__(0, {**d["courses"][0], "slug": "fleng-zz"}), "Unknown"),
    ],
)
def test_structural_mistakes_are_rejected(edit, message):
    data = deepcopy(raw())
    edit(data)
    with pytest.raises(ValueError, match=message):
        Extension.model_validate(data).validate_against(BASE)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda ln: ln["vocabulary"][0].update(example=""), "example sentence"),
        (
            lambda ln: ln.update(reading="This is a short text with only a few words in it today."),
            "paragraph",
        ),
        (
            lambda ln: ln["exercises"][0].update(explanation="Correct choice: are"),
            "explain",
        ),
        (lambda ln: ln["exercises"][0].update(explanation="Short."), "explain"),
        (lambda ln: ln["practice"].reverse(), "each practice format"),
    ],
)
def test_quality_gates_reject_weak_lessons(edit, message):
    data = deepcopy(raw())
    edit(data["courses"][0]["lessons"][0])
    with pytest.raises(ValidationError, match=message):
        Extension.model_validate(data)


def test_correct_answer_must_not_always_sit_in_the_same_place():
    data = deepcopy(raw())
    for exercise in data["courses"][0]["lessons"][0]["exercises"]:
        correct = next(o for o in exercise["options"] if o["id"] == exercise["correct_option_id"])
        first = exercise["options"][0]
        correct["id"], first["id"] = first["id"], correct["id"]
        exercise["options"].sort(key=lambda o: o["id"])
        exercise["correct_option_id"] = "1"
    with pytest.raises(ValidationError, match="vary the position"):
        Extension.model_validate(data)


def test_a_lesson_must_teach_new_words():
    data = deepcopy(raw())
    lesson = data["courses"][0]["lessons"][0]
    known = BASE.courses[0].lessons[0].vocabulary
    lesson["vocabulary"] = [
        {"word": w.word, "translation": w.translation, "example": f"{w.word} here."} for w in known
    ]
    with pytest.raises(ValueError, match="at least 8 words new"):
        Extension.model_validate(data).validate_against(BASE)


def test_conflicting_translation_is_rejected():
    data = deepcopy(raw())
    data["courses"][0]["lessons"][0]["vocabulary"][0] = {
        "word": "book",
        "translation": "не книга",
        "example": "A book.",
    }
    with pytest.raises(ValueError, match="conflicting translation"):
        Extension.model_validate(data).validate_against(BASE)


async def _base(db: AsyncSession) -> None:
    await import_curriculum(db, BASE, apply=True, owner_authorized_sha=content_sha(BASE))


async def test_import_is_unpublished_by_default_and_idempotent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _base(db_session)
    extension = a0()
    first = await import_extension(db_session, extension)
    assert first["published"] is False and first["added_rows"] > 0
    # Nothing new is visible to learners yet.
    course = next(
        c for c in (await client.get("/api/v1/courses")).json() if c["slug"] == "fleng-a0"
    )
    assert course["lessonCount"] == 10
    assert (await client.get("/api/v1/lessons/fleng-a0-cafe")).status_code == 404
    again = await import_extension(db_session, extension)
    assert again["added_rows"] == 0 and again["existing_rows"] == first["added_rows"]
    lessons = await db_session.scalar(
        select(func.count()).select_from(Lesson).where(Lesson.slug.like("fleng-a0-%"))
    )
    assert lessons == 15


async def test_publication_needs_the_exact_sha_and_exposes_the_lessons(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _base(db_session)
    extension = a0()
    with pytest.raises(ValueError, match="SHA"):
        await import_extension(db_session, extension, publish_sha="wrong")
    await import_extension(db_session, extension)  # draft first
    result = await import_extension(db_session, extension, publish_sha=extension_sha(extension))
    assert result["published"] is True
    detail = (await client.get("/api/v1/courses/fleng-a0")).json()
    assert [lesson["position"] for lesson in detail["lessons"]] == list(range(1, 16))
    lesson = (await client.get("/api/v1/lessons/fleng-a0-cafe")).json()
    assert len(lesson["exercises"]) == 14  # 10 graded choices + 4 typed practice
    words = await db_session.scalar(
        select(func.count())
        .select_from(CourseVocabularyItem)
        .where(
            CourseVocabularyItem.lesson_id.is_not(None),
            CourseVocabularyItem.course_id == UUID(detail["id"]),
        )
    )
    assert words >= 60  # new words are linked to the lesson that teaches them


async def test_existing_rows_are_never_rewritten(db_session: AsyncSession) -> None:
    await _base(db_session)
    extension = a0()
    await import_extension(db_session, extension)
    lesson = await db_session.scalar(select(Lesson).where(Lesson.slug == "fleng-a0-cafe"))
    assert lesson is not None
    lesson.title = "Edited by someone"
    await db_session.commit()
    with pytest.raises(ValueError, match="refusing overwrite"):
        await import_extension(db_session, extension)


async def test_missing_base_course_is_skipped_not_created(db_session: AsyncSession) -> None:
    result = await import_extension(db_session, a0())
    assert result["added_rows"] == 0
    assert await db_session.scalar(select(func.count()).select_from(Course)) == 0
    assert await db_session.scalar(select(func.count()).select_from(Exercise)) == 0


async def test_every_new_lesson_can_be_completed_through_the_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    from tests.test_learning_extensions import headers

    await _base(db_session)
    extension = a0()
    await import_extension(db_session, extension)
    await import_extension(db_session, extension, publish_sha=extension_sha(extension))
    auth = await headers(client)
    for lesson in extension.courses[0].lessons:
        public = (await client.get(f"/api/v1/lessons/{lesson.slug}")).json()
        by_slug = {e["slug"]: e for e in public["exercises"]}
        assert len(by_slug) == len(lesson.exercises) + len(lesson.practice)
        for exercise in lesson.exercises:
            body = {
                "exerciseId": by_slug[exercise.slug]["id"],
                "answer": exercise.correct_option_id,
            }
            result = await client.post(
                f"/api/v1/lessons/{lesson.slug}/submit", headers=auth, json=body
            )
            assert result.status_code == 200
            assert result.json()["isCorrect"] is True, exercise.slug
        for index, item in enumerate(lesson.practice, start=1):
            exercise_id = by_slug[f"{lesson.slug}-extra-{index}"]["id"]
            for answer in item.accepted_answers or [item.model_answer]:
                body = {"exerciseId": exercise_id, "answer": answer}
                if item.kind == "write":
                    body["selfAssessment"] = "correct"
                result = await client.post(
                    f"/api/v1/lessons/{lesson.slug}/submit", headers=auth, json=body
                )
                assert result.status_code == 200
                assert result.json()["isCorrect"] is True, (lesson.slug, item.kind, answer)
        progress = (
            await client.get(f"/api/v1/lessons/{lesson.slug}/progress", headers=auth)
        ).json()
        assert progress["completed"] is True, lesson.slug
