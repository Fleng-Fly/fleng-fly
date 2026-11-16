"""Read-only user/profile access.

Authentication lives in the `auth` module; this service only reads data for an
already-authenticated user. It never creates users (registration is the only
place that does).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.modules.users.schemas import UserResponse


async def get_user_with_profile(db: AsyncSession, user_id: UUID) -> User | None:
    statement = select(User).options(selectinload(User.profile)).where(User.id == user_id)
    return (await db.execute(statement)).scalar_one_or_none()


def to_user_response(user: User) -> UserResponse:
    profile = user.profile
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=profile.display_name if profile else user.email.split("@")[0],
        level=profile.level if profile else 1,
        xp=profile.xp if profile else 0,
        english_level=profile.english_level if profile else "A1",
        preferred_language=profile.preferred_language if profile else "English",
        created_at=user.created_at,
    )
