"""Lesson practice supplement: 10–15 varied exercises per lesson, clear instructions, XP."""

import json

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import content_sha, import_curriculum, load_curriculum
from app.db.models import Exercise, VocabularyItem
from app.db.practice import (
    CONTENT,
    PracticeSupplement,
    exercise_rows,
    import_practice,
    import_vocabulary_practice,
    load_supplement,
)
from app.modules.exercises.instructions import instruction_kind

LESSON = "fleng-a1-routine-questions"


async def _publish(db: AsyncSession) -> None:
    content = load_curriculum()
    await import_curriculum(db, content, apply=True, owner_authorized_sha=content_sha(content))
    await import_practice(db, content)


async def _learner(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "p@example.com", "password": "correct-horse-battery", "displayName": "P"},
    )
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def test_every_lesson_gets_four_new_formats_within_ten_to_fifteen() -> None:
    content, supplement = load_curriculum(), load_supplement()
    rows = exercise_rows(content, supplement)
    for course in content.courses:
        for lesson in course.lessons:
            extra = [r for r in rows if r["slug"].startswith(lesson.slug + "-extra-")]
            total = len(lesson.exercises) + len(extra)
            assert len(extra) == 4 and 10 <= total <= 15, lesson.slug
            assert [r["position"] for r in extra] == list(
                range(len(lesson.exercises) + 1, total + 1)
            )
            # No repeated prompts within a lesson.
            prompts = [e.prompt for e in lesson.exercises] + [r["prompt"] for r in extra]
            assert len(set(prompts)) == len(prompts), lesson.slug


def test_translation_items_use_the_lessons_own_vocabulary() -> None:
    content, supplement = load_curriculum(), load_supplement()
    for course in content.courses:
        for lesson in course.lessons:
            item = supplement.lessons[lesson.slug][2]
            words = {w.translation: w.word for w in lesson.vocabulary}
            uk = item.prompt.split("«", 1)[1].rstrip("»")
            assert words[uk] == item.accepted_answers[0], lesson.slug


@pytest.mark.parametrize(
    "broken",
    [
        {"kind": "fill_gap", "prompt": "No gap here", "accepted_answers": ["x"]},
        {
            "kind": "word_order",
            "prompt": "Put the words in order: a / b",
            "accepted_answers": ["a c"],
        },
        {"kind": "write", "prompt": "Write", "accepted_answers": ["x"]},
        {"kind": "translate", "prompt": "Say: «кіт»", "accepted_answers": ["cat"]},
    ],
)
def test_invalid_practice_is_rejected(broken: dict) -> None:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    first = next(iter(data["lessons"]))
    index = {"fill_gap": 0, "word_order": 1, "translate": 2, "write": 3}[broken["kind"]]
    data["lessons"][first][index] = {**broken, "explanation": "e"}
    with pytest.raises(ValidationError):
        PracticeSupplement.model_validate(data)


