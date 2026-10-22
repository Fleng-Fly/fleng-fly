"""Bounded learning analytics. Never includes email, names, tokens or answer keys."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import (
    Course,
    Exercise,
    ExerciseSubmission,
    Lesson,
    LessonProgress,
    Progress,
    User,
    VocabularyItem,
)


async def lesson_context(db: AsyncSession, lesson_id: UUID) -> dict:
    lesson = await db.scalar(
        select(Lesson)
        .join(Course)
        .where(Lesson.id == lesson_id, Lesson.is_published.is_(True), Course.is_published.is_(True))
    )
    if lesson is None:
        raise ApiError(404, "NOT_FOUND", "Lesson not found")
    return {
        "title": lesson.title[:200],
        "summary": lesson.summary[:1000],
        "theory": lesson.theory[:3000],
    }


async def learner_context(db: AsyncSession, user: User, lesson_id: UUID | None = None) -> dict:
    missed = (
        await db.execute(
            select(Lesson.slug, Lesson.title, func.count(ExerciseSubmission.id))
            .join(Exercise, Exercise.lesson_id == Lesson.id)
            .join(ExerciseSubmission, ExerciseSubmission.exercise_id == Exercise.id)
            .join(Course, Lesson.course_id == Course.id)
            .where(
                ExerciseSubmission.user_id == user.id,
                ExerciseSubmission.is_correct.is_(False),
                Lesson.is_published.is_(True),
                Course.is_published.is_(True),
            )
            .group_by(Lesson.id)
            .order_by(func.count(ExerciseSubmission.id).desc(), Lesson.slug)
            .limit(5)
        )
    ).all()
    completed = (
        await db.scalars(
            select(Lesson.slug)
            .join(LessonProgress)
            .where(LessonProgress.user_id == user.id, LessonProgress.status == "completed")
            .order_by(LessonProgress.completed_at.desc())
            .limit(10)
        )
    ).all()
    weak_words = (
        await db.scalars(
            select(VocabularyItem.word)
            .where(VocabularyItem.user_id == user.id, VocabularyItem.learned.is_(False))
            .order_by(VocabularyItem.due_at)
            .limit(10)
        )
    ).all()
    progress = await db.scalar(select(Progress).where(Progress.user_id == user.id))
    result: dict = {
        "level": user.profile.english_level if user.profile else "A1",
        "preferred_language": user.profile.preferred_language if user.profile else "English",
        "completed_lessons": list(completed),
        "missed_topics": [
            {"slug": slug, "topic": title[:200], "missed": count} for slug, title, count in missed
        ],
        "vocabulary_to_review": list(weak_words),
        "last_activity": progress.last_activity_at.isoformat()
        if progress and progress.last_activity_at
        else None,
    }
    if lesson_id:
        result["lesson"] = await lesson_context(db, lesson_id)
    return result


async def recommendations(db: AsyncSession, user: User) -> dict:
    context = await learner_context(db, user)
    completed = select(LessonProgress.lesson_id).where(
        LessonProgress.user_id == user.id, LessonProgress.status == "completed"
    )
    next_lessons = (
        await db.execute(
            select(Lesson.slug, Lesson.title)
            .join(Course)
            .where(
                Course.is_published.is_(True),
                Lesson.is_published.is_(True),
                Course.level == context["level"],
                Lesson.id.not_in(completed),
            )
            .order_by(Course.position, Lesson.position, Lesson.slug)
            .limit(3)
        )
    ).all()
    return {
        "level": context["level"],
        "reviewTopics": context["missed_topics"],
        "reviewWords": context["vocabulary_to_review"],
        "nextLessons": [{"slug": slug, "title": title} for slug, title in next_lessons],
        "reason": "Review incorrect submissions and unlearned words, then continue your level.",
    }
