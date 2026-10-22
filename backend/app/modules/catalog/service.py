"""Read-only catalog access: published courses and their published lessons.

Unpublished content is never returned; callers translate `None` into a `404`
that does not reveal whether the resource exists. There are no writes here —
content is managed through seed data / operations, not the public API.
"""

from dataclasses import dataclass

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, Lesson
from app.modules.catalog.schemas import (
    CourseDetailResponse,
    CourseSummaryResponse,
    LessonDetailResponse,
    LessonSummaryResponse,
)
from app.modules.exercises.schemas import ExercisePublicResponse


@dataclass(frozen=True)
class CourseWithLessons:
    """A published course together with its published lessons."""

    course: Course
    lessons: list[Lesson]


def _lesson_summary(lesson: Lesson) -> LessonSummaryResponse:
    return LessonSummaryResponse(
        id=lesson.id,
        slug=lesson.slug,
        title=lesson.title,
        summary=lesson.summary,
        position=lesson.position,
        estimated_minutes=lesson.estimated_minutes,
    )


async def list_published_courses(db: AsyncSession) -> list[CourseSummaryResponse]:
    """Published courses ordered by `position`, with a count of published lessons."""
    lesson_count = func.count(Lesson.id)
    statement = (
        select(Course, lesson_count)
        .outerjoin(
            Lesson,
            and_(Lesson.course_id == Course.id, Lesson.is_published.is_(True)),
        )
        .where(Course.is_published.is_(True))
        .group_by(Course.id)
        .order_by(Course.position, Course.title)
    )
    rows = (await db.execute(statement)).all()
    return [
        CourseSummaryResponse(
            id=course.id,
            slug=course.slug,
            title=course.title,
            description=course.description,
            level=course.level,
            lesson_count=count,
        )
        for course, count in rows
    ]


async def get_published_course(db: AsyncSession, slug: str) -> CourseWithLessons | None:
    """Return a published course and its published lessons, or `None`."""
    course = await db.scalar(
        select(Course).where(Course.slug == slug, Course.is_published.is_(True))
    )
    if course is None:
        return None
    lessons = (
        (
            await db.execute(
                select(Lesson)
                .where(Lesson.course_id == course.id, Lesson.is_published.is_(True))
                .order_by(Lesson.position, Lesson.title)
            )
        )
        .scalars()
        .all()
    )
    return CourseWithLessons(course=course, lessons=list(lessons))


def to_course_detail(result: CourseWithLessons) -> CourseDetailResponse:
    course = result.course
    return CourseDetailResponse(
        id=course.id,
        slug=course.slug,
        title=course.title,
        description=course.description,
        level=course.level,
        lessons=[_lesson_summary(lesson) for lesson in result.lessons],
    )


async def get_published_lesson(db: AsyncSession, slug: str) -> tuple[Lesson, Course] | None:
    """Return a published lesson of a published course, or `None`."""
    row = (
        await db.execute(
            select(Lesson, Course)
            .join(Course, Lesson.course_id == Course.id)
            .where(
                Lesson.slug == slug,
                Lesson.is_published.is_(True),
                Course.is_published.is_(True),
            )
        )
    ).first()
    if row is None:
        return None
    lesson, course = row
    return lesson, course


def to_lesson_detail(
    lesson: Lesson, course: Course, exercises: list[ExercisePublicResponse]
) -> LessonDetailResponse:
    return LessonDetailResponse(
        id=lesson.id,
        slug=lesson.slug,
        title=lesson.title,
        summary=lesson.summary,
        theory=lesson.theory,
        position=lesson.position,
        estimated_minutes=lesson.estimated_minutes,
        course_slug=course.slug,
        course_title=course.title,
        level=course.level,
        exercises=exercises,
    )
