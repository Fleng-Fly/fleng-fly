"""Vocabulary selection and owned, persistent flashcard-to-test handoff."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, true, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Course, CourseVocabularyItem, FlashcardSession, VocabularyItem
from app.modules.vocabulary.schemas import FlashcardCreate, FlashcardResponse


async def course_query(
    db: AsyncSession, course_id: UUID | None, level: str | None, *, include_drafts: bool = False
):
    if (
        course_id is not None
        and await db.scalar(
            select(Course.id).where(
                Course.id == course_id,
                (true() if include_drafts else Course.is_published.is_(True)),
            )
        )
        is None
    ):
        raise ApiError(404, "NOT_FOUND", "Course not found")
    query = (
        select(CourseVocabularyItem)
        .join(Course)
        .where(true() if include_drafts else Course.is_published.is_(True))
    )
    if course_id is not None:
        query = query.where(Course.id == course_id)
    if level is not None:
        query = query.where(Course.level == level)
    return query.order_by(CourseVocabularyItem.word, CourseVocabularyItem.id)


async def create(db: AsyncSession, user_id: UUID, payload: FlashcardCreate) -> FlashcardSession:
    if payload.source == "my_words":
        if payload.course_id is not None or payload.level is not None:
            raise ApiError(
                400, "INVALID_SOURCE_FILTER", "Personal words do not accept course filters"
            )
        query = (
            select(VocabularyItem)
            .where(VocabularyItem.user_id == user_id)
            .order_by(VocabularyItem.created_at, VocabularyItem.id)
        )
    else:
        if payload.course_id is None and payload.level is None:
            raise ApiError(400, "MISSING_COURSE_FILTER", "Provide courseId or level")
        query = await course_query(db, payload.course_id, payload.level)
    words = (await db.scalars(query.limit(10))).all()
    session = FlashcardSession(
        user_id=user_id,
        source=payload.source,
        status="active" if words else "empty",
        cards=[
            {
                "wordId": str(w.id),
                "word": w.word,
                "translation": w.translation,
                "example": w.example,
            }
            for w in words
        ],
    )
    db.add(session)
    await db.commit()
    return session


async def owned(db: AsyncSession, user_id: UUID, session_id: UUID) -> FlashcardSession:
    session = await db.scalar(
        select(FlashcardSession)
        .where(FlashcardSession.id == session_id, FlashcardSession.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    if session is None:
        raise ApiError(404, "NOT_FOUND", "Flashcard session not found")
    return session


async def complete(db: AsyncSession, user_id: UUID, session_id: UUID) -> FlashcardSession:
    session = await owned(db, user_id, session_id)
    if session.status == "empty":
        raise ApiError(400, "EMPTY_SESSION", "An empty set cannot start a test")
    await db.execute(
        update(FlashcardSession)
        .where(
            FlashcardSession.id == session_id,
            FlashcardSession.user_id == user_id,
            FlashcardSession.status == "active",
        )
        .values(status="completed", completed_at=datetime.now(UTC))
    )
    await db.commit()
    return await owned(db, user_id, session_id)


def response(session: FlashcardSession) -> FlashcardResponse:
    return FlashcardResponse.model_validate(
        {
            "session_id": session.id,
            "source": session.source,
            "status": session.status,
            "total": len(session.cards),
            "cards": session.cards,
            "test_ready": session.status == "completed",
        }
    )


async def words_for_test(db: AsyncSession, user_id: UUID, session_id: UUID) -> FlashcardResponse:
    """Testing must call this with the JWT user, never a client-supplied owner."""
    session = await owned(db, user_id, session_id)
    if session.status != "completed":
        raise ApiError(409, "FLASHCARDS_NOT_COMPLETED", "Complete flashcards before testing")
    return response(session)
