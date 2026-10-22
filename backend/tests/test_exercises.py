"""Exercise grading, submissions, lesson completion, XP and progress tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Exercise, Lesson
from app.db.seed import seed_catalog

REGISTER = "/api/v1/auth/register"
LESSONS = "/api/v1/lessons"
PROGRESS = "/api/v1/progress/me"
ME = "/api/v1/users/me"
PASSWORD = "correct-horse-battery"


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_catalog(db_session)
    return db_session


async def _register(client: AsyncClient, email: str = "learner@example.com") -> str:
    response = await client.post(
        REGISTER,
        json={"email": email, "password": PASSWORD, "displayName": "Learner"},
    )
    return response.json()["accessToken"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _lesson(client: AsyncClient, slug: str) -> dict:
    response = await client.get(f"{LESSONS}/{slug}")
    assert response.status_code == 200, response.text
    return response.json()


async def _exercise_id(client: AsyncClient, lesson_slug: str, exercise_slug: str) -> str:
    body = await _lesson(client, lesson_slug)
    return next(e["id"] for e in body["exercises"] if e["slug"] == exercise_slug)


async def _submit(
    client: AsyncClient,
    token: str,
    lesson_slug: str,
    exercise_id: str,
    *,
    answer: str | None = None,
    self_assessment: str | None = None,
):
    payload: dict = {"exerciseId": exercise_id}
    if answer is not None:
        payload["answer"] = answer
    if self_assessment is not None:
        payload["selfAssessment"] = self_assessment
    return await client.post(
        f"{LESSONS}/{lesson_slug}/submit", json=payload, headers=_auth(token)
    )


async def test_lesson_progress_restores_own_latest_answer(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    learner = await _register(client)
    other = await _register(client, "another-learner@example.com")
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q1"
    )
    response = await _submit(
        client, learner, "greetings-and-introductions", exercise_id, answer="b"
    )
    assert response.status_code == 200
    url = f"{LESSONS}/greetings-and-introductions/progress"
    own = await client.get(url, headers=_auth(learner))
    another = await client.get(url, headers=_auth(other))
    saved = next(item for item in own.json()["exercises"] if item["exerciseId"] == exercise_id)
    assert saved["answer"] == "b"
    assert all(item["answer"] is None for item in another.json()["exercises"])


async def _complete_greetings(client: AsyncClient, token: str) -> None:
    """Complete every exercise in the greetings lesson (3 exercises)."""
    q1 = await _exercise_id(client, "greetings-and-introductions", "greetings-and-introductions-q1")
    q2 = await _exercise_id(client, "greetings-and-introductions", "greetings-and-introductions-q2")
    q3 = await _exercise_id(client, "greetings-and-introductions", "greetings-and-introductions-q3")
    first = await _submit(client, token, "greetings-and-introductions", q1, answer="a")
    assert first.status_code == 200
    assert (
        await _submit(
            client, token, "greetings-and-introductions", q2, answer="nice to meet you too"
        )
    ).status_code == 200
    assert (
        await _submit(
            client,
            token,
            "greetings-and-introductions",
            q3,
            answer="Good morning",
            self_assessment="correct",
        )
    ).status_code == 200


# ── Serialization safety ────────────────────────────────────────────────────


async def test_public_lesson_exercises_hide_answer_keys(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    body = await _lesson(client, "greetings-and-introductions")
    assert len(body["exercises"]) == 3
    for exercise in body["exercises"]:
        assert "correctOptionId" not in exercise
        assert "acceptedAnswers" not in exercise
        assert "modelAnswer" not in exercise
        assert "explanation" not in exercise
        if exercise["type"] == "single_choice":
            assert isinstance(exercise["options"], list) and exercise["options"]
        else:
            assert exercise.get("options") is None


# ── Authentication ──────────────────────────────────────────────────────────


async def test_submit_requires_authentication(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q1"
    )
    response = await client.post(
        f"{LESSONS}/greetings-and-introductions/submit",
        json={"exerciseId": exercise_id, "answer": "a"},
    )
    assert response.status_code == 401


async def test_start_requires_authentication(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    response = await client.post(f"{LESSONS}/greetings-and-introductions/start")
    assert response.status_code == 401


async def test_course_progress_counts_started_before_completion(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    headers = _auth(token)
    initial = (await client.get(PROGRESS, headers=headers)).json()
    course = next(c for c in initial["courses"] if c["slug"] == "english-foundations")
    assert course["lessonsStarted"] == 0
    assert course["lessonsCompleted"] == 0

    started = await client.post(
        f"{LESSONS}/greetings-and-introductions/start", headers=headers
    )
    assert started.status_code == 200
    updated = (await client.get(PROGRESS, headers=headers)).json()
    course = next(c for c in updated["courses"] if c["slug"] == "english-foundations")
    assert course["lessonsStarted"] == 1
    assert course["lessonsCompleted"] == 0


# ── single_choice ───────────────────────────────────────────────────────────


async def test_single_choice_correct(client: AsyncClient, seeded: AsyncSession) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q1"
    )
    response = await _submit(client, token, "greetings-and-introductions", exercise_id, answer="a")
    assert response.status_code == 200
    body = response.json()
    assert body["isCorrect"] is True
    assert body["completed"] is True
    assert body["points"] == 1
    assert body["xpAwarded"] == 1
    assert body["correctOptionId"] == "a"
    assert body["feedback"]
    assert body["lesson"]["exercisesCompleted"] == 1
    assert body["lesson"]["xpEarned"] == 1


async def test_single_choice_incorrect(client: AsyncClient, seeded: AsyncSession) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q1"
    )
    response = await _submit(client, token, "greetings-and-introductions", exercise_id, answer="b")
    assert response.status_code == 200
    body = response.json()
    assert body["isCorrect"] is False
    assert body["completed"] is False
    assert body["xpAwarded"] == 0
    assert body["correctOptionId"] == "a"


async def test_single_choice_invalid_option_rejected(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q1"
    )
    response = await _submit(client, token, "greetings-and-introductions", exercise_id, answer="z")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ANSWER"


# ── text ────────────────────────────────────────────────────────────────────


async def test_text_answer_is_normalised(client: AsyncClient, seeded: AsyncSession) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(client, "numbers-and-days", "numbers-and-days-q2")
    response = await _submit(
        client, token, "numbers-and-days", exercise_id, answer="  TWELVE  "
    )
    assert response.status_code == 200
    body = response.json()
    assert body["isCorrect"] is True
    assert body["xpAwarded"] == 1
    assert "twelve" in body["acceptedAnswers"]


async def test_text_answer_incorrect(client: AsyncClient, seeded: AsyncSession) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(client, "numbers-and-days", "numbers-and-days-q2")
    response = await _submit(client, token, "numbers-and-days", exercise_id, answer="thirteen")
    assert response.status_code == 200
    assert response.json()["isCorrect"] is False
    assert response.json()["completed"] is False


async def test_text_blank_answer_rejected(client: AsyncClient, seeded: AsyncSession) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(client, "numbers-and-days", "numbers-and-days-q2")
    response = await _submit(client, token, "numbers-and-days", exercise_id, answer="   ")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ANSWER"


# ── self_check ──────────────────────────────────────────────────────────────


async def test_self_check_requires_assessment(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q3"
    )
    response = await _submit(
        client, token, "greetings-and-introductions", exercise_id, answer="Good morning"
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ANSWER"


async def test_self_check_completes_and_reveals_model_answer(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    exercise_id = await _exercise_id(
        client, "greetings-and-introductions", "greetings-and-introductions-q3"
    )
    response = await _submit(
        client,
        token,
        "greetings-and-introductions",
        exercise_id,
        answer="Good morning",
        self_assessment="correct",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "self_check"
    assert body["isCorrect"] is True
    assert body["completed"] is True
    assert body["xpAwarded"] == 1
    assert body["modelAnswer"]


# ── Relationship / ownership validation ─────────────────────────────────────


async def test_exercise_from_another_lesson_is_rejected(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    # An exercise that belongs to "the-verb-to-be", submitted against greetings.
    other = await _exercise_id(client, "the-verb-to-be", "the-verb-to-be-q1")
    response = await _submit(client, token, "greetings-and-introductions", other, answer="b")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_unknown_exercise_is_rejected(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    response = await _submit(
        client, token, "greetings-and-introductions", str(uuid.uuid4()), answer="a"
    )
    assert response.status_code == 404


# ── Completion rules ────────────────────────────────────────────────────────


async def test_start_does_not_complete_a_lesson(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    response = await client.post(
        f"{LESSONS}/greetings-and-introductions/start", headers=_auth(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["completed"] is False
    assert body["exercisesCompleted"] == 0
    assert body["exercisesTotal"] == 3


async def test_lesson_completes_only_when_all_exercises_are_done(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    await _complete_greetings(client, token)

    response = await client.get(PROGRESS, headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["lessonsStarted"] == 1
    assert body["lessonsCompleted"] == 1
    assert body["exercisesCompleted"] == 3
    assert body["xp"] == 3
    assert body["studyMinutes"] == 10  # greetings lesson estimated_minutes
    assert body["lastActivityAt"] is not None

    course = next(c for c in body["courses"] if c["slug"] == "english-foundations")
    assert course["lessonsTotal"] == 3
    assert course["lessonsCompleted"] == 1


async def test_lesson_without_exercises_is_never_completed(
    client: AsyncClient, seeded: AsyncSession, db_session: AsyncSession
) -> None:
    course = Course(
        slug="empty-course",
        title="Empty",
        description="No exercises.",
        level="A1",
        position=9,
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()
    db_session.add(
        Lesson(
            course_id=course.id,
            slug="empty-lesson",
            title="Empty lesson",
            summary="No exercises.",
            theory="Nothing here.",
            position=1,
            estimated_minutes=1,
            is_published=True,
        )
    )
    await db_session.commit()

    token = await _register(client)
    response = await client.post(f"{LESSONS}/empty-lesson/start", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["completed"] is False
    assert response.json()["status"] == "in_progress"


# ── Idempotency ─────────────────────────────────────────────────────────────


async def test_completion_and_xp_are_idempotent(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    await _complete_greetings(client, token)

    me_before = (await client.get(ME, headers=_auth(token))).json()
    progress_before = (await client.get(PROGRESS, headers=_auth(token))).json()

    # Re-submit a correct answer: no new XP.
    q1 = await _exercise_id(client, "greetings-and-introductions", "greetings-and-introductions-q1")
    repeat = await _submit(client, token, "greetings-and-introductions", q1, answer="a")
    assert repeat.status_code == 200
    assert repeat.json()["xpAwarded"] == 0

    me_after = (await client.get(ME, headers=_auth(token))).json()
    progress_after = (await client.get(PROGRESS, headers=_auth(token))).json()
    assert me_after["xp"] == me_before["xp"] == 3
    assert progress_after["lessonsCompleted"] == progress_before["lessonsCompleted"] == 1
    assert progress_after["exercisesCompleted"] == 3


async def test_progress_is_isolated_between_users(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    first = await _register(client, email="a@example.com")
    second = await _register(client, email="b@example.com")
    await _complete_greetings(client, first)

    first_progress = (await client.get(PROGRESS, headers=_auth(first))).json()
    second_progress = (await client.get(PROGRESS, headers=_auth(second))).json()

    assert first_progress["lessonsCompleted"] == 1
    assert second_progress["lessonsCompleted"] == 0
    assert second_progress["exercisesCompleted"] == 0
    assert second_progress["xp"] == 0


# ── Progress response shape / backward compatibility ────────────────────────


async def test_progress_response_is_backward_compatible_and_extended(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    token = await _register(client)
    body = (await client.get(PROGRESS, headers=_auth(token))).json()

    # Original fields survive.
    for field in ("userId", "lessonsStarted", "lessonsCompleted", "studyMinutes",
                  "lastActivityAt", "updatedAt"):
        assert field in body
    # New fields.
    assert body["xp"] == 0
    assert body["exercisesCompleted"] == 0
    assert isinstance(body["courses"], list)
    assert len(body["courses"]) == 2
    assert {"courseId", "slug", "title", "level", "lessonsTotal", "lessonsCompleted"} <= set(
        body["courses"][0]
    )


async def test_lesson_progress_endpoint_requires_auth_and_reports_state(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    assert (await client.get(f"{LESSONS}/greetings-and-introductions/progress")).status_code == 401

    token = await _register(client)
    empty = await client.get(
        f"{LESSONS}/greetings-and-introductions/progress", headers=_auth(token)
    )
    assert empty.status_code == 200
    assert empty.json()["status"] == "in_progress"
    assert empty.json()["startedAt"] is None

    await client.post(f"{LESSONS}/greetings-and-introductions/start", headers=_auth(token))
    started = await client.get(
        f"{LESSONS}/greetings-and-introductions/progress", headers=_auth(token)
    )
    assert started.json()["startedAt"] is not None


# ── Seed idempotency ────────────────────────────────────────────────────────


async def test_seed_exercises_are_idempotent(
    client: AsyncClient, seeded: AsyncSession
) -> None:
    async def counts() -> tuple[int, int, int]:
        courses = await seeded.scalar(select(func.count()).select_from(Course))
        lessons = await seeded.scalar(select(func.count()).select_from(Lesson))
        exercises = await seeded.scalar(select(func.count()).select_from(Exercise))
        return courses or 0, lessons or 0, exercises or 0

    before = await counts()
    await seed_catalog(seeded)
    after = await counts()

    assert before == after == (2, 6, 18)
