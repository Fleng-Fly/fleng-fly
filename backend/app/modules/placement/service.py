import copy
import random
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.limits import consume
from app.db.models import PlacementAttempt
from app.modules.catalog.service import list_published_courses
from app.modules.placement.bank import load_bank
from app.modules.placement.schemas import (
    PlacementAnswers,
    PlacementDetail,
    PlacementQuestion,
    PlacementResult,
    PlacementSummary,
)
from app.modules.placement.scoring import (
    PRACTICE_VERSION,
    SCORING_VERSION,
    SINGLE_PASS_VERSION,
    score,
)


async def owned(db: AsyncSession, user_id: UUID, attempt_id: UUID, *, lock: bool = False):
    if lock:
        # SQLite write lock / PostgreSQL row lock, touching only this attempt.
        # Read the latest answers after acquiring it to avoid lost parallel saves.
        await db.execute(
            update(PlacementAttempt)
            .where(PlacementAttempt.id == attempt_id, PlacementAttempt.user_id == user_id)
            .values(id=PlacementAttempt.id)
            .execution_options(synchronize_session=False)
        )
    attempt = await db.scalar(
        select(PlacementAttempt)
        .where(PlacementAttempt.id == attempt_id, PlacementAttempt.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    if attempt is None:
        raise ApiError(404, "NOT_FOUND", "Placement attempt not found")
    return attempt


def summary(attempt: PlacementAttempt) -> PlacementSummary:
    return PlacementSummary(
        id=attempt.id,
        status=cast(Literal["in_progress", "completed"], attempt.status),
        bank_version=attempt.bank_version,
        scoring_version=attempt.scoring_version,
        practice=attempt.scoring_version == PRACTICE_VERSION,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        answered=len(attempt.answers),
        total=len(attempt.questions),
        estimated_level=attempt.result["estimated_level"] if attempt.result else None,
        result_label=attempt.result["label"] if attempt.result else None,
        correct=attempt.result["correct"] if attempt.result else None,
    )


async def detail(db: AsyncSession, attempt: PlacementAttempt) -> PlacementDetail:
    courses = []
    note = "Course suggestions appear after completion."
    if attempt.result and not attempt.result["insufficient_evidence"]:
        target = attempt.result["estimated_level"] or "A0"
        courses = await list_published_courses(db, level=target)
        note = f"Published {target} courses matching your approximate study starting point."
        if not courses:
            note = (
                f"No published {target} course is available. "
                "Browse the catalog; no substitute level has been inferred."
            )
    if attempt.result and attempt.result["insufficient_evidence"]:
        note = "Insufficient evidence for course placement; browse the catalog or ask a teacher."
    return PlacementDetail(
        **summary(attempt).model_dump(),
        # Explicit response projection keeps keys/explanations private before completion.
        questions=[PlacementQuestion.model_validate(q) for q in attempt.questions],
        answers=attempt.answers,
        result=PlacementResult.model_validate(attempt.result) if attempt.result else None,
        recommended_courses=courses,
        recommendation_note=note,
    )


async def start(db: AsyncSession, user_id: UUID) -> PlacementDetail:
    bank = load_bank()
    await consume(db, f"placement:start:{user_id}", 20, 86400)
    questions = copy.deepcopy(bank["questions"])
    rng = random.SystemRandom()
    rng.shuffle(questions)
    for q in questions:
        rng.shuffle(q["options"])
    attempt = PlacementAttempt(
        user_id=user_id,
        bank_version=bank["version"],
        scoring_version=SINGLE_PASS_VERSION,
        questions=questions,
        answers={},
        status="in_progress",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return await detail(db, attempt)


async def retry_mistakes(db: AsyncSession, user_id: UUID, attempt_id: UUID) -> PlacementDetail:
    source = await owned(db, user_id, attempt_id)
    if source.status != "completed" or source.result is None:
        raise ApiError(409, "PLACEMENT_INCOMPLETE", "Finish the attempt before retrying mistakes")
    missed = {
        row["question_id"]
        for row in source.result["review"]
        if not row["is_correct"] and row["selected_option_id"] is not None
    }
    if not missed:
        raise ApiError(409, "PLACEMENT_NO_MISTAKES", "This attempt has no wrong answers to retry")
    await consume(db, f"placement:start:{user_id}", 20, 86400)
    attempt = PlacementAttempt(
        user_id=user_id,
        bank_version=source.bank_version,
        scoring_version=PRACTICE_VERSION,
        questions=[question for question in source.questions if question["id"] in missed],
        answers={},
        status="in_progress",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return await detail(db, attempt)


async def save_answers(
    db: AsyncSession, user_id: UUID, attempt_id: UUID, payload: PlacementAnswers
) -> PlacementDetail:
    attempt = await owned(db, user_id, attempt_id, lock=True)
    if attempt.status != "in_progress":
        raise ApiError(409, "PLACEMENT_COMPLETED", "Completed attempts cannot be edited")
    questions = {q["id"]: q for q in attempt.questions}
    incoming = {}
    for answer in payload.answers:
        if answer.question_id in incoming:
            raise ApiError(422, "INVALID_PLACEMENT_ANSWER", "Duplicate question in answer batch")
        q = questions.get(answer.question_id)
        if q is None or (
            answer.option_id is not None and answer.option_id not in {o["id"] for o in q["options"]}
        ):
            raise ApiError(422, "INVALID_PLACEMENT_ANSWER", "Choose an option from this attempt")
        incoming[answer.question_id] = answer.option_id
    if any(
        question_id in attempt.answers and attempt.answers[question_id] != option_id
        for question_id, option_id in incoming.items()
    ):
        raise ApiError(409, "PLACEMENT_ANSWER_SAVED", "This question already has a saved outcome")
    attempt.answers = {**attempt.answers, **incoming}
    await db.commit()
    return await detail(db, attempt)


async def complete(db: AsyncSession, user_id: UUID, attempt_id: UUID) -> PlacementDetail:
    attempt = await owned(db, user_id, attempt_id, lock=True)
    if attempt.status == "completed":
        # Retried completion does not create a new attempt or recompute the result.
        await db.commit()
        return await detail(db, attempt)
    if len(attempt.answers) != len(attempt.questions):
        raise ApiError(
            409, "PLACEMENT_INCOMPLETE", "Answer or skip every question before finishing"
        )
    if attempt.scoring_version not in {SCORING_VERSION, SINGLE_PASS_VERSION, PRACTICE_VERSION}:
        raise ApiError(
            409, "PLACEMENT_VERSION_UNAVAILABLE", "Start a new attempt for this test version"
        )
    attempt.result = score(attempt.questions, attempt.answers)
    if attempt.scoring_version == PRACTICE_VERSION:
        attempt.result.update(
            estimated_level=None,
            insufficient_evidence=True,
            ceiling_reached=False,
            label="Placement mistake practice complete",
        )
    attempt.status = "completed"
    attempt.completed_at = datetime.now(UTC)
    await db.commit()
    return await detail(db, attempt)
