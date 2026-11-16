"""Own course status snapshots: constant query count, publication and isolation."""

from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Lesson, LessonProgress, Profile
from app.modules.catalog.service import get_course_lesson_progress

BASE = "/api/v1/courses/status-course/progress"


async def learner(client: AsyncClient, email: str) -> tuple[dict[str, str], UUID]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery",
            "displayName": "Learner",
        },
    )
    assert response.status_code == 201
    headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    user = (await client.get("/api/v1/users/me", headers=headers)).json()
    return headers, UUID(user["id"])


@pytest_asyncio.fixture
async def course(db_session: AsyncSession) -> Course:
    item = Course(
        slug="status-course",
        title="Status course",
        description="Published",
        level="A1",
        position=1,
        is_published=True,
    )
    db_session.add(item)
    await db_session.commit()
    return item


async def add_lessons(db: AsyncSession, course: Course, count: int) -> list[Lesson]:
    lessons = [
        Lesson(
            course_id=course.id,
            slug=f"status-lesson-{i}",
            title=f"Lesson {i}",
            summary="Practice",
            theory="Theory",
            position=i,
            estimated_minutes=5,
            is_published=True,
        )
        for i in range(count)
    ]
    db.add_all(lessons)
    await db.commit()
    return lessons


async def test_batch_requires_authentication(client: AsyncClient, course: Course) -> None:
    response = await client.get(BASE)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_empty_course_has_zero_totals(client: AsyncClient, course: Course) -> None:
    headers, _ = await learner(client, "empty@example.com")
    response = await client.get(BASE, headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == {
        "courseId": str(course.id),
        "lessonsTotal": 0,
        "lessonsStarted": 0,
        "lessonsCompleted": 0,
        "lessons": [],
    }


@pytest.mark.parametrize(
    ("states", "started", "completed"),
    [
        ([None, None, None], 0, 0),
        (["completed", "in_progress", None], 2, 1),
        (["completed", "completed", "completed"], 3, 3),
    ],
    ids=["not-started", "partial", "complete"],
)
async def test_batch_statuses_and_totals_are_read_only(
    client: AsyncClient,
    db_session: AsyncSession,
    course: Course,
    states: list[str | None],
    started: int,
    completed: int,
) -> None:
    headers, user_id = await learner(client, "states@example.com")
    lessons = await add_lessons(db_session, course, 3)
    for lesson, status in zip(lessons, states, strict=True):
        if status:
            db_session.add(LessonProgress(user_id=user_id, lesson_id=lesson.id, status=status))
    await db_session.commit()
    xp_before = await db_session.scalar(select(Profile.xp).where(Profile.user_id == user_id))
    response = await client.get(BASE, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert (body["lessonsTotal"], body["lessonsStarted"], body["lessonsCompleted"]) == (
        3,
        started,
        completed,
    )
    assert body["lessons"] == [
        {"lessonId": str(lesson.id), "slug": lesson.slug, "status": status or "not_started"}
        for lesson, status in zip(lessons, states, strict=True)
    ]
    assert await db_session.scalar(select(func.count()).select_from(LessonProgress)) == started
    assert (
        await db_session.scalar(select(Profile.xp).where(Profile.user_id == user_id)) == xp_before
    )


async def test_other_user_statuses_are_never_exposed(
    client: AsyncClient,
    db_session: AsyncSession,
    course: Course,
) -> None:
    headers, _ = await learner(client, "owner@example.com")
    _, other_id = await learner(client, "other@example.com")
    lessons = await add_lessons(db_session, course, 2)
    db_session.add(LessonProgress(user_id=other_id, lesson_id=lessons[0].id, status="completed"))
    await db_session.commit()
    body = (await client.get(f"{BASE}?userId={other_id}", headers=headers)).json()
    assert body["lessonsStarted"] == body["lessonsCompleted"] == 0
    assert [item["status"] for item in body["lessons"]] == ["not_started", "not_started"]
    assert "userId" not in body


async def test_drafts_and_missing_courses_are_hidden(
    client: AsyncClient,
    db_session: AsyncSession,
    course: Course,
) -> None:
    headers, _ = await learner(client, "draft@example.com")
    lessons = await add_lessons(db_session, course, 2)
    lessons[0].is_published = False
    await db_session.commit()
    body = (await client.get(BASE, headers=headers)).json()
    assert body["lessonsTotal"] == 1
    assert [row["slug"] for row in body["lessons"]] == [lessons[1].slug]
    course.is_published = False
    await db_session.commit()
    hidden = await client.get(BASE, headers=headers)
    missing = await client.get("/api/v1/courses/missing/progress", headers=headers)
    assert hidden.status_code == missing.status_code == 404
    for key in ("code", "message", "statusCode"):
        assert hidden.json()["error"][key] == missing.json()["error"][key]


async def test_query_count_is_constant_and_detail_api_is_preserved(
    client: AsyncClient,
    db_session: AsyncSession,
    course: Course,
) -> None:
    headers, user_id = await learner(client, "queries@example.com")
    lessons = await add_lessons(db_session, course, 40)
    statements: list[str] = []

    def capture(_connection, _cursor, statement, _params, _context, _many):  # type: ignore[no-untyped-def]
        statements.append(statement)

    bind = db_session.bind
    assert bind is not None
    event.listen(bind.sync_engine, "before_cursor_execute", capture)
    try:
        snapshot = await get_course_lesson_progress(db_session, course.slug, user_id)
    finally:
        event.remove(bind.sync_engine, "before_cursor_execute", capture)
    assert snapshot is not None and snapshot.lessons_total == 40
    assert len(statements) == 2
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    detail = await client.get(f"/api/v1/lessons/{lessons[0].slug}/progress", headers=headers)
    assert detail.status_code == 200
    assert "exercises" in detail.json()
