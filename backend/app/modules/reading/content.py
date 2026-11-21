"""Authoring side of Reading: categories, articles, quiz questions and publication.

Learner-facing reads use `available_only=True`: an article is available when its status is
`published` and its category is active. Public services commit on success.
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.db.models import (
    READING_ARTICLE_STATUSES,
    READING_LEVELS,
    ReadingAnswer,
    ReadingArticle,
    ReadingCategory,
    ReadingQuestion,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WORDS_PER_MINUTE = 150  # learners read more slowly than native readers
MAX_READING_MINUTES = 120


@dataclass(frozen=True)
class AnswerInput:
    text: str
    is_correct: bool = False


@dataclass(frozen=True)
class QuestionInput:
    prompt: str
    answers: list[AnswerInput]
    explanation: str | None = None
    points: int = 1


@dataclass
class ArticleFilters:
    category_id: UUID | None = None
    level: str | None = None
    available_only: bool = True
    limit: int = 50
    offset: int = field(default=0)


def _invalid(message: str) -> ApiError:
    return ApiError(422, "VALIDATION_FAILED", message)


def estimate_reading_minutes(content: str) -> int:
    """Minutes needed to read `content`, at least 1 and at most `MAX_READING_MINUTES`."""
    words = len(content.split())
    return max(1, min(MAX_READING_MINUTES, -(-words // WORDS_PER_MINUTE)))


def _slug(value: str) -> str:
    value = value.strip()
    if not SLUG_RE.fullmatch(value) or len(value) > 120:
        raise _invalid("slug must be lowercase letters, digits and single hyphens")
    return value


def _text(value: str, name: str, max_length: int) -> str:
    value = value.strip()
    if not value:
        raise _invalid(f"{name} must not be empty")
    if len(value) > max_length:
        raise _invalid(f"{name} must be at most {max_length} characters")
    return value


def _level(value: str) -> str:
    if value not in READING_LEVELS:
        raise _invalid(f"level must be one of {', '.join(READING_LEVELS)}")
    return value


def _cover(url: str | None) -> str | None:
    if url is None or not url.strip():
        return None
    url = url.strip()
    # Only https images or same-origin paths: never javascript:/data: URLs.
    is_path = url.startswith("/") and not url.startswith("//")
    if len(url) > 500 or not (is_path or url.startswith("https://")):
        raise _invalid("cover_image_url must be an https URL or a site-relative path")
    return url


def _minutes(value: int | None, content: str) -> int:
    if value is None:
        return estimate_reading_minutes(content)
    if not 1 <= value <= MAX_READING_MINUTES:
        raise _invalid(f"reading_minutes must be between 1 and {MAX_READING_MINUTES}")
    return value


def validate_questions(questions: list[QuestionInput]) -> None:
    """Each question: text, 2-6 distinct answers, exactly one correct, points 1-10."""
    for number, question in enumerate(questions, start=1):
        label = f"question {number}"
        _text(question.prompt, f"{label} prompt", 2000)
        if not 1 <= question.points <= 10:
            raise _invalid(f"{label} points must be between 1 and 10")
        if not 2 <= len(question.answers) <= 6:
            raise _invalid(f"{label} needs 2 to 6 answers")
        texts = [_text(a.text, f"{label} answer", 500).casefold() for a in question.answers]
        if len(set(texts)) != len(texts):
            raise _invalid(f"{label} has duplicate answers")
        if sum(a.is_correct for a in question.answers) != 1:
            raise _invalid(f"{label} must have exactly one correct answer")


def _build_questions(questions: list[QuestionInput]) -> list[ReadingQuestion]:
    return [
        ReadingQuestion(
            position=i,
            prompt=q.prompt.strip(),
            explanation=(q.explanation or "").strip() or None,
            points=q.points,
            answers=[
                ReadingAnswer(position=j, text=a.text.strip(), is_correct=a.is_correct)
                for j, a in enumerate(q.answers, start=1)
            ],
        )
        for i, q in enumerate(questions, start=1)
    ]


# --- categories -------------------------------------------------------------------------


async def create_category(
    db: AsyncSession,
    *,
    slug: str,
    title: str,
    description: str = "",
    position: int = 0,
    is_active: bool = True,
) -> ReadingCategory:
    category = ReadingCategory(
        slug=_slug(slug),
        title=_text(title, "title", 120),
        description=description.strip()[:500],
        position=position,
        is_active=is_active,
    )
    db.add(category)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ApiError(409, "CONFLICT", "A category with this slug already exists") from None
    return category


async def update_category(
    db: AsyncSession,
    category: ReadingCategory,
    *,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    is_active: bool | None = None,
) -> ReadingCategory:
    if title is not None:
        category.title = _text(title, "title", 120)
    if description is not None:
        category.description = description.strip()[:500]
    if position is not None:
        category.position = position
    if is_active is not None:
        category.is_active = is_active
    await db.commit()
    return category


async def list_categories(db: AsyncSession, *, active_only: bool = True) -> list[ReadingCategory]:
    statement = select(ReadingCategory).order_by(ReadingCategory.position, ReadingCategory.title)
    if active_only:
        statement = statement.where(ReadingCategory.is_active.is_(True))
    return list((await db.scalars(statement)).all())


async def get_category(db: AsyncSession, category_id: UUID) -> ReadingCategory | None:
    return await db.get(ReadingCategory, category_id)


# --- articles ---------------------------------------------------------------------------


async def create_article(
    db: AsyncSession,
    *,
    category_id: UUID,
    slug: str,
    title: str,
    description: str,
    content: str,
    level: str,
    reading_minutes: int | None = None,
    cover_image_url: str | None = None,
    cover_alt: str | None = None,
    questions: list[QuestionInput] | None = None,
) -> ReadingArticle:
    """Create a **draft** article (publish it with `set_status`)."""
    if await db.get(ReadingCategory, category_id) is None:
        raise ApiError(404, "NOT_FOUND", "Category not found")
    questions = questions or []
    validate_questions(questions)
    content = _text(content, "content", 100_000)
    article = ReadingArticle(
        category_id=category_id,
        slug=_slug(slug),
        title=_text(title, "title", 200),
        description=_text(description, "description", 500),
        content=content,
        level=_level(level),
        reading_minutes=_minutes(reading_minutes, content),
        cover_image_url=_cover(cover_image_url),
        cover_alt=(cover_alt or "").strip()[:200] or None,
        status="draft",
        questions=_build_questions(questions),
    )
    db.add(article)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ApiError(409, "CONFLICT", "An article with this slug already exists") from None
    return await _load(db, article.id)


async def _load(db: AsyncSession, article_id: UUID) -> ReadingArticle:
    article = await db.scalar(
        select(ReadingArticle)
        .where(ReadingArticle.id == article_id)
        .options(
            selectinload(ReadingArticle.category),
            selectinload(ReadingArticle.questions).selectinload(ReadingQuestion.answers),
        )
        .execution_options(populate_existing=True)
    )
    if article is None:
        raise ApiError(404, "NOT_FOUND", "Article not found")
    return article


async def update_article(
    db: AsyncSession,
    article: ReadingArticle,
    *,
    category_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
    content: str | None = None,
    level: str | None = None,
    reading_minutes: int | None = None,
    cover_image_url: str | None = None,
    cover_alt: str | None = None,
) -> ReadingArticle:
    """Partial update; `None` keeps the current value. Slug and status are not editable here."""
    if category_id is not None and category_id != article.category_id:
        if await db.get(ReadingCategory, category_id) is None:
            raise ApiError(404, "NOT_FOUND", "Category not found")
        article.category_id = category_id
    if title is not None:
        article.title = _text(title, "title", 200)
    if description is not None:
        article.description = _text(description, "description", 500)
    if content is not None:
        article.content = _text(content, "content", 100_000)
        if reading_minutes is None:
            article.reading_minutes = estimate_reading_minutes(article.content)
    if level is not None:
        article.level = _level(level)
    if reading_minutes is not None:
        article.reading_minutes = _minutes(reading_minutes, article.content)
    if cover_image_url is not None:
        article.cover_image_url = _cover(cover_image_url)
    if cover_alt is not None:
        article.cover_alt = cover_alt.strip()[:200] or None
    await db.commit()
    return await _load(db, article.id)


async def replace_questions(
    db: AsyncSession, article: ReadingArticle, questions: list[QuestionInput]
) -> ReadingArticle:
    """Replace the whole quiz. Past attempts keep their frozen result snapshots."""
    validate_questions(questions)
    article = await _load(db, article.id)
    # Delete first: new rows reuse positions 1..n, so they must not coexist with the old ones.
    article.questions.clear()
    await db.flush()
    article.questions = _build_questions(questions)
    await db.commit()
    return await _load(db, article.id)


async def set_status(db: AsyncSession, article: ReadingArticle, status: str) -> ReadingArticle:
    """Move an article between draft, published and archived.

    Publishing needs a complete article (content, active category) and a valid quiz.
    `published_at` is set the first time only.
    """
    if status not in READING_ARTICLE_STATUSES:
        raise _invalid(f"status must be one of {', '.join(READING_ARTICLE_STATUSES)}")
    if status == "published":
        article = await _load(db, article.id)
        if not article.category.is_active:
            raise ApiError(409, "CONFLICT", "Cannot publish into an inactive category")
        validate_questions(
            [
                QuestionInput(
                    q.prompt,
                    [AnswerInput(a.text, a.is_correct) for a in q.answers],
                    q.explanation,
                    q.points,
                )
                for q in article.questions
            ]
        )
        if article.published_at is None:
            article.published_at = datetime.now(UTC)
    article.status = status
    await db.commit()
    return await _load(db, article.id)


async def get_article(
    db: AsyncSession,
    *,
    article_id: UUID | None = None,
    slug: str | None = None,
    available_only: bool = True,
) -> ReadingArticle | None:
    """One article with category and quiz, or `None` (also when hidden from learners)."""
    statement = select(ReadingArticle.id)
    if article_id is not None:
        statement = statement.where(ReadingArticle.id == article_id)
    elif slug is not None:
        statement = statement.where(ReadingArticle.slug == slug)
    else:
        raise ValueError("article_id or slug is required")
    if available_only:
        statement = statement.where(*available_clauses())
    found = await db.scalar(statement)
    return await _load(db, found) if found else None


def available_clauses() -> tuple:
    """SQL conditions for 'visible to learners'; the query must join the category."""
    return (
        ReadingArticle.status == "published",
        ReadingArticle.category_id.in_(
            select(ReadingCategory.id).where(ReadingCategory.is_active.is_(True))
        ),
    )


async def list_articles(
    db: AsyncSession, filters: ArticleFilters | None = None
) -> list[ReadingArticle]:
    """Articles newest-published first (drafts by creation), without loading quizzes."""
    f = filters or ArticleFilters()
    if f.level is not None:
        _level(f.level)
    if not 1 <= f.limit <= 200 or f.offset < 0:
        raise _invalid("limit must be 1-200 and offset must not be negative")
    statement = select(ReadingArticle).options(selectinload(ReadingArticle.category))
    if f.available_only:
        statement = statement.where(*available_clauses())
    if f.category_id is not None:
        statement = statement.where(ReadingArticle.category_id == f.category_id)
    if f.level is not None:
        statement = statement.where(ReadingArticle.level == f.level)
    statement = (
        statement.order_by(
            ReadingArticle.published_at.desc().nulls_last(),
            ReadingArticle.created_at.desc(),
            ReadingArticle.id,
        )
        .limit(f.limit)
        .offset(f.offset)
    )
    return list((await db.scalars(statement)).all())
