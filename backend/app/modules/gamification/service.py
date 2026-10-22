from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import (
    Achievement,
    LearningActivity,
    Profile,
    Progress,
    User,
    UserAchievement,
    VocabularyItem,
)
from app.modules.gamification.schemas import StreakResponse

DEFINITIONS = (
    ("first_lesson", "First Lesson", "lessons", 1),
    ("seven_day_streak", "7-Day Streak", "streak", 7),
    ("hundred_xp", "100 XP", "xp", 100),
    ("ten_lessons", "10 Lessons Completed", "lessons", 10),
    ("vocabulary_beginner", "Vocabulary Beginner", "vocabulary", 5),
)


def calculate_streak(days: list[date], today: date) -> tuple[int, int]:
    days = sorted(set(d for d in days if d <= today))
    longest = run = 0
    previous = None
    for day in days:
        run = run + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    current = run if previous in (today, today - timedelta(days=1)) else 0
    return current, longest


async def streak(db: AsyncSession, user_id: UUID) -> StreakResponse:
    timezone = get_settings().learning_timezone
    today = datetime.now(ZoneInfo(timezone)).date()
    days = list(
        (
            await db.scalars(
                select(LearningActivity.day).where(LearningActivity.user_id == user_id)
            )
        ).all()
    )
    current, longest = calculate_streak(days, today)
    return StreakResponse(
        current=current,
        longest=longest,
        last_activity_date=max(days) if days else None,
        timezone=timezone,
    )


async def lock_learner(db: AsyncSession, user_id: UUID) -> None:
    # Same lock order for grading, vocabulary, activity and achievement awards.
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())


async def record_activity(db: AsyncSession, user_id: UUID) -> None:
    await lock_learner(db, user_id)
    day = datetime.now(ZoneInfo(get_settings().learning_timezone)).date()
    if (
        await db.scalar(
            select(LearningActivity.id).where(
                LearningActivity.user_id == user_id, LearningActivity.day == day
            )
        )
        is None
    ):
        db.add(LearningActivity(user_id=user_id, day=day))
    await db.flush()
    await award(db, user_id)


async def award(db: AsyncSession, user_id: UUID) -> None:
    await lock_learner(db, user_id)
    await db.flush()
    progress = await db.scalar(select(Progress).where(Progress.user_id == user_id))
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    metrics = {
        "lessons": progress.lessons_completed if progress else 0,
        "xp": profile.xp if profile else 0,
        "streak": (await streak(db, user_id)).longest,
        "vocabulary": await db.scalar(
            select(func.count())
            .select_from(VocabularyItem)
            .where(VocabularyItem.user_id == user_id)
        )
        or 0,
    }
    for code, _title, metric, threshold in DEFINITIONS:
        # Definitions are migration-owned, not editable by clients or AI.
        if metrics[metric] >= threshold and await db.get(Achievement, code) is not None:
            if await db.get(UserAchievement, (user_id, code)) is None:
                db.add(
                    UserAchievement(
                        user_id=user_id, achievement_code=code, awarded_at=datetime.now(UTC)
                    )
                )
