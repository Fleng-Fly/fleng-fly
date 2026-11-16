from datetime import datetime
from typing import Literal
from uuid import UUID

from app.core.schemas import CamelModel
from app.modules.gamification.schemas import StreakResponse


class CourseProgressResponse(CamelModel):
    """The caller's progress through one published course."""

    course_id: UUID
    slug: str
    title: str
    level: str
    lessons_total: int
    lessons_started: int
    lessons_completed: int
    completion_percent: float


class XPHistoryResponse(CamelModel):
    """The current schema has no immutable XP award amounts/timestamps."""

    available: Literal[False] = False
    reason: Literal["XP_AWARD_HISTORY_NOT_RECORDED"] = "XP_AWARD_HISTORY_NOT_RECORDED"
    last_7_days: None = None
    last_30_days: None = None


class ProgressResponse(CamelModel):
    """Aggregate progress plus a per-course breakdown.

    New fields are additive: existing clients that read only `lessonsStarted`,
    `lessonsCompleted`, `studyMinutes`, `lastActivityAt`, `updatedAt` and
    `userId` keep working.
    """

    user_id: UUID
    lessons_started: int
    lessons_completed: int
    exercises_completed: int
    study_minutes: int
    xp: int
    last_activity_at: datetime | None
    updated_at: datetime | None
    courses: list[CourseProgressResponse]
    active_courses: int
    streak: StreakResponse
    xp_history: XPHistoryResponse
