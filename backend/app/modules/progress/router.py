from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.progress.schemas import ProgressResponse
from app.modules.progress.service import get_progress, to_progress_response

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=ProgressResponse)
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    progress = await get_progress(db, current_user.id)
    xp = current_user.profile.xp if current_user.profile else 0
    return await to_progress_response(db, user_id=current_user.id, progress=progress, xp=xp)
