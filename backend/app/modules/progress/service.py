"""Read-only access to a user's aggregate learning progress.

Progress is server-derived. There is deliberately no client-writable mutation:
letting a client set its own XP/progress would break progress integrity
(see `docs/security.md`). Write endpoints arrive with lesson completion, where
the backend records progress from graded activity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress
from app.modules.progress.schemas import ProgressResponse


async def get_progress(db: AsyncSession, user_id: UUID) -> Progress | None:
    return await db.scalar(select(Progress).where(Progress.user_id == user_id))


def to_progress_response(user_id: UUID, progress: Progress | None) -> ProgressResponse:
    if progress is None:
        # Safety net for accounts created before registration seeded progress.
        return ProgressResponse(
            user_id=user_id,
            lessons_started=0,
            lessons_completed=0,
            study_minutes=0,
            last_activity_at=None,
            updated_at=None,
        )
    return ProgressResponse(
        user_id=progress.user_id,
        lessons_started=progress.lessons_started,
        lessons_completed=progress.lessons_completed,
        study_minutes=progress.study_minutes,
        last_activity_at=progress.last_activity_at,
        updated_at=progress.updated_at,
    )
