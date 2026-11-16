"""Read-only personal analytics from persisted lesson state and activity days."""

from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import (
    Course,
    Exercise,
    ExerciseSubmission,
    LearningActivity,
    Lesson,
    LessonProgress,
    Profile,
    Progress,
)

URL = "/api/v1/progress/me"


async def register(client: AsyncClient, email: str):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "analytics-password", "displayName": "Learner"},
    )
    assert response.status_code == 201
    body = response.json()
    return {"Authorization": "Bearer " + body["accessToken"]}, UUID(body["user"]["id"])


async def course(db: AsyncSession, slug: str, count: int, published: bool = True):
    item = Course(slug=slug, title=slug, description="Test", level="A1", is_published=published)
    db.add(item)
    await db.flush()
    lessons = [
        Lesson(
            course_id=item.id,
            slug=f"{slug}-{i}",
            title="Lesson",
            summary="Summary",
            theory="Theory",
            is_published=True,
        )
        for i in range(count)
    ]
    db.add_all(lessons)
    await db.flush()
    return lessons


async def test_new_user_has_no_invented_activity(client: AsyncClient, db_session: AsyncSession):
    headers, _ = await register(client, "new@example.com")
    await course(db_session, "empty", 0)
    await course(db_session, "untouched", 2)
    await db_session.commit()
    body = (await client.get(URL, headers=headers)).json()
    assert (
        body["lessonsStarted"]
        == body["lessonsCompleted"]
        == body["activeCourses"]
        == body["xp"]
        == 0
    )
    assert all(c["completionPercent"] == 0 for c in body["courses"])
    assert body["streak"] == {
        "current": 0,
        "longest": 0,
        "lastActivityDate": None,
        "timezone": get_settings().learning_timezone,
    }
    assert body["xpHistory"] == {
        "available": False,
        "reason": "XP_AWARD_HISTORY_NOT_RECORDED",
        "last7Days": None,
        "last30Days": None,
    }


async def test_real_lesson_counts_visibility_and_user_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    headers, user_id = await register(client, "first@example.com")
    other_headers, other_id = await register(client, "second@example.com")
    active = await course(db_session, "active", 3)
    finished = await course(db_session, "finished", 1)
    await course(db_session, "untouched", 1)
    await course(db_session, "empty", 0)
    hidden = await course(db_session, "hidden", 1, published=False)
    draft = await course(db_session, "draft-lesson", 1)
    draft[0].is_published = False
    for lesson in (active[0], finished[0], hidden[0], draft[0]):
        db_session.add(LessonProgress(user_id=user_id, lesson_id=lesson.id, status="completed"))
    db_session.add(LessonProgress(user_id=user_id, lesson_id=active[1].id, status="in_progress"))
    for lesson in active:
        db_session.add(LessonProgress(user_id=other_id, lesson_id=lesson.id, status="completed"))
    aggregate = await db_session.scalar(select(Progress).where(Progress.user_id == user_id))
    aggregate.lessons_started = aggregate.lessons_completed = 99
    profile = await db_session.scalar(select(Profile).where(Profile.user_id == user_id))
    profile.xp = 47
    today = datetime.now(ZoneInfo(get_settings().learning_timezone)).date()
    db_session.add(LearningActivity(user_id=other_id, day=today))
    await db_session.commit()
    body = (await client.get(URL + f"?userId={other_id}", headers=headers)).json()
    assert body["userId"] == str(user_id)
    assert body["lessonsStarted"] == 5 and body["lessonsCompleted"] == 4
    assert body["activeCourses"] == 1 and body["xp"] == 47
    courses = {c["slug"]: c for c in body["courses"]}
    assert "hidden" not in courses
    assert courses["active"]["lessonsTotal"] == 3
    assert courses["active"]["lessonsStarted"] == 2
    assert courses["active"]["lessonsCompleted"] == 1
    assert courses["active"]["completionPercent"] == 33.33
    assert courses["finished"]["completionPercent"] == 100
    assert (
        courses["empty"]["completionPercent"] == courses["draft-lesson"]["completionPercent"] == 0
    )
    assert body["streak"]["current"] == body["streak"]["longest"] == 0
    other = (await client.get(URL, headers=other_headers)).json()
    assert other["lessonsCompleted"] == 3 and other["activeCourses"] == 0
    assert other["xp"] == 0 and other["streak"]["current"] == 1
    await db_session.refresh(aggregate)
    assert aggregate.lessons_completed == aggregate.lessons_started == 99
    assert (await client.get(URL)).status_code == 401
    assert (await client.get(URL, headers={"Authorization": "Bearer invalid"})).status_code == 401


