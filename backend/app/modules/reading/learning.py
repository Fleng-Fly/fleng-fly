"""Reading progress, quiz attempts, grading and XP.

Rules (also documented in `docs/database.md`):

- **Progress**: `read_percent` (0-100) only grows. An article is **completed** once: on the
  first *passing* quiz attempt (score >= `PASS_PERCENT`), or on reaching 100% for an article
  without questions.
- **Attempts**: at most one is `in_progress` per learner and article; `start_attempt` returns
  it again instead of creating another, so a learner can resume. `save_answers` merges
  partial answers. `submit_attempt` grades, freezes a `result` snapshot and is idempotent:
  submitting an already submitted attempt returns it unchanged. Unanswered questions score 0.
- **XP**: the existing `profiles.xp`. The first passing attempt for an article pays the
  article's total question points, once per (learner, article): a conditional UPDATE on
  `reading_user_progress.xp_awarded` makes the claim atomic. Retries, failed attempts and
  repeated submissions never pay again. Streak activity and achievements reuse the
  gamification service.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Profile, ReadingArticle, ReadingAttempt, ReadingUserProgress
from app.modules.gamification.service import lock_learner, record_activity
from app.modules.reading.content import get_article

PASS_PERCENT = 70


def grade(article: ReadingArticle, answers: Mapping[str, str]) -> dict[str, Any]:
    """Pure grading of `{question_id: answer_id}` against the article's current quiz."""
    items: list[dict[str, Any]] = []
    earned = possible = 0
    for question in article.questions:
        correct = next(a for a in question.answers if a.is_correct)
        selected = answers.get(str(question.id))
        is_correct = selected == str(correct.id)
        possible += question.points
        earned += question.points if is_correct else 0
        items.append(
            {
                "question_id": str(question.id),
                # Text is snapshotted so a reviewed result never depends on later edits.
                "prompt": question.prompt,
                "answers": [{"id": str(a.id), "text": a.text} for a in question.answers],
                "selected_answer_id": selected,
                "correct_answer_id": str(correct.id),
                "is_correct": is_correct,
                "points": question.points,
                "explanation": question.explanation,
            }
        )
    percent = earned * 100 // possible if possible else 0
    return {
        "questions": items,
        "points_earned": earned,
        "points_possible": possible,
        "score_percent": percent,
        "passed": possible > 0 and percent >= PASS_PERCENT,
    }


def _not_found(what: str) -> ApiError:
    return ApiError(404, "NOT_FOUND", f"{what} not found")


async def _available_article(db: AsyncSession, article_id: UUID) -> ReadingArticle:
    article = await get_article(db, article_id=article_id, available_only=True)
    if article is None:
        raise _not_found("Article")
    return article


async def _claim(db: AsyncSession, statement: Any) -> bool:
    """Run a conditional UPDATE; True when this call won the row."""
    result = cast("CursorResult[Any]", await db.execute(statement))
    return result.rowcount == 1


async def get_progress(
    db: AsyncSession, user_id: UUID, article_id: UUID
) -> ReadingUserProgress | None:
    return await db.scalar(
        select(ReadingUserProgress).where(
            ReadingUserProgress.user_id == user_id, ReadingUserProgress.article_id == article_id
        )
    )


async def _get_or_create_progress(
    db: AsyncSession, user_id: UUID, article_id: UUID
) -> ReadingUserProgress:
    progress = await get_progress(db, user_id, article_id)
    if progress is None:
        progress = ReadingUserProgress(user_id=user_id, article_id=article_id)
        db.add(progress)
        await db.flush()
    return progress


async def list_progress(
    db: AsyncSession, user_id: UUID, *, status: str | None = None
) -> list[ReadingUserProgress]:
    statement = select(ReadingUserProgress).where(ReadingUserProgress.user_id == user_id)
    if status is not None:
        statement = statement.where(ReadingUserProgress.status == status)
    statement = statement.order_by(ReadingUserProgress.last_read_at.desc())
    return list((await db.scalars(statement)).all())


async def update_read_progress(
    db: AsyncSession, user_id: UUID, article_id: UUID, percent: int
) -> ReadingUserProgress:
    """Record how far the learner has read. Lower values are ignored (never regresses)."""
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ApiError(422, "VALIDATION_FAILED", "percent must be an integer from 0 to 100")
    article = await _available_article(db, article_id)
    await lock_learner(db, user_id)
    progress = await _get_or_create_progress(db, user_id, article_id)
    now = datetime.now(UTC)
    progress.read_percent = max(progress.read_percent, percent)
    progress.last_read_at = now
    if not article.questions and progress.read_percent == 100 and progress.status != "completed":
        progress.status = "completed"
        progress.completed_at = now
        await record_activity(db, user_id)
    await db.commit()
    return progress


async def get_active_attempt(
    db: AsyncSession, user_id: UUID, article_id: UUID
) -> ReadingAttempt | None:
    return await db.scalar(
        select(ReadingAttempt).where(
            ReadingAttempt.user_id == user_id,
            ReadingAttempt.article_id == article_id,
            ReadingAttempt.status == "in_progress",
        )
    )


