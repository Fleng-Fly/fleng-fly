"""Exercise endpoints: start a lesson, submit an answer, read progress.

All routes require authentication and resolve the lesson by its **slug** (the
same stable identifier used by `GET /lessons/{slug}`).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.exercises import service
from app.modules.exercises.schemas import (
    LessonProgressResponse,
    SubmissionRequest,
    SubmissionResultResponse,
)

router = APIRouter(tags=["exercises"])


@router.post("/lessons/{slug}/start", response_model=LessonProgressResponse)
async def start_lesson(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonProgressResponse:
    """Start or resume a lesson. Idempotent."""
    lesson, _course = await service.get_lesson_or_404(db, slug)
    return await service.start_lesson(db, current_user, lesson)


@router.get("/lessons/{slug}/progress", response_model=LessonProgressResponse)
async def get_lesson_progress(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonProgressResponse:
    """Read the caller's progress through a lesson."""
    lesson, _course = await service.get_lesson_or_404(db, slug)
    return await service.get_lesson_progress(db, current_user, lesson)


@router.post("/lessons/{slug}/submit", response_model=SubmissionResultResponse)
async def submit_answer(
    slug: str,
    payload: SubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResultResponse:
    """Grade and persist one answer; return the result and lesson progress."""
    lesson, _course = await service.get_lesson_or_404(db, slug)
    exercise = await service.get_exercise_or_404(db, lesson, payload.exercise_id)
    return await service.submit_answer(
        db,
        user=current_user,
        lesson=lesson,
        exercise=exercise,
        answer=payload.answer,
        self_assessment=payload.self_assessment,
    )
