"""Reading HTTP routes. Thin: validation and shaping only; rules live in the services."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.core.limits import consume
from app.db.models import ReadingArticle, ReadingUserProgress, User
from app.db.session import get_db
from app.modules.reading import content, learning, library, personal
from app.modules.reading.content import ArticleFilters
from app.modules.reading.schemas import (
    ReadingArticleDetail,
    ReadingArticleList,
    ReadingArticleSummary,
    ReadingBookmarkResponse,
    ReadingCategoryRef,
    ReadingCategoryResponse,
    ReadingLevel,
    ReadingPreferencesResponse,
    ReadingPreferencesUpdate,
    ReadingProgressResponse,
    ReadingProgressUpdate,
)

router = APIRouter(prefix="/reading", tags=["reading"])

PROGRESS_WRITES_PER_MINUTE = 60


def _progress(row: ReadingUserProgress | None) -> ReadingProgressResponse | None:
    if row is None:
        return None
    return ReadingProgressResponse(
        status=row.status,  # type: ignore[arg-type]
        read_percent=row.read_percent,
        best_score_percent=row.best_score_percent,
        attempts_count=row.attempts_count,
        xp_awarded=row.xp_awarded,
    )


def _summary(
    article: ReadingArticle, progress: ReadingUserProgress | None, bookmarked: bool
) -> ReadingArticleSummary:
    return ReadingArticleSummary(
        id=article.id,
        slug=article.slug,
        title=article.title,
        description=article.description,
        level=article.level,  # type: ignore[arg-type]
        reading_minutes=article.reading_minutes,
        cover_image_url=article.cover_image_url,
        cover_alt=article.cover_alt,
        category=ReadingCategoryRef(
            id=article.category.id, slug=article.category.slug, title=article.category.title
        ),
        published_at=article.published_at,
        progress=_progress(progress),
        bookmarked=bookmarked,
    )


async def _article(db: AsyncSession, slug: str) -> ReadingArticle:
    article = await content.get_article(db, slug=slug, available_only=True)
    if article is None:
        raise ApiError(404, "NOT_FOUND", "Article not found")
    return article


@router.get("/categories", response_model=list[ReadingCategoryResponse])
async def list_categories(
    _user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ReadingCategoryResponse]:
    return [
        ReadingCategoryResponse(
            id=c.id,
            slug=c.slug,
            title=c.title,
            description=c.description,
            article_count=count,
        )
        for c, count in await library.category_counts(db)
    ]


@router.get("/articles", response_model=ReadingArticleList)
async def list_articles(
    category_id: UUID | None = Query(None, alias="categoryId"),
    level: ReadingLevel | None = None,
    bookmarked: bool | None = None,
    progress: str | None = Query(None, description="new | in_progress | completed"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingArticleList:
    filters = ArticleFilters(category_id=category_id, level=level, limit=limit, offset=offset)
    articles, total = await library.list_for_learner(
        db, user.id, filters, bookmarked=bookmarked, progress=progress
    )
    ids = [a.id for a in articles]
    progress_rows = await library.progress_by_article(db, user.id, ids)
    saved = await library.bookmarked_ids(db, user.id, ids)
    return ReadingArticleList(
        items=[_summary(a, progress_rows.get(a.id), a.id in saved) for a in articles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/articles/{slug}", response_model=ReadingArticleDetail)
async def get_article(
    slug: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ReadingArticleDetail:
    article = await _article(db, slug)
    summary = _summary(
        article,
        await learning.get_progress(db, user.id, article.id),
        await personal.is_bookmarked(db, user.id, article.id),
    )
    return ReadingArticleDetail(
        **summary.model_dump(),
        content=article.content,
        question_count=len(article.questions),
        points_possible=sum(q.points for q in article.questions),
    )


@router.put("/articles/{slug}/progress", response_model=ReadingProgressResponse)
async def update_progress(
    slug: str,
    body: ReadingProgressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingProgressResponse:
    await consume(db, f"reading:progress:{user.id}", PROGRESS_WRITES_PER_MINUTE, 60)
    article = await _article(db, slug)
    row = await learning.update_read_progress(db, user.id, article.id, body.percent)
    response = _progress(row)
    assert response is not None
    return response


@router.put("/articles/{slug}/bookmark", response_model=ReadingBookmarkResponse)
async def add_bookmark(
    slug: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ReadingBookmarkResponse:
    article = await _article(db, slug)
    await personal.add_bookmark(db, user.id, article.id)
    return ReadingBookmarkResponse(article_id=article.id, bookmarked=True)


@router.delete("/articles/{slug}/bookmark", status_code=204)
async def remove_bookmark(
    slug: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Response:
    # Works for hidden articles too, so a stale bookmark can always be dropped.
    article = await content.get_article(db, slug=slug, available_only=False)
    if article is not None:
        await personal.remove_bookmark(db, user.id, article.id)
    return Response(status_code=204)


@router.get("/bookmarks", response_model=list[ReadingArticleSummary])
async def list_bookmarks(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ReadingArticleSummary]:
    articles = await personal.list_bookmarks(db, user.id)
    progress_rows = await library.progress_by_article(db, user.id, [a.id for a in articles])
    return [_summary(a, progress_rows.get(a.id), True) for a in articles]


@router.get("/preferences", response_model=ReadingPreferencesResponse)
async def get_preferences(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ReadingPreferencesResponse:
    categories = await personal.get_topic_preferences(db, user.id)
    return ReadingPreferencesResponse(
        categories=[ReadingCategoryRef(id=c.id, slug=c.slug, title=c.title) for c in categories]
    )


@router.put("/preferences", response_model=ReadingPreferencesResponse)
async def set_preferences(
    body: ReadingPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingPreferencesResponse:
    categories = await personal.set_topic_preferences(db, user.id, body.category_ids)
    return ReadingPreferencesResponse(
        categories=[ReadingCategoryRef(id=c.id, slug=c.slug, title=c.title) for c in categories]
    )
