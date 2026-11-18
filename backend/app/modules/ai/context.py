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
from app.modules.exercises.instructions import instruction_for


async def lesson_context(db: AsyncSession, lesson_id: UUID) -> dict:
    lesson = await db.scalar(
        select(Lesson)
        .join(Course)
        .where(Lesson.id == lesson_id, Lesson.is_published.is_(True), Course.is_published.is_(True))
    )
    if lesson is None:
        raise ApiError(404, "NOT_FOUND", "Lesson not found")
    course = await db.scalar(select(Course).where(Course.id == lesson.course_id))
    return {
        "id": str(lesson.id),
        "slug": lesson.slug,
        "level": course.level if course else None,
        "course": {"id": str(lesson.course_id), "title": course.title[:200] if course else ""},
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
        try:
            result["lesson"] = await lesson_context(db, lesson_id)
        except ApiError:
            # Invalid/unpublished context never reaches the provider; general tutoring works.
            return result
        current = await db.scalar(
            select(LessonProgress).where(
                LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
            )
        )
        result["lesson"]["progress"] = current.status if current else "not_started"
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


async def exercise_context(
    db: AsyncSession, user: User, exercise: Exercise, current_answer: str | None
) -> dict:
    """What the learner sees for one exercise, plus their own answer/attempts.

    Never includes answer keys (`correct_option_id`, `accepted_answers`, `model_answer`)
    or the authored explanation, so the tutor teaches instead of revealing the answer.
    """
    options = {str(o["id"]): str(o["text"])[:300] for o in (exercise.options or [])}
    submission = await db.scalar(
        select(ExerciseSubmission).where(
            ExerciseSubmission.user_id == user.id, ExerciseSubmission.exercise_id == exercise.id
        )
    )

    def readable(answer: str | None) -> str | None:
        if not answer or not answer.strip():
            return None
        # Choice answers are option ids; give the tutor the text the learner picked.
        return options.get(answer, answer)[:2000]

    return {
        "id": str(exercise.id),
        "position": exercise.position,
        "type": "letter_tiles" if exercise.letter_tiles else exercise.type,
        "instruction": instruction_for(exercise).en,
        "prompt": exercise.prompt[:2000],
        "options": list(options.values()) or None,
        "current_answer": readable(current_answer),
        "attempts": submission.attempts if submission else 0,
        "last_checked_answer": readable(submission.answer) if submission else None,
        "last_checked_correct": submission.is_correct if submission else None,
    }