@pytest.mark.parametrize("offset, current", [(0, 2), (1, 2), (2, 0)])
async def test_streak_reuses_existing_policy(
    client: AsyncClient, db_session: AsyncSession, offset: int, current: int
):
    headers, user_id = await register(client, "streak@example.com")
    today = datetime.now(ZoneInfo(get_settings().learning_timezone)).date()
    for days_ago in (offset, offset + 1, 10, 11, 12):
        db_session.add(LearningActivity(user_id=user_id, day=today - timedelta(days=days_ago)))
    await db_session.commit()
    body = (await client.get(URL, headers=headers)).json()
    assert body["streak"]["current"] == current
    assert body["streak"]["longest"] == 3
    assert body["streak"]["lastActivityDate"] == (today - timedelta(days=offset)).isoformat()
    existing = (await client.get("/api/v1/streaks/me", headers=headers)).json()
    assert body["streak"] == existing


async def test_missing_aggregate_and_profile_read_without_writes(
    client: AsyncClient, db_session: AsyncSession
):
    headers, user_id = await register(client, "legacy@example.com")
    lessons = await course(db_session, "legacy", 1)
    db_session.add(LessonProgress(user_id=user_id, lesson_id=lessons[0].id, status="completed"))
    await db_session.execute(delete(Progress).where(Progress.user_id == user_id))
    await db_session.execute(delete(Profile).where(Profile.user_id == user_id))
    await db_session.commit()
    body = (await client.get(URL, headers=headers)).json()
    assert body["lessonsStarted"] == body["lessonsCompleted"] == 1
    assert body["xp"] == body["studyMinutes"] == 0
    assert body["updatedAt"] is None and body["lastActivityAt"] is None
    assert await db_session.scalar(select(Progress).where(Progress.user_id == user_id)) is None
    assert await db_session.scalar(select(Profile).where(Profile.user_id == user_id)) is None


async def test_xp_history_not_inferred_from_mutable_submissions(
    client: AsyncClient, db_session: AsyncSession
):
    headers, user_id = await register(client, "history@example.com")
    lessons = await course(db_session, "history", 1)
    exercise = Exercise(
        lesson_id=lessons[0].id,
        slug="history-exercise",
        type="text",
        prompt="Test",
        accepted_answers=["ok"],
        points=999,
    )
    db_session.add(exercise)
    await db_session.flush()
    db_session.add(
        ExerciseSubmission(
            user_id=user_id,
            exercise_id=exercise.id,
            completed=True,
            xp_awarded=True,
            attempts=3,
            submitted_at=datetime.now(UTC),
        )
    )
    profile = await db_session.scalar(select(Profile).where(Profile.user_id == user_id))
    profile.xp = 17
    await db_session.commit()
    body = (await client.get(URL, headers=headers)).json()
    assert body["exercisesCompleted"] == 1 and body["xp"] == 17
    assert body["xpHistory"]["available"] is False
    assert body["xpHistory"]["last7Days"] is None and body["xpHistory"]["last30Days"] is None


async def test_query_count_does_not_grow_with_catalog(
    client: AsyncClient, db_session: AsyncSession
):
    headers, _ = await register(client, "queries@example.com")
    statements = []
    engine = db_session.get_bind()

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    try:
        assert (await client.get(URL, headers=headers)).status_code == 200
        initial = list(statements)
        for i in range(12):
            await course(db_session, f"course-{i}", 3)
        await db_session.commit()
        statements.clear()
        response = await client.get(URL, headers=headers)
        assert len(response.json()["courses"]) == 12
        assert len(statements) == len(initial) <= 7
        assert all(s.lstrip().upper().startswith("SELECT") for s in statements)
    finally:
        event.remove(engine, "before_cursor_execute", capture)