async def start_attempt(db: AsyncSession, user_id: UUID, article_id: UUID) -> ReadingAttempt:
    """Open a quiz attempt, or return the one already in progress (resume)."""
    article = await _available_article(db, article_id)
    if not article.questions:
        raise ApiError(409, "NO_QUESTIONS", "This article has no quiz")
    await lock_learner(db, user_id)
    attempt = await get_active_attempt(db, user_id, article_id)
    if attempt is None:
        last = await db.scalar(
            select(func.max(ReadingAttempt.attempt_number)).where(
                ReadingAttempt.user_id == user_id, ReadingAttempt.article_id == article_id
            )
        )
        attempt = ReadingAttempt(
            user_id=user_id, article_id=article_id, attempt_number=(last or 0) + 1, answers={}
        )
        db.add(attempt)
        await _get_or_create_progress(db, user_id, article_id)
        await db.flush()
    await db.commit()
    return attempt


async def get_attempt(db: AsyncSession, user_id: UUID, attempt_id: UUID) -> ReadingAttempt:
    """An attempt owned by `user_id`; another learner's attempt is indistinguishable (404)."""
    attempt = await db.scalar(
        select(ReadingAttempt)
        .where(ReadingAttempt.id == attempt_id, ReadingAttempt.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    if attempt is None:
        raise _not_found("Attempt")
    return attempt


async def list_attempts(db: AsyncSession, user_id: UUID, article_id: UUID) -> list[ReadingAttempt]:
    return list(
        (
            await db.scalars(
                select(ReadingAttempt)
                .where(ReadingAttempt.user_id == user_id, ReadingAttempt.article_id == article_id)
                .order_by(ReadingAttempt.attempt_number.desc())
            )
        ).all()
    )


def _merge_answers(
    article: ReadingArticle, current: Mapping[str, str], new: Mapping[Any, Any]
) -> dict[str, str]:
    """Validate `{question_id: answer_id}` against the quiz and merge it over `current`."""
    options = {str(q.id): {str(a.id) for a in q.answers} for q in article.questions}
    merged = dict(current)
    for question_id, answer_id in new.items():
        question_key, answer_key = str(question_id), str(answer_id)
        if question_key not in options:
            raise ApiError(422, "INVALID_ANSWER", "Unknown question for this article")
        if answer_key not in options[question_key]:
            raise ApiError(422, "INVALID_ANSWER", "Answer does not belong to the question")
        merged[question_key] = answer_key
    return merged


async def save_answers(
    db: AsyncSession, user_id: UUID, attempt_id: UUID, answers: Mapping[Any, Any]
) -> ReadingAttempt:
    """Save (merge) partial answers so the attempt can be resumed later."""
    await lock_learner(db, user_id)
    attempt = await get_attempt(db, user_id, attempt_id)
    if attempt.status != "in_progress":
        raise ApiError(409, "ATTEMPT_SUBMITTED", "This attempt is already submitted")
    article = await _available_article(db, attempt.article_id)
    attempt.answers = _merge_answers(article, attempt.answers, answers)
    await db.commit()
    return attempt


async def submit_attempt(
    db: AsyncSession,
    user_id: UUID,
    attempt_id: UUID,
    answers: Mapping[Any, Any] | None = None,
) -> ReadingAttempt:
    """Grade and freeze an attempt. Idempotent: a submitted attempt is returned unchanged."""
    await lock_learner(db, user_id)
    attempt = await get_attempt(db, user_id, attempt_id)
    if attempt.status == "submitted":
        return attempt
    article = await _available_article(db, attempt.article_id)
    if not article.questions:
        raise ApiError(409, "NO_QUESTIONS", "This article has no quiz")
    final_answers = _merge_answers(article, attempt.answers, answers or {})
    graded = grade(article, final_answers)
    now = datetime.now(UTC)

    won = await _claim(
        db,
        update(ReadingAttempt)
        .where(ReadingAttempt.id == attempt.id, ReadingAttempt.status == "in_progress")
        .values(status="submitted"),
    )
    if not won:  # another request submitted it first
        await db.refresh(attempt)
        return attempt

    attempt.status = "submitted"
    attempt.answers = final_answers
    attempt.result = {"questions": graded["questions"]}
    attempt.points_earned = graded["points_earned"]
    attempt.points_possible = graded["points_possible"]
    attempt.score_percent = graded["score_percent"]
    attempt.passed = graded["passed"]
    attempt.submitted_at = now

    progress = await _get_or_create_progress(db, user_id, article.id)
    progress.attempts_count += 1
    progress.best_score_percent = max(progress.best_score_percent or 0, graded["score_percent"])
    progress.read_percent = 100 if graded["passed"] else progress.read_percent
    progress.last_read_at = now
    if graded["passed"]:
        if progress.status != "completed":
            progress.status = "completed"
            progress.completed_at = now
        xp = graded["points_possible"]
        if await _claim(
            db,
            update(ReadingUserProgress)
            .where(ReadingUserProgress.id == progress.id, ReadingUserProgress.xp_awarded == 0)
            .values(xp_awarded=xp),
        ):
            progress.xp_awarded = xp
            attempt.xp_awarded = xp
            profile = await db.scalar(
                select(Profile)
                .where(Profile.user_id == user_id)
                .execution_options(populate_existing=True)
            )
            if profile is not None:
                profile.xp += xp
    await record_activity(db, user_id)
    await db.commit()
    return attempt
