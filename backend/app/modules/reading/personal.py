"""A learner's own Reading data: bookmarks and topic preferences.

All writes are idempotent. Per-learner writes take the same learner lock as the rest of the
learning services, so concurrent duplicate requests cannot violate the unique constraints.
"""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import ReadingArticle, ReadingBookmark, ReadingCategory, ReadingTopicPreference
from app.modules.gamification.service import lock_learner
from app.modules.reading.content import available_clauses, get_article


async def add_bookmark(db: AsyncSession, user_id: UUID, article_id: UUID) -> ReadingBookmark:
    if await get_article(db, article_id=article_id, available_only=True) is None:
        raise ApiError(404, "NOT_FOUND", "Article not found")
    await lock_learner(db, user_id)
    bookmark = await db.scalar(
        select(ReadingBookmark).where(
            ReadingBookmark.user_id == user_id, ReadingBookmark.article_id == article_id
        )
    )
    if bookmark is None:
        bookmark = ReadingBookmark(user_id=user_id, article_id=article_id)
        db.add(bookmark)
    await db.commit()
    return bookmark


async def remove_bookmark(db: AsyncSession, user_id: UUID, article_id: UUID) -> bool:
    """Remove a bookmark (even of an article that is no longer available). False if absent."""
    await lock_learner(db, user_id)
    result = await db.execute(
        delete(ReadingBookmark).where(
            ReadingBookmark.user_id == user_id, ReadingBookmark.article_id == article_id
        )
    )
    await db.commit()
    return bool(result.rowcount)  # type: ignore[attr-defined]


async def is_bookmarked(db: AsyncSession, user_id: UUID, article_id: UUID) -> bool:
    return (
        await db.scalar(
            select(ReadingBookmark.id).where(
                ReadingBookmark.user_id == user_id, ReadingBookmark.article_id == article_id
            )
        )
    ) is not None


async def list_bookmarks(db: AsyncSession, user_id: UUID) -> list[ReadingArticle]:
    """Bookmarked articles that are still available, most recently saved first."""
    statement = (
        select(ReadingArticle)
        .join(ReadingBookmark, ReadingBookmark.article_id == ReadingArticle.id)
        .where(ReadingBookmark.user_id == user_id, *available_clauses())
        .options(selectinload(ReadingArticle.category))
        .order_by(ReadingBookmark.created_at.desc(), ReadingBookmark.id)
    )
    return list((await db.scalars(statement)).all())


async def set_topic_preferences(
    db: AsyncSession, user_id: UUID, category_ids: Iterable[UUID]
) -> list[ReadingCategory]:
    """Replace the learner's preferred topics. Unknown or inactive categories are rejected."""
    wanted = set(category_ids)
    if wanted:
        valid = set(
            (
                await db.scalars(
                    select(ReadingCategory.id).where(
                        ReadingCategory.id.in_(wanted), ReadingCategory.is_active.is_(True)
                    )
                )
            ).all()
        )
        if valid != wanted:
            raise ApiError(
                422,
                "VALIDATION_FAILED",
                "Unknown or inactive reading category",
                details={"categoryIds": sorted(str(c) for c in wanted - valid)},
            )
    await lock_learner(db, user_id)
    existing = set(
        (
            await db.scalars(
                select(ReadingTopicPreference.category_id).where(
                    ReadingTopicPreference.user_id == user_id
                )
            )
        ).all()
    )
    if existing - wanted:
        await db.execute(
            delete(ReadingTopicPreference).where(
                ReadingTopicPreference.user_id == user_id,
                ReadingTopicPreference.category_id.in_(existing - wanted),
            )
        )
    db.add_all(
        ReadingTopicPreference(user_id=user_id, category_id=c) for c in sorted(wanted - existing)
    )
    await db.commit()
    return await get_topic_preferences(db, user_id)


async def get_topic_preferences(db: AsyncSession, user_id: UUID) -> list[ReadingCategory]:
    """Preferred categories that are still active."""
    statement = (
        select(ReadingCategory)
        .join(ReadingTopicPreference, ReadingTopicPreference.category_id == ReadingCategory.id)
        .where(ReadingTopicPreference.user_id == user_id, ReadingCategory.is_active.is_(True))
        .order_by(ReadingCategory.position, ReadingCategory.title)
    )
    return list((await db.scalars(statement)).all())
