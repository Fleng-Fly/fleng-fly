"""Learner-facing reads: filtered article lists with totals, and per-article decorations."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import (
    ReadingArticle,
    ReadingBookmark,
    ReadingCategory,
    ReadingUserProgress,
)
from app.modules.reading.content import ArticleFilters, available_clauses, validate_level

PROGRESS_FILTERS = ("new", "in_progress", "completed")


async def category_counts(db: AsyncSession) -> list[tuple[ReadingCategory, int]]:
    """Active categories with the number of articles learners can see in each."""
    rows = await db.execute(
        select(ReadingCategory, func.count(ReadingArticle.id))
        .outerjoin(
            ReadingArticle,
            (ReadingArticle.category_id == ReadingCategory.id)
            & (ReadingArticle.status == "published"),
        )
        .where(ReadingCategory.is_active.is_(True))
        .group_by(ReadingCategory.id)
        .order_by(ReadingCategory.position, ReadingCategory.title)
    )
    return [(category, count) for category, count in rows.all()]


async def list_for_learner(
    db: AsyncSession,
    user_id: UUID,
    filters: ArticleFilters,
    *,
    bookmarked: bool | None = None,
    progress: str | None = None,
) -> tuple[list[ReadingArticle], int]:
    """Available articles (newest first) and the total matching the filters.

    `bookmarked=True` keeps only this learner's bookmarks; `progress` is one of
    `new` (no progress yet), `in_progress` or `completed`.
    """
    if filters.level is not None:
        validate_level(filters.level)
    if progress is not None and progress not in PROGRESS_FILTERS:
        raise ApiError(422, "VALIDATION_FAILED", "Unknown progress filter")
    if not 1 <= filters.limit <= 100 or filters.offset < 0:
        raise ApiError(422, "VALIDATION_FAILED", "limit must be 1-100, offset not negative")

    conditions = list(available_clauses())
    if filters.category_id is not None:
        conditions.append(ReadingArticle.category_id == filters.category_id)
    if filters.level is not None:
        conditions.append(ReadingArticle.level == filters.level)
    mine = ReadingBookmark.article_id
    if bookmarked is True:
        conditions.append(
            ReadingArticle.id.in_(select(mine).where(ReadingBookmark.user_id == user_id))
        )
    elif bookmarked is False:
        conditions.append(
            ReadingArticle.id.not_in(select(mine).where(ReadingBookmark.user_id == user_id))
        )
    started = select(ReadingUserProgress.article_id).where(ReadingUserProgress.user_id == user_id)
    if progress == "new":
        conditions.append(ReadingArticle.id.not_in(started))
    elif progress is not None:
        conditions.append(
            ReadingArticle.id.in_(started.where(ReadingUserProgress.status == progress))
        )

    total = await db.scalar(select(func.count()).select_from(ReadingArticle).where(*conditions))
    items = (
        await db.scalars(
            select(ReadingArticle)
            .where(*conditions)
            .options(selectinload(ReadingArticle.category))
            .order_by(
                ReadingArticle.published_at.desc().nulls_last(),
                ReadingArticle.created_at.desc(),
                ReadingArticle.id,
            )
            .limit(filters.limit)
            .offset(filters.offset)
        )
    ).all()
    return list(items), int(total or 0)


async def progress_by_article(
    db: AsyncSession, user_id: UUID, article_ids: Iterable[UUID]
) -> dict[UUID, ReadingUserProgress]:
    ids = list(article_ids)
    if not ids:
        return {}
    rows = await db.scalars(
        select(ReadingUserProgress).where(
            ReadingUserProgress.user_id == user_id, ReadingUserProgress.article_id.in_(ids)
        )
    )
    return {row.article_id: row for row in rows.all()}


async def bookmarked_ids(db: AsyncSession, user_id: UUID, article_ids: Iterable[UUID]) -> set[UUID]:
    ids = list(article_ids)
    if not ids:
        return set()
    rows = await db.scalars(
        select(ReadingBookmark.article_id).where(
            ReadingBookmark.user_id == user_id, ReadingBookmark.article_id.in_(ids)
        )
    )
    return set(rows.all())
