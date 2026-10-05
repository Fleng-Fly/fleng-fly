from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel


class ProgressResponse(CamelModel):
    user_id: UUID
    lessons_started: int
    lessons_completed: int
    study_minutes: int
    last_activity_at: datetime | None
    updated_at: datetime | None
