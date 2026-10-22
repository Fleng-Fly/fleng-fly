from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User, VocabularyItem, VocabularyReview
from app.db.session import get_db
from app.modules.gamification.service import lock_learner
from app.modules.vocabulary import service
from app.modules.vocabulary.schemas import (
    ReviewRequest,
    ReviewResponse,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyStatsResponse,
    VocabularyUpdate,
)

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("/stats", response_model=VocabularyStatsResponse)
async def vocabulary_stats(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> VocabularyStatsResponse:
    """Count the caller's saved words marked learned, without paging through the list."""
    count = await db.scalar(
        select(func.count())
        .select_from(VocabularyItem)
        .where(VocabularyItem.user_id == user.id, VocabularyItem.learned.is_(True))
    )
    return VocabularyStatsResponse(words_learned=int(count or 0))


@router.get("", response_model=list[VocabularyResponse])
async def list_words(
    due: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    lesson_id: UUID | None = Query(None, alias="lessonId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(VocabularyItem).where(VocabularyItem.user_id == user.id)
    if lesson_id is not None:
        query = query.where(VocabularyItem.lesson_id == lesson_id)
    if due:
        query = query.where(VocabularyItem.due_at <= datetime.now(UTC))
    return (
        await db.scalars(
            query.order_by(VocabularyItem.created_at, VocabularyItem.id).limit(limit).offset(offset)
        )
    ).all()


@router.post("", response_model=VocabularyResponse, status_code=201)
async def add_word(
    payload: VocabularyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.add(db, user, payload)


@router.patch("/{item_id}", response_model=VocabularyResponse)
async def update_word(
    item_id: UUID,
    payload: VocabularyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await lock_learner(db, user.id)
    item = await service.owned(db, user, item_id)
    item.learned = payload.learned
    item.due_at = datetime.now(UTC) + timedelta(days=7 if payload.learned else 0)
    await db.commit()
    return item


@router.delete("/{item_id}", status_code=204)
async def remove_word(
    item_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await lock_learner(db, user.id)
    item = await service.owned(db, user, item_id)
    await db.execute(delete(VocabularyReview).where(VocabularyReview.item_id == item.id))
    await db.delete(item)
    await db.commit()


@router.post("/{item_id}/review", response_model=VocabularyResponse)
async def review_word(
    item_id: UUID,
    payload: ReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.review(db, user, item_id, payload.remembered)


@router.get("/{item_id}/reviews", response_model=list[ReviewResponse])
async def review_history(
    item_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.owned(db, user, item_id)
    return (
        await db.scalars(
            select(VocabularyReview)
            .where(VocabularyReview.item_id == item_id)
            .order_by(VocabularyReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
