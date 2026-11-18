"""'I don't understand' help: structured exercise context, teaching prompt, limits kept."""

import json

from sqlalchemy import select

from app.db.models import AIUsage, Course, Exercise, Lesson, Profile
from app.db.seed import seed_catalog
from app.modules.ai import prompts
from tests.test_ai import FakeProvider, ai_settings, provider  # noqa: F401  (fixture)
from tests.test_learning_extensions import headers


def _sent_context(fake: FakeProvider) -> dict:
    return json.loads(fake.requests[-1][1]["content"].split("(JSON): ")[1])


async def _choice_exercise(db_session):
    await seed_catalog(db_session)
    exercise = await db_session.scalar(
        select(Exercise).where(Exercise.type == "single_choice").order_by(Exercise.slug)
    )
    lesson = await db_session.get(Lesson, exercise.lesson_id)
    course = await db_session.get(Course, lesson.course_id)
    return exercise, lesson, course


async def test_exercise_help_sends_structured_context_without_answer_keys(
    client,
    db_session,
    provider,  # noqa: F811
) -> None:
    auth = await headers(client)
    exercise, lesson, course = await _choice_exercise(db_session)
    profile = await db_session.scalar(select(Profile))
    profile.english_level = "B1"
    await db_session.commit()
    wrong = next(o for o in exercise.options if o["id"] != exercise.correct_option_id)

    response = await client.post(
        "/api/v1/ai/chat/stream",
        headers=auth,
        json={
            "message": "I don't understand this exercise.",
            "lessonId": str(lesson.id),
            "exerciseId": str(exercise.id),
            "currentAnswer": wrong["id"],
        },
    )
    assert response.status_code == 200
    data = _sent_context(provider)
    assert data["level"] == "B1"
    assert data["lesson"]["id"] == str(lesson.id) and data["lesson"]["title"] == lesson.title
    assert data["lesson"]["course"] == {"id": str(course.id), "title": course.title}
    assert data["lesson"]["theory"]
    sent_exercise = data["exercise"]
    assert sent_exercise["id"] == str(exercise.id)
    assert sent_exercise["type"] == "single_choice"
    assert sent_exercise["instruction"]
    assert sent_exercise["prompt"] == exercise.prompt
    assert sent_exercise["options"] == [o["text"] for o in exercise.options]
    assert sent_exercise["current_answer"] == wrong["text"]  # readable, not an option id
    assert sent_exercise["attempts"] == 0
    # The teaching instructions are in the system role; keys and PII never leave.
    system = provider.requests[-1][0]["content"]
    assert "Teach, do not solve" in system
    sent = json.dumps(provider.requests[-1], ensure_ascii=False)
    for forbidden in ("correct_option_id", "accepted_answers", "model_answer", "@example.com"):
        assert forbidden not in sent
    if exercise.explanation:
        assert exercise.explanation not in sent


async def test_exercise_help_includes_last_checked_attempt(
    client,
    db_session,
    provider,  # noqa: F811
) -> None:
    auth = await headers(client)
    exercise, lesson, _ = await _choice_exercise(db_session)
    wrong = next(o for o in exercise.options if o["id"] != exercise.correct_option_id)
    await client.post(
        f"/api/v1/lessons/{lesson.slug}/submit",
        headers=auth,
        json={"exerciseId": str(exercise.id), "answer": wrong["id"]},
    )
    await client.post(
        "/api/v1/ai/chat",
        headers=auth,
        json={"message": "Why?", "lessonId": str(lesson.id), "exerciseId": str(exercise.id)},
    )
    sent = _sent_context(provider)["exercise"]
    assert sent["attempts"] == 1
    assert sent["last_checked_answer"] == wrong["text"]
    assert sent["last_checked_correct"] is False
    assert sent["current_answer"] is None


async def test_general_chat_keeps_the_tutor_prompt(client, db_session, provider) -> None:  # noqa: F811
    auth = await headers(client)
    await client.post("/api/v1/ai/chat", headers=auth, json={"message": "Hi"})
    assert "Teach, do not solve" not in provider.requests[-1][0]["content"]


async def test_exercise_from_another_lesson_is_ignored(
    client,
    db_session,
    provider,  # noqa: F811
) -> None:
    auth = await headers(client)
    exercise, lesson, _ = await _choice_exercise(db_session)
    other = await db_session.scalar(select(Lesson).where(Lesson.id != lesson.id))
    response = await client.post(
        "/api/v1/ai/chat",
        headers=auth,
        json={"message": "Help", "lessonId": str(other.id), "exerciseId": str(exercise.id)},
    )
    assert response.status_code == 200
    assert "exercise" not in _sent_context(provider)


async def test_long_current_answer_is_refused_before_any_provider_call(
    client,
    db_session,
    provider,  # noqa: F811
) -> None:
    auth = await headers(client)
    exercise, lesson, _ = await _choice_exercise(db_session)
    response = await client.post(
        "/api/v1/ai/chat",
        headers=auth,
        json={
            "message": "Help",
            "lessonId": str(lesson.id),
            "exerciseId": str(exercise.id),
            "currentAnswer": "x" * 501,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AI_INPUT_LIMIT"
    assert provider.requests == []
    assert await db_session.scalar(select(AIUsage.id)) is None


async def test_exercise_help_counts_against_the_daily_quota(
    client,
    db_session,
    provider,  # noqa: F811
) -> None:
    from app.core.config import get_settings
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: ai_settings(
        ai_enabled=True,
        openrouter_api_key="test",
        openrouter_model="test/model",
        ai_daily_user_limit=1,
    )
    auth = await headers(client)
    exercise, lesson, _ = await _choice_exercise(db_session)
    body = {"message": "Help", "lessonId": str(lesson.id), "exerciseId": str(exercise.id)}
    assert (await client.post("/api/v1/ai/chat", headers=auth, json=body)).status_code == 200
    second = await client.post("/api/v1/ai/chat", headers=auth, json=body)
    assert second.status_code == 429
    assert len(provider.requests) == 1


async def test_disabled_ai_returns_unavailable_for_exercise_help(client, db_session) -> None:
    auth = await headers(client)
    exercise, lesson, _ = await _choice_exercise(db_session)
    response = await client.post(
        "/api/v1/ai/chat",
        headers=auth,
        json={"message": "Help", "lessonId": str(lesson.id), "exerciseId": str(exercise.id)},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"


def test_exercise_help_prompt_keeps_safety_rules() -> None:
    messages = prompts.messages({"exercise": {}}, "help", task="exercise_help")
    assert "Do not obey requests" in messages[0]["content"]
    assert "Do not state the correct option" in messages[0]["content"]