async def test_lesson_api_has_twelve_exercises_each_with_an_instruction(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _publish(db_session)
    body = (await client.get(f"/api/v1/lessons/{LESSON}")).json()
    exercises = body["exercises"]
    assert len(exercises) == 12
    assert [e["position"] for e in exercises] == list(range(1, 13))
    assert {e["type"] for e in exercises} == {"single_choice", "text", "self_check"}
    for exercise in exercises:
        assert exercise["instruction"]["en"] and exercise["instruction"]["uk"]
        for secret in ("acceptedAnswers", "modelAnswer", "correctOptionId", "explanation"):
            assert secret not in exercise
    word_order = next(e for e in exercises if e["slug"].endswith("-extra-2"))
    assert word_order["instruction"]["en"].startswith("Use all the given words")


async def test_new_formats_grade_award_xp_once_and_complete_the_lesson(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _publish(db_session)
    auth = await _learner(client)
    lesson = (await client.get(f"/api/v1/lessons/{LESSON}")).json()
    rows = {
        r.slug: r
        for r in (
            await db_session.scalars(select(Exercise).where(Exercise.slug.like(f"{LESSON}-%")))
        ).all()
    }

    async def submit(exercise: dict, answer: str, assessment: str | None = None):
        payload = {"exerciseId": exercise["id"], "answer": answer}
        if assessment:
            payload["selfAssessment"] = assessment
        response = await client.post(f"/api/v1/lessons/{LESSON}/submit", json=payload, headers=auth)
        assert response.status_code == 200, response.text
        return response.json()

    gap = next(e for e in lesson["exercises"] if e["slug"].endswith("-extra-1"))
    wrong = await submit(gap, "do")
    assert wrong["isCorrect"] is False and wrong["xpAwarded"] == 0
    assert wrong["acceptedAnswers"] == ["does"]
    right = await submit(gap, "  Does ")
    assert right["isCorrect"] is True and right["xpAwarded"] == 1

    total_xp = 1
    for exercise in lesson["exercises"]:
        if exercise["id"] == gap["id"]:
            continue
        row = rows[exercise["slug"]]
        if row.type == "single_choice":
            result = await submit(exercise, row.correct_option_id)
        elif row.type == "text":
            result = await submit(exercise, row.accepted_answers[-1] + ".")
        else:
            result = await submit(exercise, "I usually walk to work.", "correct")
            assert result["modelAnswer"]
        assert result["isCorrect"] is True, exercise["slug"]
        total_xp += result["xpAwarded"]
    assert total_xp == 12
    assert result["lesson"]["completed"] is True
    assert result["lesson"]["exercisesCompleted"] == 12
    # Completion collected the lesson's ten words, once.
    assert await db_session.scalar(select(func.count()).select_from(VocabularyItem)) == 10
    again = await submit(gap, "does")
    assert again["xpAwarded"] == 0
    me = (await client.get("/api/v1/users/me", headers=auth)).json()
    assert me["xp"] == 12

    await import_vocabulary_practice(db_session, load_curriculum())
    words = await client.get("/api/v1/vocabulary", headers=auth)
    assert words.status_code == 200 and len(words.json()) == 20
    assert {w["word"] for w in words.json()} >= {"usually", "once a week"}
    progress = await client.get(f"/api/v1/lessons/{LESSON}/progress", headers=auth)
    assert progress.status_code == 200
    assert progress.json()["completed"] is True
    assert progress.json()["exercisesCompleted"] == 12


async def test_practice_import_is_additive_and_refuses_changes(db_session: AsyncSession) -> None:
    content = load_curriculum()
    await import_curriculum(
        db_session, content, apply=True, owner_authorized_sha=content_sha(content)
    )
    first = await import_practice(db_session, content)
    assert first == {"added": 200, "existing": 0}
    assert await import_practice(db_session, content) == {"added": 0, "existing": 200}
    row = await db_session.scalar(select(Exercise).where(Exercise.slug == f"{LESSON}-extra-1"))
    assert row is not None
    row.prompt = "edited"
    await db_session.commit()
    with pytest.raises(ValueError, match="refusing overwrite"):
        await import_practice(db_session, content)


def test_instruction_kinds_cover_every_format() -> None:
    def kind(type_: str, prompt: str, tiles: dict | None = None) -> str:
        return instruction_kind(Exercise(type=type_, prompt=prompt, letter_tiles=tiles))

    assert kind("single_choice", "I ___ happy.") == "choose_gap"
    assert kind("single_choice", "Which word is a colour?") == "choose_question"
    assert kind("single_choice", "Pick the plural form") == "choose"
    assert kind("text", "c_t", {"pattern": "c_t", "letters": ["a"]}) == "letters"
    assert kind("text", "Put the words in order to make a sentence: a / b") == "word_order"
    assert kind("text", "Translate into English: «кіт»") == "translate"
    assert kind("text", "She ___ tea.") == "type_gap"
    assert kind("text", "What is 2 + 2?") == "type"
    assert kind("self_check", "Write about you.") == "self_check"
