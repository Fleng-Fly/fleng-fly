"""Catalog tests: published-only listing, ordering, detail, 404s and seeding."""

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Lesson
from app.db.seed import seed_catalog

COURSES = "/api/v1/courses"
LESSONS = "/api/v1/lessons"


@pytest_asyncio.fixture
async def catalog(db_session: AsyncSession) -> AsyncSession:
    """Seed the catalog into the test database (same session as the client)."""
    await seed_catalog(db_session)
    return db_session


def _course(**overrides) -> Course:
    values = {
        "slug": "draft-course",
        "title": "Draft course",
        "description": "Not published yet.",
        "level": "B2",
        "position": 0,
        "is_published": False,
    }
    values.update(overrides)
    return Course(**values)


def _lesson(course_id, **overrides) -> Lesson:
    values = {
        "course_id": course_id,
        "slug": "draft-lesson",
        "title": "Draft lesson",
        "summary": "Not published yet.",
        "theory": "Draft theory.",
        "position": 0,
        "estimated_minutes": 5,
        "is_published": False,
    }
    values.update(overrides)
    return Lesson(**values)


async def test_list_courses_is_public_and_ordered(
    client: AsyncClient, catalog: AsyncSession
) -> None:
    response = await client.get(COURSES)
    assert response.status_code == 200
    body = response.json()
    assert [course["slug"] for course in body] == [
        "english-foundations",
        "everyday-conversations",
    ]
    first = body[0]
    assert first["level"] == "A1"
    assert first["lessonCount"] == 3
    assert set(first) == {"id", "slug", "title", "description", "level", "lessonCount"}


async def test_list_courses_excludes_unpublished(
    client: AsyncClient, catalog: AsyncSession, db_session: AsyncSession
) -> None:
    db_session.add(_course())
    await db_session.commit()

    body = (await client.get(COURSES)).json()
    assert all(course["slug"] != "draft-course" for course in body)


async def test_course_detail_returns_published_lessons_ordered(
    client: AsyncClient, catalog: AsyncSession
) -> None:
    response = await client.get(f"{COURSES}/english-foundations")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "english-foundations"
    assert body["level"] == "A1"
    assert [lesson["slug"] for lesson in body["lessons"]] == [
        "greetings-and-introductions",
        "the-verb-to-be",
        "numbers-and-days",
    ]
    assert all("theory" not in lesson for lesson in body["lessons"])


async def test_course_detail_hides_unpublished_lessons(
    client: AsyncClient, catalog: AsyncSession, db_session: AsyncSession
) -> None:
    course = await db_session.scalar(
        select(Course).where(Course.slug == "english-foundations")
    )
    assert course is not None
    db_session.add(_lesson(course.id, position=99))
    await db_session.commit()

    body = (await client.get(f"{COURSES}/english-foundations")).json()
    assert all(lesson["slug"] != "draft-lesson" for lesson in body["lessons"])


async def test_lesson_detail_returns_theory_and_course_context(
    client: AsyncClient, catalog: AsyncSession
) -> None:
    response = await client.get(f"{LESSONS}/greetings-and-introductions")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "greetings-and-introductions"
    assert body["courseSlug"] == "english-foundations"
    assert body["courseTitle"] == "English Foundations"
    assert body["level"] == "A1"
    assert body["estimatedMinutes"] == 10
    assert "Hello" in body["theory"]


async def test_missing_course_is_404(client: AsyncClient, catalog: AsyncSession) -> None:
    response = await client.get(f"{COURSES}/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_unpublished_course_is_404(
    client: AsyncClient, catalog: AsyncSession, db_session: AsyncSession
) -> None:
    db_session.add(_course())
    await db_session.commit()

    response = await client.get(f"{COURSES}/draft-course")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_missing_lesson_is_404(client: AsyncClient, catalog: AsyncSession) -> None:
    response = await client.get(f"{LESSONS}/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_lesson_of_unpublished_course_is_404(
    client: AsyncClient, catalog: AsyncSession, db_session: AsyncSession
) -> None:
    draft = _course()
    db_session.add(draft)
    await db_session.flush()
    db_session.add(_lesson(draft.id, is_published=True))
    await db_session.commit()

    response = await client.get(f"{LESSONS}/draft-lesson")
    assert response.status_code == 404


async def test_seed_is_idempotent(client: AsyncClient, catalog: AsyncSession) -> None:
    async def counts() -> tuple[int, int]:
        courses = await catalog.scalar(select(func.count()).select_from(Course))
        lessons = await catalog.scalar(select(func.count()).select_from(Lesson))
        return courses or 0, lessons or 0

    before = await counts()
    await seed_catalog(catalog)
    after = await counts()

    assert before == after == (2, 6)
