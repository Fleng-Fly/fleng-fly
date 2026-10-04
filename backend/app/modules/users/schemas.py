from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel


class UserResponse(CamelModel):
    id: UUID
    email: str
    display_name: str
    level: int
    xp: int
    created_at: datetime
