from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.db.models import User
from app.db.session import get_db
from app.modules.gamification.service import lock_learner
from app.modules.users.schemas import ProfileUpdate, UserResponse
from app.modules.users.service import to_user_response

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Read the authenticated user's profile. Read-only; never creates a user."""
    return to_user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    await lock_learner(db, current_user.id)
    if current_user.profile is None:
        raise ApiError(409, "PROFILE_MISSING", "Profile unavailable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            raise ApiError(422, "VALIDATION_FAILED", "Profile fields cannot be null")
        setattr(current_user.profile, key, value)
    await db.commit()
    return to_user_response(current_user)
