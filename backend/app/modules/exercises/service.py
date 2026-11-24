"""Exercise submission, grading and per-lesson progress.

Rules (also documented in `docs/database.md`):

- An exercise is **completed** when:
  - `single_choice` / `text`: the learner has submitted a *correct* answer at
    least once;
  - `self_check`: the learner has marked an answer as correct (the server
    records the learner's assessment).
- **XP** equals the exercise's `points`, awarded once per `(user, exercise)` on
  the first time the exercise becomes completed. A conditional `UPDATE` on
  `exercise_submissions.xp_awarded` guarantees this at the database level, so
  retries cannot farm XP.
- A lesson is **completed** when it has at least one exercise and every exercise
  is completed. Opening a lesson only moves it to `in_progress`; a lesson with no
  exercises is never auto-completed. The `in_progress -> completed` transition
  happens at most once, so aggregate counters cannot double-count.
"""

from collections import Counter
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, func, select, true, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import (
    Course,
    Exercise,
    ExerciseSubmission,
    Lesson,
    LessonProgress,
    User,
)
from app.modules.exercises import grading, guidance
from app.modules.exercises.guidance import LocalizedText
from app.modules.exercises.instructions import instruction_for
from app.modules.exercises.schemas import (
    ExerciseOptionResponse,
    ExercisePublicResponse,
    LessonExerciseStateResponse,
    LessonProgressResponse,
    LetterTilesResponse,
    SubmissionResultResponse,
)
from app.modules.gamification.service import lock_learner, record_activity
from app.modules.progress import service as progress_service
from app.modules.vocabulary.service import collect_lesson_words


def _not_found(message: str) -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def _invalid(message: str) -> ApiError:
    return ApiError(422, "INVALID_ANSWER", message)


async def get_published_lesson(
    db: AsyncSession, slug: str, *, include_drafts: bool = False
) -> tuple[Lesson, Course] | None:
    """Return a published lesson of a published course, or `None`."""
    row = (
        await db.execute(
            select(Lesson, Course)
            .join(Course, Lesson.course_id == Course.id)
            .where(
                Lesson.slug == slug,
                (true() if include_drafts else Lesson.is_published.is_(True)),
                (true() if include_drafts else Course.is_published.is_(True)),
            )
        )
    ).first()
    if row is None:
        return None
    lesson, course = row
    return lesson, course


async def get_lesson_or_404(
    db: AsyncSession, slug: str, *, include_drafts: bool = False
) -> tuple[Lesson, Course]:
    result = await get_published_lesson(db, slug, include_drafts=include_drafts)
    if result is None:
        raise _not_found("Lesson not found")
    return result


async def get_exercise_or_404(db: AsyncSession, lesson: Lesson, exercise_id: UUID) -> Exercise:
    """Resolve an exercise that belongs to `lesson`, or raise `404`.

    An exercise from another lesson is reported as not found so the API never
    reveals (or lets a learner submit against) another lesson's content.
    """
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if exercise is None or exercise.lesson_id != lesson.id:
        raise _not_found("Exercise not found")
    return exercise


async def list_exercises(db: AsyncSession, lesson_id: UUID) -> list[Exercise]:
    result = await db.execute(
        select(Exercise)
        .where(Exercise.lesson_id == lesson_id)
        .order_by(Exercise.position, Exercise.slug)
    )
    return list(result.scalars().all())


def to_public_exercise(exercise: Exercise) -> ExercisePublicResponse:
    options = None
    if exercise.type == "single_choice":
        options = [
            ExerciseOptionResponse(id=str(option["id"]), text=str(option["text"]))
            for option in (exercise.options or [])
        ]
    return ExercisePublicResponse(
        id=exercise.id,
        slug=exercise.slug,
        position=exercise.position,
        type=exercise.type,
        prompt=exercise.prompt,
        points=exercise.points,
        options=options,
        letter_tiles=(
            LetterTilesResponse.model_validate(exercise.letter_tiles)
            if exercise.type == "text" and exercise.letter_tiles
            else None
        ),
        hint=guidance.hint_for(exercise.slug),
        instruction=instruction_for(exercise),
    )


