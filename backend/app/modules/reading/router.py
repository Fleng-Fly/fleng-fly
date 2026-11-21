"""Reading HTTP routes. Thin: validation and shaping only; rules live in the services."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.core.limits import consume
from app.db.models import ReadingArticle, ReadingAttempt, ReadingUserProgress, User
from app.db.session import get_db
from app.modules.reading import content, learning, library, personal, study
from app.modules.reading.content import ArticleFilters
from app.modules.reading.schemas import (
    ReadingAnswerPublic,
    ReadingAnswersUpdate,
    ReadingArticleDetail,
    ReadingArticleList,
    ReadingArticleSummary,
    ReadingAttemptResponse,
    ReadingAttemptResult,
    ReadingAttemptSummary,
    ReadingBookmarkResponse,
    ReadingCategoryRef,
    ReadingCategoryResponse,
    ReadingHeartbeatRequest,
    ReadingHeartbeatResponse,
    ReadingLevel,
    ReadingPreferencesResponse,
    ReadingPreferencesUpdate,
    ReadingProgressResponse,
    ReadingProgressUpdate,
    ReadingQuestionPublic,
    ReadingReviewItem,
    ReadingStudyArticleResponse,
    ReadingStudyDayResponse,
    ReadingStudyTimeResponse,
    ReadingSubmitRequest,
)

router = APIRouter(prefix="/reading", tags=["reading"])

PROGRESS_WRITES_PER_MINUTE = 60
HEARTBEATS_PER_MINUTE = 20
ATTEMPT_STARTS_PER_HOUR = 30
ATTEMPT_WRITES_PER_MINUTE = 30


def _progress(row: ReadingUserProgress | None, seconds: int = 0) -> ReadingProgressResponse | None:
    if row is None:
        return None
    return ReadingProgressResponse(
        active_seconds=seconds,
        status=row.status,  # type: ignore[arg-type]
        read_percent=row.read_percent,
        best_score_percent=row.best_score_percent,
        attempts_count=row.attempts_count,
        xp_awarded=row.xp_awarded,
    )


def _summary(
    article: ReadingArticle,
    progress: ReadingUserProgress | None,
    bookmarked: bool,
    seconds: int = 0,
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
        progress=_progress(progress, seconds),
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
    seconds = await study.seconds_by_article(db, user.id, ids)
    return ReadingArticleList(
        items=[
            _summary(a, progress_rows.get(a.id), a.id in saved, seconds.get(a.id, 0))
            for a in articles
        ],
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
        (await study.seconds_by_article(db, user.id, [article.id])).get(article.id, 0),
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
    seconds = (await study.seconds_by_article(db, user.id, [article.id])).get(article.id, 0)
    response = _progress(row, seconds)
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
    ids = [a.id for a in articles]
    progress_rows = await library.progress_by_article(db, user.id, ids)
    seconds = await study.seconds_by_article(db, user.id, ids)
    return [_summary(a, progress_rows.get(a.id), True, seconds.get(a.id, 0)) for a in articles]


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


# --- quiz attempts ----------------------------------------------------------------------


async def _attempt_response(
    db: AsyncSession, attempt: ReadingAttempt, *, already_submitted: bool = False
) -> ReadingAttemptResponse:
    article = await db.get(ReadingArticle, attempt.article_id)
    assert article is not None
    questions = None
    result = None
    if attempt.status == "in_progress":
        full = await content.get_article(db, article_id=article.id, available_only=False)
        assert full is not None
        questions = [
            ReadingQuestionPublic(
                id=q.id,
                prompt=q.prompt,
                points=q.points,
                answers=[ReadingAnswerPublic(id=a.id, text=a.text) for a in q.answers],
            )
            for q in full.questions
        ]
    elif attempt.result is not None:
        result = ReadingAttemptResult(
            score_percent=attempt.score_percent or 0,
            points_earned=attempt.points_earned or 0,
            points_possible=attempt.points_possible or 0,
            passed=bool(attempt.passed),
            pass_mark=learning.PASS_PERCENT,
            xp_awarded=attempt.xp_awarded,
            questions=[
                ReadingReviewItem.model_validate(item) for item in attempt.result["questions"]
            ],
        )
    return ReadingAttemptResponse(
        id=attempt.id,
        article_slug=article.slug,
        attempt_number=attempt.attempt_number,
        status=attempt.status,  # type: ignore[arg-type]
        answers={UUID(q): UUID(a) for q, a in attempt.answers.items()},
        questions=questions,
        result=result,
        already_submitted=already_submitted,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
    )


@router.post("/articles/{slug}/attempts", response_model=ReadingAttemptResponse)
async def start_attempt(
    slug: str,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingAttemptResponse:
    """Start a quiz attempt (201) or resume the one already open (200)."""
    article = await _article(db, slug)
    resumed = await learning.get_active_attempt(db, user.id, article.id)
    if resumed is None:
        await consume(db, f"reading:attempt-start:{user.id}", ATTEMPT_STARTS_PER_HOUR, 3600)
    attempt = await learning.start_attempt(db, user.id, article.id)
    response.status_code = 200 if resumed is not None else 201
    return await _attempt_response(db, attempt)


@router.get("/articles/{slug}/attempts", response_model=list[ReadingAttemptSummary])
async def list_attempts(
    slug: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ReadingAttemptSummary]:
    article = await _article(db, slug)
    return [
        ReadingAttemptSummary(
            id=a.id,
            attempt_number=a.attempt_number,
            status=a.status,  # type: ignore[arg-type]
            score_percent=a.score_percent,
            passed=a.passed,
            xp_awarded=a.xp_awarded,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
        )
        for a in await learning.list_attempts(db, user.id, article.id)
    ]


@router.get("/attempts/{attempt_id}", response_model=ReadingAttemptResponse)
async def get_attempt(
    attempt_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ReadingAttemptResponse:
    return await _attempt_response(db, await learning.get_attempt(db, user.id, attempt_id))


@router.patch("/attempts/{attempt_id}/answers", response_model=ReadingAttemptResponse)
async def save_answers(
    attempt_id: UUID,
    body: ReadingAnswersUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingAttemptResponse:
    await consume(db, f"reading:attempt-write:{user.id}", ATTEMPT_WRITES_PER_MINUTE, 60)
    attempt = await learning.save_answers(db, user.id, attempt_id, body.answers)
    return await _attempt_response(db, attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=ReadingAttemptResponse)
async def submit_attempt(
    attempt_id: UUID,
    body: ReadingSubmitRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingAttemptResponse:
    """Grade the attempt. Repeating the call returns the stored result and pays no XP."""
    current = await learning.get_attempt(db, user.id, attempt_id)
    already = current.status == "submitted"
    if not already:
        await consume(db, f"reading:attempt-write:{user.id}", ATTEMPT_WRITES_PER_MINUTE, 60)
    attempt = await learning.submit_attempt(
        db, user.id, attempt_id, body.answers if body is not None else None
    )
    return await _attempt_response(db, attempt, already_submitted=already)


# --- measured reading time ---------------------------------------------------------------


@router.post("/articles/{slug}/heartbeat", response_model=ReadingHeartbeatResponse)
async def heartbeat(
    slug: str,
    _body: ReadingHeartbeatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingHeartbeatResponse:
    """Report that the learner is actively reading. The server decides how much time to credit."""
    await consume(db, f"reading:heartbeat:{user.id}", HEARTBEATS_PER_MINUTE, 60)
    article = await _article(db, slug)
    result = await study.heartbeat(db, user.id, article.id)
    return ReadingHeartbeatResponse(
        credited_seconds=result.credited_seconds,
        article_seconds=result.article_seconds,
        today_seconds=result.today_seconds,
        total_seconds=result.total_seconds,
        next_beat_in_seconds=study.BEAT_INTERVAL_SECONDS,
        capped=result.capped,
    )


@router.get("/study-time", response_model=ReadingStudyTimeResponse)
async def study_time(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingStudyTimeResponse:
    summary = await study.summary(db, user.id, days=days)
    return ReadingStudyTimeResponse(
        total_seconds=summary.total_seconds,
        today_seconds=summary.today_seconds,
        days=[ReadingStudyDayResponse(date=day, seconds=seconds) for day, seconds in summary.days],
        by_article=[
            ReadingStudyArticleResponse(slug=a.slug, title=a.title, seconds=seconds)
            for a, seconds in summary.by_article
        ],
    )
