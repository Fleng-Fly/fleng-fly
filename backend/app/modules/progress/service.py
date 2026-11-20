"""Learner progress: the aggregate row plus derived counters.

Progress is server-derived. Clients cannot set their own counters or XP: the
aggregate is written here (when a lesson starts/completes) and the extra
counters (`exercises_completed`, per-course progress) are computed from
`exercise_submissions` and `lesson_progress` on read.
"""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import (
    Course,
    ExerciseSubmission,
    Lesson,
    LessonProgress,
    Profile,
    Progress,
    VocabularyItem,
    VocabularyReview,
)
from app.modules.gamification.service import streak
from app.modules.progress.schemas import (
    CourseProgressResponse,
    DailyGoalResponse,
    DailyGoalsResponse,
    ProgressResponse,
    XPHistoryResponse,
)


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


async def list_course_progress(
    db: AsyncSession, user_id: UUID, *, include_drafts: bool = False
) -> list[CourseProgressResponse]:
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
            and_(
                Lesson.course_id == Course.id,
                (true() if include_drafts else Lesson.is_published.is_(True)),
            ),
        )
        .outerjoin(
            LessonProgress,
            and_(
                LessonProgress.lesson_id == Lesson.id,
                LessonProgress.user_id == user_id,
            ),
        )
        .where(true() if include_drafts else Course.is_published.is_(True))
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
            completion_percent=round(100 * lessons_completed / lessons_total, 2)
            if lessons_total
            else 0.0,
        )
        for course, lessons_total, lessons_started, lessons_completed in rows
    ]


async def to_progress_response(
    db: AsyncSession,
    *,
    user_id: UUID,
    progress: Progress | None,
    xp: int,
    include_drafts: bool = False,
) -> ProgressResponse:
    exercises_completed = await count_completed_exercises(db, user_id)
    courses = await list_course_progress(db, user_id, include_drafts=include_drafts)
    # Read actual lesson state even for legacy accounts without an aggregate row.
    # Counts span the learner's history; course breakdown follows catalog visibility.
    totals = (
        await db.execute(
            select(
                func.count(LessonProgress.id),
                func.count(LessonProgress.id).filter(LessonProgress.status == "completed"),
            ).where(LessonProgress.user_id == user_id)
        )
    ).one()
    return ProgressResponse(
        user_id=user_id,
        lessons_started=totals[0],
        lessons_completed=totals[1],
        exercises_completed=exercises_completed,
        study_minutes=progress.study_minutes if progress else 0,
        xp=xp,
        last_activity_at=progress.last_activity_at if progress else None,
        updated_at=progress.updated_at if progress else None,
        courses=courses,
        active_courses=sum(
            0 < course.lessons_started and course.lessons_completed < course.lessons_total
            for course in courses
        ),
        streak=await streak(db, user_id),
        xp_history=XPHistoryResponse(),
    )


def local_day_window(
    zone_name: str, now: datetime | None = None
) -> tuple[date, datetime, datetime]:
    """The learner's current local date and its [start, next start) bounds in UTC.

    Local midnights are converted individually, so 23/25-hour DST days are exact.
    """
    zone = ZoneInfo(zone_name)
    today = (now or datetime.now(UTC)).astimezone(zone).date()
    start = datetime.combine(today, time.min, tzinfo=zone).astimezone(UTC)
    end = datetime.combine(today + timedelta(days=1), time.min, tzinfo=zone).astimezone(UTC)
    return today, start, end


async def daily_goals(
    db: AsyncSession, user_id: UUID, profile: Profile | None, now: datetime | None = None
) -> DailyGoalsResponse:
    """Derive today's progress from existing records; nothing is stored per day.

    Lessons: `completed_at` is written once per lesson, so reopening never recounts.
    Words: distinct words remembered in a review today, so repeating one word counts once.
    """
    zone_name = (profile.timezone if profile else None) or get_settings().learning_timezone
    today, start, end = local_day_window(zone_name, now)
    lessons = await db.scalar(
        select(func.count())
        .select_from(LessonProgress)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed_at >= start,
            LessonProgress.completed_at < end,
        )
    )
    words = await db.scalar(
        select(func.count(func.distinct(VocabularyReview.item_id)))
        .join(VocabularyItem, VocabularyItem.id == VocabularyReview.item_id)
        .where(
            VocabularyItem.user_id == user_id,
            VocabularyReview.remembered.is_(True),
            VocabularyReview.created_at >= start,
            VocabularyReview.created_at < end,
        )
    )
    return DailyGoalsResponse(
        date=today,
        timezone=zone_name,
        lessons=DailyGoalResponse(
            goal=profile.daily_lessons_goal if profile else 1, done=lessons or 0
        ),
        vocabulary=DailyGoalResponse(
            goal=profile.daily_words_goal if profile else 10, done=words or 0
        ),
    )
