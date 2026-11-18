"""The learner's personal dictionary: manual words, lesson words and reviews.

Words from every course live in one list (`VocabularyItem`, unique per learner and
word). Finishing a lesson copies that lesson's curated words (`CourseVocabularyItem`)
into the list; the copy is idempotent, so repeating or retrying a lesson never
duplicates a word and a failed request leaves nothing half-written.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import (
    Course,
    CourseVocabularyItem,
    Lesson,
    LessonProgress,
    User,
    VocabularyItem,
    VocabularyReview,
)
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
    if payload.lesson_id:
        item.course_id = await db.scalar(
            select(Lesson.course_id).where(Lesson.id == item.lesson_id)
        )
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
    # Basic two-step policy. The scheduling state is stored so a smarter scheduler can
    # replace these two lines without a schema change.
    now = datetime.now(UTC)
    item.interval_days = 7 if remembered else 1
    item.repetitions = item.repetitions + 1 if remembered else 0
    item.last_reviewed_at = now
    item.due_at = now + timedelta(days=item.interval_days)
    db.add(VocabularyReview(item_id=item.id, remembered=remembered))
    await record_activity(db, user.id)
    await db.commit()
    return item


def _missing_lesson_words(user_id: UUID, lesson_id: UUID | None) -> Select:
    """Curated words of the learner's completed lessons that are not in their list yet."""
    query = (
        select(CourseVocabularyItem, Lesson.course_id)
        .join(Lesson, CourseVocabularyItem.lesson_id == Lesson.id)
        .join(
            LessonProgress,
            (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user_id),
        )
        .where(
            LessonProgress.status == "completed",
            ~exists().where(
                VocabularyItem.user_id == user_id, VocabularyItem.word == CourseVocabularyItem.word
            ),
        )
        .order_by(Lesson.position, CourseVocabularyItem.word)
    )
    if lesson_id is not None:
        query = query.where(Lesson.id == lesson_id)
    return query


async def collect_lesson_words(
    db: AsyncSession, user_id: UUID, lesson_id: UUID | None = None
) -> int:
    """Add the words of completed lesson(s) to the learner's dictionary; return how many.

    Runs in the caller's transaction and does not commit. Existing words (from any
    course, or added by hand) are left untouched, and a concurrent insert of the same
    word is ignored by the database, so the call is safe to repeat.
    """
    missing = (await db.execute(_missing_lesson_words(user_id, lesson_id))).all()
    if not missing:
        return 0
    now = datetime.now(UTC)
    rows = [
        {
            "id": uuid4(),
            "user_id": user_id,
            "lesson_id": word.lesson_id,
            "course_id": course_id,
            "word": word.word.casefold(),
            "translation": word.translation,
            "example": word.example,
            "pronunciation": word.pronunciation,
            "source": "lesson",
            "learned": False,
            "interval_days": 0,
            "repetitions": 0,
            "due_at": now,
            # Keep the lesson's order when the list is sorted by creation time.
            "created_at": now + timedelta(microseconds=index),
        }
        for index, (word, course_id) in enumerate(missing)
    ]
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    for start in range(0, len(rows), 100):
        await db.execute(
            insert(VocabularyItem)
            .values(rows[start : start + 100])
            .on_conflict_do_nothing(index_elements=["user_id", "word"])
        )
    return len(rows)


async def sync_completed_lessons(db: AsyncSession, user_id: UUID) -> None:
    """Self-heal: collect words for lessons completed before this feature existed.

    Reads first and only takes the learner lock when there is something to write, so a
    normal dictionary view stays read-only.
    """
    if (await db.execute(_missing_lesson_words(user_id, None).limit(1))).first() is None:
        return
    await lock_learner(db, user_id)
    await collect_lesson_words(db, user_id)
    await db.commit()


def search_filter(query: Select, text: str) -> Select:
    """Match the English word or the translation. Case-insensitive for any script:
    SQLite folds only ASCII, so common case variants are tried explicitly."""
    needle = text.strip()
    variants = {needle, needle.casefold(), needle.upper(), needle.capitalize()}
    return query.where(
        or_(
            VocabularyItem.word.contains(needle.casefold(), autoescape=True),
            *(VocabularyItem.translation.contains(v, autoescape=True) for v in variants),
        )
    )


async def groups(db: AsyncSession, user_id: UUID) -> dict:
    """Courses and lessons that hold the learner's words, with counts (for filters)."""
    rows = (
        await db.execute(
            select(
                VocabularyItem.course_id,
                VocabularyItem.lesson_id,
                func.count(VocabularyItem.id),
            )
            .where(VocabularyItem.user_id == user_id)
            .group_by(VocabularyItem.course_id, VocabularyItem.lesson_id)
        )
    ).all()
    course_ids = {r[0] for r in rows if r[0]}
    lesson_ids = {r[1] for r in rows if r[1]}
    course_rows = {
        c.id: c for c in (await db.scalars(select(Course).where(Course.id.in_(course_ids)))).all()
    }
    lessons = {
        item.id: item
        for item in (await db.scalars(select(Lesson).where(Lesson.id.in_(lesson_ids)))).all()
    }
    result: dict[UUID, dict] = {}
    other = total = 0
    for course_id, lesson_id, count in rows:
        total += count
        course = course_rows.get(course_id) if course_id else None
        if course is None:
            other += count
            continue
        entry = result.setdefault(
            course.id,
            {
                "id": course.id,
                "slug": course.slug,
                "title": course.title,
                "level": course.level,
                "position": course.position,
                "count": 0,
                "lessons": [],
            },
        )
        entry["count"] += count
        lesson = lessons.get(lesson_id) if lesson_id else None
        if lesson is not None:
            entry["lessons"].append(
                {
                    "id": lesson.id,
                    "slug": lesson.slug,
                    "title": lesson.title,
                    "position": lesson.position,
                    "count": count,
                }
            )
    ordered = sorted(result.values(), key=lambda c: (c["position"], c["title"]))
    for group in ordered:
        group["lessons"].sort(key=lambda item: item["position"])
    return {"total": total, "courses": ordered, "other": other}
