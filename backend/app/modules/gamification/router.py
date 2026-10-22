from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Achievement, User, UserAchievement
from app.db.session import get_db
from app.modules.gamification import service
from app.modules.gamification.schemas import AchievementResponse, StreakResponse

router = APIRouter(tags=["gamification"])


@router.get("/streaks/me", response_model=StreakResponse)
async def get_streak(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.streak(db, user.id)


@router.get("/achievements/me", response_model=list[AchievementResponse])
async def achievements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Achievement, UserAchievement.awarded_at)
            .outerjoin(
                UserAchievement,
                (UserAchievement.achievement_code == Achievement.code)
                & (UserAchievement.user_id == user.id),
            )
            .order_by(Achievement.code)
        )
    ).all()
    return [AchievementResponse(code=a.code, title=a.title, awarded_at=at) for a, at in rows]
