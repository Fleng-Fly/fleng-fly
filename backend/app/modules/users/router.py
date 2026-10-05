from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import User
from app.modules.users.schemas import UserResponse
from app.modules.users.service import to_user_response

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Read the authenticated user's profile. Read-only; never creates a user."""
    return to_user_response(current_user)
