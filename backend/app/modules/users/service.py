"""User profile reads.

DEVELOPMENT-ONLY: `get_or_create_user` persists a profile for the stub identity
so the slice returns real rows. It is only reachable behind the dev auth
dependency (app.api.deps) and must be replaced with a plain lookup once real
authentication exists.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Profile, User
from app.modules.users.schemas import UserResponse


async def get_or_create_user(db: AsyncSession, user_id: UUID) -> UserResponse:
    statement = select(User).options(selectinload(User.profile)).where(User.id == user_id)
    user = (await db.execute(statement)).scalar_one_or_none()

    if user is None:
        user = User(
            id=user_id,
            email=f"dev+{user_id}@fleng.local",
            password_hash="dev-only-not-a-login-credential",
        )
        user.profile = Profile(display_name="Dev Learner")
        db.add(user)
        await db.commit()
        user = (await db.execute(statement)).scalar_one()

    profile = user.profile
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=profile.display_name if profile else "Learner",
        level=profile.level if profile else 1,
        xp=profile.xp if profile else 0,
        created_at=user.created_at,
    )
