from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Course, Lesson, User, VocabularyItem, VocabularyReview
from app.modules.gamification.service import award, lock_learner, record_activity
from app.modules.vocabulary.schemas import VocabularyCreate


async def owned(db: AsyncSession, user: User, item_id: UUID) -> VocabularyItem:
    item = await db.scalar(
        select(VocabularyItem)
        .where(VocabularyItem.id == item_id, VocabularyItem.user_id == user.id)
        .with_for_update()
    )
    if item is None:
        raise ApiError(404, "NOT_FOUND", "Vocabulary item not found")
    return item


async def add(db: AsyncSession, user: User, payload: VocabularyCreate) -> VocabularyItem:
    await lock_learner(db, user.id)
    if (
        payload.lesson_id
        and await db.scalar(
            select(Lesson.id)
            .join(Course)
            .where(
                Lesson.id == payload.lesson_id,
                Lesson.is_published.is_(True),
                Course.is_published.is_(True),
            )
        )
        is None
    ):
        raise ApiError(404, "NOT_FOUND", "Lesson not found")
    word = payload.word.casefold()
    if await db.scalar(
        select(VocabularyItem.id).where(
            VocabularyItem.user_id == user.id, VocabularyItem.word == word
        )
    ):
        raise ApiError(409, "WORD_EXISTS", "Word already saved")
    item = VocabularyItem(user_id=user.id, **payload.model_dump(exclude={"word"}), word=word)
    db.add(item)
    await db.flush()
    await award(db, user.id)
    await db.commit()
    await db.refresh(item)
    return item


async def review(db: AsyncSession, user: User, item_id: UUID, remembered: bool):
    await lock_learner(db, user.id)
    item = await owned(db, user, item_id)
    item.learned = remembered
    item.due_at = datetime.now(UTC) + timedelta(days=7 if remembered else 1)
    db.add(VocabularyReview(item_id=item.id, remembered=remembered))
    await record_activity(db, user.id)
    await db.commit()
    return item
