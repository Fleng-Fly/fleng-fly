import asyncio

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.db.models import User
from app.db.session import get_db
from app.modules.auth.security import hash_password, verify_password
from app.modules.gamification.service import lock_learner
from app.modules.users.schemas import PasswordChange, ProfileUpdate, UserResponse
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
    changes = payload.model_dump(exclude_unset=True)
    email = changes.pop("email", None)
    if "email" in payload.model_fields_set:
        if email is None:
            raise ApiError(422, "VALIDATION_FAILED", "Email cannot be null")
        email = email.strip().lower()
        if email != current_user.email:
            existing = await db.scalar(select(User.id).where(User.email == email))
            if existing is not None:
                raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")
            current_user.email = email
    for key, value in changes.items():
        if value is None:
            raise ApiError(422, "VALIDATION_FAILED", "Profile fields cannot be null")
        setattr(current_user.profile, key, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists") from None
    return to_user_response(current_user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await lock_learner(db, current_user.id)
    if not await asyncio.to_thread(
        verify_password, current_user.password_hash, payload.current_password
    ):
        raise ApiError(400, "INVALID_PASSWORD", "Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise ApiError(422, "VALIDATION_FAILED", "Choose a different new password")
    current_user.password_hash = await asyncio.to_thread(hash_password, payload.new_password)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
