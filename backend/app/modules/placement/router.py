from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import PlacementAttempt, User
from app.db.session import get_db
from app.modules.placement import service
from app.modules.placement.schemas import PlacementAnswers, PlacementDetail, PlacementSummary

router = APIRouter(prefix="/placement-test", tags=["placement"])


@router.post("/attempts", response_model=PlacementDetail, status_code=201)
async def start_attempt(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.start(db, user.id)


@router.get("/attempts", response_model=list[PlacementSummary])
async def history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempts = (
        await db.scalars(
            select(PlacementAttempt)
            .where(PlacementAttempt.user_id == user.id)
            .order_by(PlacementAttempt.started_at.desc(), PlacementAttempt.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [service.summary(attempt) for attempt in attempts]


@router.get("/attempts/{attempt_id}", response_model=PlacementDetail)
async def get_attempt(
    attempt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.detail(db, await service.owned(db, user.id, attempt_id))


@router.put("/attempts/{attempt_id}/answers", response_model=PlacementDetail)
async def save_answers(
    attempt_id: UUID,
    payload: PlacementAnswers,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.save_answers(db, user.id, attempt_id, payload)


@router.post("/attempts/{attempt_id}/complete", response_model=PlacementDetail)
async def complete_attempt(
    attempt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.complete(db, user.id, attempt_id)
