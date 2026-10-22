from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel


class CourseProgressResponse(CamelModel):
    """The caller's progress through one published course."""

    course_id: UUID
    slug: str
    title: str
    level: str
    lessons_total: int
    lessons_started: int
    lessons_completed: int


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
