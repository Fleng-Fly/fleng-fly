"""The seeded demo lessons reach the same standard as the curriculum: words and 10 exercises."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.demo_lessons import import_demo_lessons, load_demo_content
from app.db.models import CourseVocabularyItem, Exercise, Lesson, VocabularyItem
from app.db.seed import seed_catalog
from app.modules.exercises.grading import grade_objective

LESSON = "greetings-and-introductions"


async def _prepare(db: AsyncSession) -> dict:
    await seed_catalog(db)
    return await import_demo_lessons(db)


def test_content_has_ten_words_and_seven_new_exercises_per_lesson() -> None:
    content = load_demo_content()
    assert len(content.lessons) == 6
    for slug, lesson in content.lessons.items():
        assert len(lesson.vocabulary) == 10, slug
        assert len({w.word for w in lesson.vocabulary}) == 10, slug
        assert len(lesson.practice) == 7, slug
        prompts = [item.prompt for item in lesson.practice]
        assert len(set(prompts)) == len(prompts), slug


async def test_import_adds_words_and_exercises_once_and_refuses_changes(
    db_session: AsyncSession,
) -> None:
    first = await _prepare(db_session)
    assert first == {
        "words_added": 60,
        "words_existing": 0,
        "practice_added": 42,
        "practice_existing": 0,
    }
    again = await import_demo_lessons(db_session)
    assert again["words_added"] == 0 and again["practice_added"] == 0
    assert again["words_existing"] == 60 and again["practice_existing"] == 42

    lessons = (await db_session.scalars(select(Lesson).where(Lesson.slug.in_(_slugs())))).all()
    for lesson in lessons:
        positions = sorted(
            await db_session.scalars(
                select(Exercise.position).where(Exercise.lesson_id == lesson.id)
            )
        )
        assert positions == list(range(1, 11)), lesson.slug

    row = await db_session.scalar(select(Exercise).where(Exercise.slug == f"{LESSON}-extra-1"))
    assert row is not None
    row.prompt = "edited"
    await db_session.commit()
    with pytest.raises(ValueError, match="refusing"):
        await import_demo_lessons(db_session)


def _slugs() -> list[str]:
    return list(load_demo_content().lessons)


async def test_every_accepted_answer_is_graded_correct(db_session: AsyncSession) -> None:
    await _prepare(db_session)
    rows = (
        await db_session.scalars(
            select(Exercise).where(Exercise.slug.like("%-extra-%"), Exercise.type == "text")
        )
    ).all()
    assert len(rows) == 36
    for row in rows:
        for answer in row.accepted_answers or []:
            assert grade_objective(row, answer.upper() + "."), row.slug
        assert not grade_objective(row, "definitely wrong"), row.slug


async def test_finishing_a_demo_lesson_fills_the_dictionary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _prepare(db_session)
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "demo@example.com", "password": "correct-horse-battery", "displayName": "D"},
    )
    auth = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    lesson = (await client.get(f"/api/v1/lessons/{LESSON}")).json()
    assert len(lesson["exercises"]) == 10
    assert all(e["instruction"]["en"] for e in lesson["exercises"])
    rows = {
        r.slug: r
        for r in (
            await db_session.scalars(select(Exercise).where(Exercise.slug.like(f"{LESSON}-%")))
        ).all()
    }
    result = {}
    for exercise in lesson["exercises"]:
        row = rows[exercise["slug"]]
        payload = {"exerciseId": exercise["id"], "answer": "x"}
        if row.type == "single_choice":
            payload["answer"] = row.correct_option_id
        elif row.type == "text":
            payload["answer"] = row.accepted_answers[0]
        else:
            payload.update(answer="Hello, my name is Ann.", selfAssessment="correct")
        reply = await client.post(f"/api/v1/lessons/{LESSON}/submit", json=payload, headers=auth)
        assert reply.status_code == 200, reply.text
        result = reply.json()
    assert result["lesson"]["completed"] is True
    words = (await client.get("/api/v1/vocabulary", headers=auth)).json()
    assert len(words) == 10
    assert {w["lessonSlug"] for w in words} == {LESSON}
    assert {w["source"] for w in words} == {"lesson"}
    assert await db_session.scalar(select(func.count()).select_from(VocabularyItem)) == 10
    assert await db_session.scalar(select(func.count()).select_from(CourseVocabularyItem)) == 60
