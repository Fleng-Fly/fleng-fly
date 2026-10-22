"""Learner progress: the aggregate row plus derived counters.

Progress is server-derived. Clients cannot set their own counters or XP: the
aggregate is written here (when a lesson starts/completes) and the extra
counters (`exercises_completed`, per-course progress) are computed from
`exercise_submissions` and `lesson_progress` on read.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Course, ExerciseSubmission, Lesson, LessonProgress, Progress
from app.modules.progress.schemas import CourseProgressResponse, ProgressResponse


async def get_progress(db: AsyncSession, user_id: UUID) -> Progress | None:
    return await db.scalar(select(Progress).where(Progress.user_id == user_id))


async def get_or_create_progress(db: AsyncSession, user_id: UUID) -> Progress:
    """Return the aggregate row, creating it if a legacy account lacks one."""
    progress = await get_progress(db, user_id)
    if progress is None:
        progress = Progress(user_id=user_id)
        db.add(progress)
        await db.flush()
    return progress


async def count_completed_exercises(db: AsyncSession, user_id: UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(ExerciseSubmission)
        .where(
            ExerciseSubmission.user_id == user_id,
            ExerciseSubmission.completed.is_(True),
        )
    )
    return int(count or 0)


async def list_course_progress(db: AsyncSession, user_id: UUID) -> list[CourseProgressResponse]:
    """Published courses with lesson totals and the caller's started/completed lessons."""
    statement = (
        select(
            Course,
            func.count(Lesson.id),
            func.count(LessonProgress.id),
            func.count(LessonProgress.id).filter(LessonProgress.status == "completed"),
        )
        .outerjoin(
            Lesson,
            and_(Lesson.course_id == Course.id, Lesson.is_published.is_(True)),
        )
        .outerjoin(
            LessonProgress,
            and_(
                LessonProgress.lesson_id == Lesson.id,
                LessonProgress.user_id == user_id,
            ),
        )
        .where(Course.is_published.is_(True))
        .group_by(Course.id)
        .order_by(Course.position, Course.title)
    )
    rows = (await db.execute(statement)).all()
    return [
        CourseProgressResponse(
            course_id=course.id,
            slug=course.slug,
            title=course.title,
            level=course.level,
            lessons_total=lessons_total,
            lessons_started=lessons_started,
            lessons_completed=lessons_completed,
        )
        for course, lessons_total, lessons_started, lessons_completed in rows
    ]


async def to_progress_response(
    db: AsyncSession, *, user_id: UUID, progress: Progress | None, xp: int
) -> ProgressResponse:
    exercises_completed = await count_completed_exercises(db, user_id)
    courses = await list_course_progress(db, user_id)
    if progress is None:
        # Safety net for accounts created before registration seeded progress.
        return ProgressResponse(
            user_id=user_id,
            lessons_started=0,
            lessons_completed=0,
            exercises_completed=exercises_completed,
            study_minutes=0,
            xp=xp,
            last_activity_at=None,
            updated_at=None,
            courses=courses,
        )
    return ProgressResponse(
        user_id=progress.user_id,
        lessons_started=progress.lessons_started,
        lessons_completed=progress.lessons_completed,
        exercises_completed=exercises_completed,
        study_minutes=progress.study_minutes,
        xp=xp,
        last_activity_at=progress.last_activity_at,
        updated_at=progress.updated_at,
        courses=courses,
    )