async def list_public_exercises(db: AsyncSession, lesson_id: UUID) -> list[ExercisePublicResponse]:
    return [to_public_exercise(exercise) for exercise in await list_exercises(db, lesson_id)]


async def _submissions_by_exercise(
    db: AsyncSession, user_id: UUID, exercise_ids: list[UUID]
) -> dict[UUID, ExerciseSubmission]:
    if not exercise_ids:
        return {}
    rows = (
        (
            await db.execute(
                select(ExerciseSubmission).where(
                    ExerciseSubmission.user_id == user_id,
                    ExerciseSubmission.exercise_id.in_(exercise_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    return {row.exercise_id: row for row in rows}


async def _get_or_create_lesson_progress(
    db: AsyncSession, user_id: UUID, lesson: Lesson
) -> LessonProgress:
    record = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson.id
        )
    )
    if record is None:
        record = LessonProgress(user_id=user_id, lesson_id=lesson.id, status="in_progress")
        db.add(record)
        aggregate = await progress_service.get_or_create_progress(db, user_id)
        aggregate.lessons_started += 1
        await db.flush()
    return record


async def _get_or_create_submission(
    db: AsyncSession, user_id: UUID, exercise: Exercise
) -> ExerciseSubmission:
    submission = await db.scalar(
        select(ExerciseSubmission).where(
            ExerciseSubmission.user_id == user_id,
            ExerciseSubmission.exercise_id == exercise.id,
        )
    )
    if submission is None:
        submission = ExerciseSubmission(user_id=user_id, exercise_id=exercise.id, attempts=0)
        db.add(submission)
        await db.flush()
    return submission


async def build_lesson_progress(
    db: AsyncSession, user_id: UUID, lesson: Lesson, record: LessonProgress | None
) -> LessonProgressResponse:
    exercises = await list_exercises(db, lesson.id)
    submissions = await _submissions_by_exercise(
        db, user_id, [exercise.id for exercise in exercises]
    )

    states: list[LessonExerciseStateResponse] = []
    unattempted: list[UUID] = []
    completed_count = 0
    xp_earned = 0
    for exercise in exercises:
        submission = submissions.get(exercise.id)
        completed = bool(submission and submission.completed)
        if completed:
            completed_count += 1
            xp_earned += exercise.points
        if not submission or not submission.attempts:
            unattempted.append(exercise.id)
        first = first_result(submission)
        states.append(
            LessonExerciseStateResponse(
                exercise_id=exercise.id,
                completed=completed,
                is_correct=submission.is_correct if submission else None,
                attempts=submission.attempts if submission else 0,
                points_awarded=exercise.points if completed else 0,
                answer=submission.answer if submission else None,
                first_answer=first.get("answer"),
                first_outcome=first.get("outcome"),
                expected_answer=(
                    review_answer(exercise)
                    if first.get("outcome") in {"incorrect", "skipped"}
                    else None
                ),
            )
        )

    status = record.status if record else "in_progress"
    test_finished_at = None
    if record and exercises and not unattempted:
        test_finished_at = record.test_finished_at or max(
            submission.submitted_at.replace(tzinfo=UTC) for submission in submissions.values()
        )
    return LessonProgressResponse(
        lesson_slug=lesson.slug,
        lesson_title=lesson.title,
        status=status,
        completed=status == "completed",
        started_at=record.started_at if record else None,
        completed_at=record.completed_at if record else None,
        test_finished_at=test_finished_at,
        exercises_total=len(exercises),
        exercises_completed=completed_count,
        xp_earned=xp_earned,
        exercises=states,
        pending_exercise_ids=unattempted,
    )


def first_result(submission: ExerciseSubmission | None) -> dict[str, Any]:
    if submission is None:
        return {}
    if submission.first_result is not None:
        return submission.first_result
    if submission.attempts == 1 and submission.is_correct is not None:
        return {
            "answer": submission.answer,
            "outcome": "correct" if submission.is_correct else "incorrect",
        }
    return {}


def review_answer(exercise: Exercise) -> str | None:
    if exercise.type == "single_choice":
        return next(
            (
                option["text"]
                for option in exercise.options or []
                if str(option["id"]) == exercise.correct_option_id
            ),
            None,
        )
    return exercise.accepted_answers[0] if exercise.accepted_answers else exercise.model_answer


async def start_lesson(db: AsyncSession, user: User, lesson: Lesson) -> LessonProgressResponse:
    """Start or resume a lesson. Idempotent; never completes the lesson."""
    await lock_learner(db, user.id)
    if user.profile is not None:
        await db.refresh(user.profile)
    aggregate = await progress_service.get_or_create_progress(db, user.id)
    record = await _get_or_create_lesson_progress(db, user.id, lesson)
    aggregate.last_activity_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(record)
    return await build_lesson_progress(db, user.id, lesson, record)


async def get_lesson_progress(
    db: AsyncSession, user: User, lesson: Lesson
) -> LessonProgressResponse:
    record = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson.id
        )
    )
    return await build_lesson_progress(db, user.id, lesson, record)


def preview_self_check(exercise: Exercise, answer: str) -> str:
    if exercise.type != "self_check" or not exercise.model_answer:
        raise _invalid("This exercise has no model answer for self-checking")
    if not answer.strip():
        raise _invalid("Write an answer before self-checking")
    return exercise.model_answer


def _validate_answer(exercise: Exercise, answer: str, self_assessment: str | None) -> None:
    if exercise.type == "single_choice":
        if not answer or answer not in grading.option_ids(exercise):
            raise _invalid("Choose one of the available options")
    elif exercise.type == "text":
        if not answer.strip():
            raise _invalid("Write a short answer")
        if exercise.letter_tiles:
            pattern = exercise.letter_tiles["pattern"].casefold()
            word = answer.strip().casefold()
            if len(word) != len(pattern):
                raise _invalid("Fill every blank with a letter tile")
            pairs = list(zip(pattern, word, strict=True))
            used = Counter(letter for fixed, letter in pairs if fixed == "_")
            available = Counter(letter.casefold() for letter in exercise.letter_tiles["letters"])
            if used - available or any(fixed != "_" and fixed != letter for fixed, letter in pairs):
                raise _invalid("Use the available letter tiles and keep the given letters")
    elif exercise.type == "self_check":
        if not answer.strip():
            raise _invalid("Write an answer before self-checking")
        if self_assessment not in ("correct", "incorrect"):
            raise _invalid("Choose whether your answer was correct")
    else:  # pragma: no cover - guarded by the check constraint
        raise ApiError(422, "UNSUPPORTED_EXERCISE_TYPE", "Unsupported exercise type")


def _wrong_note(exercise: Exercise, answer: str, is_correct: bool | None) -> LocalizedText | None:
    """Why the selected option is wrong; only for a graded incorrect single choice."""
    if is_correct is not False or exercise.type != "single_choice":
        return None
    selected = next(
        (str(o["text"]) for o in (exercise.options or []) if str(o["id"]) == answer), None
    )
    return guidance.wrong_note_for(exercise.slug, selected) if selected else None


def _feedback(exercise: Exercise, is_correct: bool | None) -> str:
    if exercise.type == "self_check":
        if is_correct:
            return "Marked as correct. Compare with the model answer."
        return "Marked for practice. Compare with the model answer."
    if is_correct:
        return "Correct."
    return "Not quite. See the correct answer below."


async def submit_answer(
    db: AsyncSession,
    *,
    user: User,
    lesson: Lesson,
    exercise: Exercise,
    answer: str | None,
    self_assessment: str | None,
    expected_attempts: int | None = None,
) -> SubmissionResultResponse:
    """Grade and persist one submission, then recompute lesson progress."""
    if answer is None:
        if self_assessment is not None:
            raise _invalid("A skipped question cannot have a self-assessment")
    else:
        _validate_answer(exercise, answer, self_assessment)
    await lock_learner(db, user.id)
    if user.profile is not None:
        await db.refresh(user.profile)
    aggregate = await progress_service.get_or_create_progress(db, user.id)
    record = await _get_or_create_lesson_progress(db, user.id, lesson)
    submission = await _get_or_create_submission(db, user.id, exercise)
    if expected_attempts is not None and submission.attempts != expected_attempts:
        raise ApiError(409, "LESSON_ATTEMPT_CHANGED", "This exercise has a newer attempt")
    if expected_attempts and record.test_finished_at is None:
        progress = await build_lesson_progress(db, user.id, lesson, record)
        if progress.test_finished_at is None:
            raise ApiError(409, "LESSON_TEST_INCOMPLETE", "Finish the first pass before retrying")
        record.test_finished_at = progress.test_finished_at

    now = datetime.now(UTC)
    if answer is None:
        is_correct: bool | None = None
    elif exercise.type == "self_check":
        is_correct = self_assessment == "correct"
    else:
        is_correct = grading.grade_objective(exercise, answer)
    will_complete = bool(is_correct)

    if submission.attempts == 0:
        submission.first_result = {
            "answer": answer,
            "outcome": "skipped" if answer is None else "correct" if is_correct else "incorrect",
        }
    elif submission.first_result is None:
        submission.first_result = first_result(submission)
    submission.answer = answer
    submission.is_correct = is_correct
    submission.attempts += 1
    submission.submitted_at = now
    if will_complete and not submission.completed:
        submission.completed = True
    await db.flush()

    # Award XP at most once per submission row. The conditional UPDATE makes the
    # claim atomic, so concurrent or repeated requests cannot double-award.
    xp_awarded = 0
    if will_complete:
        claimed = cast(
            "CursorResult[Any]",
            await db.execute(
                update(ExerciseSubmission)
                .where(
                    ExerciseSubmission.id == submission.id,
                    ExerciseSubmission.xp_awarded.is_(False),
                )
                .values(xp_awarded=True)
            ),
        )
        if claimed.rowcount == 1:
            submission.xp_awarded = True
            xp_awarded = exercise.points
            profile = user.profile
            if profile is not None:
                profile.xp += exercise.points

    # Recompute lesson completion from the persisted submissions.
    total = int(
        await db.scalar(
            select(func.count()).select_from(Exercise).where(Exercise.lesson_id == lesson.id)
        )
        or 0
    )
    completed = int(
        await db.scalar(
            select(func.count())
            .select_from(ExerciseSubmission)
            .join(Exercise, ExerciseSubmission.exercise_id == Exercise.id)
            .where(
                Exercise.lesson_id == lesson.id,
                ExerciseSubmission.user_id == user.id,
                ExerciseSubmission.completed.is_(True),
            )
        )
        or 0
    )
    if total > 0 and completed == total and record.status != "completed":
        won = cast(
            "CursorResult[Any]",
            await db.execute(
                update(LessonProgress)
                .where(
                    LessonProgress.id == record.id,
                    LessonProgress.status != "completed",
                )
                .values(status="completed", completed_at=now)
            ),
        )
        if won.rowcount == 1:
            record.status = "completed"
            record.completed_at = now
            aggregate.lessons_completed += 1
            aggregate.study_minutes += lesson.estimated_minutes
            # Same transaction as the completion: both persist or neither does.
            await collect_lesson_words(db, user.id, lesson.id)

    aggregate.last_activity_at = now
    await record_activity(db, user.id)
    await db.flush()
    lesson_progress = await build_lesson_progress(db, user.id, lesson, record)
    if record.test_finished_at is None and lesson_progress.test_finished_at is not None:
        record.test_finished_at = lesson_progress.test_finished_at
    await db.commit()
    return SubmissionResultResponse(
        exercise_id=exercise.id,
        type=exercise.type,
        is_correct=is_correct,
        completed=submission.completed,
        points=exercise.points,
        xp_awarded=xp_awarded,
        feedback=_feedback(exercise, is_correct) if answer is not None else "Skipped",
        correct_option_id=(
            exercise.correct_option_id if exercise.type == "single_choice" else None
        ),
        accepted_answers=(
            list(exercise.accepted_answers)
            if exercise.type == "text" and exercise.accepted_answers
            else None
        ),
        model_answer=exercise.model_answer if exercise.type == "self_check" else None,
        explanation=exercise.explanation,
        explanation_localized=guidance.explanation_for(exercise.slug),
        wrong_answer_note=_wrong_note(exercise, answer, is_correct) if answer is not None else None,
        lesson=lesson_progress,
    )
