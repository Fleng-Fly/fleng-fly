from datetime import date, datetime
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


class ReadingStudyResponse(CamelModel):
    """Measured active reading time (heartbeat), in seconds.

    Separate from `studyMinutes` (an estimate added when a lesson is completed) and from XP.
    `totalMinutes` is whole minutes, rounded down; `todaySeconds` is the learner's local day.
    """

    total_seconds: int = 0
    total_minutes: int = 0
    today_seconds: int = 0


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
    reading_study: ReadingStudyResponse = ReadingStudyResponse()


class DailyGoalResponse(CamelModel):
    goal: int
    done: int


class DailyGoalsResponse(CamelModel):
    """Today's goals and real activity in the learner's own calendar day.

    `done` may exceed `goal`; clients cap the bar, not the number.
    """

    date: date
    timezone: str
    lessons: DailyGoalResponse
    vocabulary: DailyGoalResponse
