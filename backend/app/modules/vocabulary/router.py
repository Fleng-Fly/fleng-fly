from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Course, Lesson, User, VocabularyItem, VocabularyReview
from app.db.session import get_db
from app.modules.gamification.service import lock_learner
from app.modules.vocabulary import flashcards, service
from app.modules.vocabulary.schemas import (
    CefrLevel,
    CourseWordResponse,
    DictionaryGroupsResponse,
    FlashcardCreate,
    FlashcardResponse,
    ReviewRequest,
    ReviewResponse,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyStatsResponse,
    VocabularyUpdate,
)

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("/course-words", response_model=list[CourseWordResponse])
async def course_words(
    course_id: UUID | None = Query(None, alias="courseId"),
    level: CefrLevel | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = await flashcards.course_query(db, course_id, level)
    items = (await db.scalars(query.limit(limit).offset(offset))).all()
    lessons = {
        row.id: row
        for row in (
            await db.execute(
                select(Lesson.id, Lesson.slug, Lesson.title).where(
                    Lesson.id.in_({i.lesson_id for i in items if i.lesson_id})
                )
            )
        ).all()
    }
    result = []
    for item in items:
        data = CourseWordResponse.model_validate(item, from_attributes=True)
        lesson = lessons.get(item.lesson_id) if item.lesson_id else None
        if lesson is not None:
            data.lesson_slug, data.lesson_title = lesson.slug, lesson.title
        result.append(data)
    return result


@router.post("/flashcards/sessions", response_model=FlashcardResponse, status_code=201)
async def create_flashcards(
    payload: FlashcardCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return flashcards.response(await flashcards.create(db, user.id, payload))


@router.get("/flashcards/sessions/{session_id}", response_model=FlashcardResponse)
async def get_flashcards(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return flashcards.response(await flashcards.owned(db, user.id, session_id))


@router.post("/flashcards/sessions/{session_id}/complete", response_model=FlashcardResponse)
async def complete_flashcards(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return flashcards.response(await flashcards.complete(db, user.id, session_id))


@router.get("/flashcards/sessions/{session_id}/test-words", response_model=FlashcardResponse)
async def flashcards_test_words(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await flashcards.words_for_test(db, user.id, session_id)


@router.get("/stats", response_model=VocabularyStatsResponse)
async def vocabulary_stats(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> VocabularyStatsResponse:
    """Count the caller's saved words marked learned, without paging through the list."""
    await service.sync_completed_lessons(db, user.id)
    mine = VocabularyItem.user_id == user.id
    learned = await db.scalar(
        select(func.count())
        .select_from(VocabularyItem)
        .where(mine, VocabularyItem.learned.is_(True))
    )
    total = await db.scalar(select(func.count()).select_from(VocabularyItem).where(mine))
    due = await db.scalar(
        select(func.count())
        .select_from(VocabularyItem)
        .where(mine, VocabularyItem.due_at <= datetime.now(UTC))
    )
    return VocabularyStatsResponse(
        words_learned=int(learned or 0), total_words=int(total or 0), due_words=int(due or 0)
    )


@router.get("/groups", response_model=DictionaryGroupsResponse)
async def dictionary_groups(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Courses and lessons the learner's words come from, with counts."""
    await service.sync_completed_lessons(db, user.id)
    return await service.groups(db, user.id)


@router.get("", response_model=list[VocabularyResponse])
async def list_words(
    response: Response,
    due: bool = False,
    learned: bool | None = None,
    q: str | None = Query(None, max_length=100, description="Search word or translation"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    lesson_id: UUID | None = Query(None, alias="lessonId"),
    course_id: UUID | None = Query(None, alias="courseId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The personal dictionary across all courses. `X-Total-Count` has the filtered total."""
    await service.sync_completed_lessons(db, user.id)
    query = select(VocabularyItem).where(VocabularyItem.user_id == user.id)
    if lesson_id is not None:
        query = query.where(VocabularyItem.lesson_id == lesson_id)
    if course_id is not None:
        query = query.where(VocabularyItem.course_id == course_id)
    if learned is not None:
        query = query.where(VocabularyItem.learned.is_(learned))
    if q and q.strip():
        query = service.search_filter(query, q)
    if due:
        query = query.where(VocabularyItem.due_at <= datetime.now(UTC))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    response.headers["X-Total-Count"] = str(int(total or 0))
    items = (
        await db.scalars(
            query.order_by(VocabularyItem.created_at, VocabularyItem.id).limit(limit).offset(offset)
        )
    ).all()
    course_titles = dict(
        (
            await db.execute(
                select(Course.id, Course.title).where(
                    Course.id.in_({i.course_id for i in items if i.course_id})
                )
            )
        ).all()
    )
    lessons = {
        row.id: row
        for row in (
            await db.execute(
                select(Lesson.id, Lesson.slug, Lesson.title).where(
                    Lesson.id.in_({i.lesson_id for i in items if i.lesson_id})
                )
            )
        ).all()
    }
    result = []
    for item in items:
        data = VocabularyResponse.model_validate(item, from_attributes=True)
        data.course_title = course_titles.get(item.course_id) if item.course_id else None
        lesson = lessons.get(item.lesson_id) if item.lesson_id else None
        if lesson is not None:
            data.lesson_slug, data.lesson_title = lesson.slug, lesson.title
        result.append(data)
    return result


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
