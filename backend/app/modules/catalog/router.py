"""Catalog HTTP endpoints (public, read-only).

Missing and unpublished resources both return the same `404 NOT_FOUND` so the
API never reveals the existence of draft content.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.session import get_db
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    CourseDetailResponse,
    CourseSummaryResponse,
    LessonDetailResponse,
)
from app.modules.exercises import service as exercises_service

router = APIRouter(tags=["catalog"])


def _not_found(message: str) -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


@router.get("/courses", response_model=list[CourseSummaryResponse])
async def list_courses(db: AsyncSession = Depends(get_db)) -> list[CourseSummaryResponse]:
    """List published courses ordered by position."""
    return await service.list_published_courses(db)


@router.get("/courses/{slug}", response_model=CourseDetailResponse)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)) -> CourseDetailResponse:
    """Return a published course and its published lessons."""
    result = await service.get_published_course(db, slug)
    if result is None:
        raise _not_found("Course not found")
    return service.to_course_detail(result)


@router.get("/lessons/{slug}", response_model=LessonDetailResponse)
async def get_lesson(slug: str, db: AsyncSession = Depends(get_db)) -> LessonDetailResponse:
    """Return a published lesson with its course context."""
    result = await service.get_published_lesson(db, slug)
    if result is None:
        raise _not_found("Lesson not found")
    lesson, course = result
    exercises = await exercises_service.list_public_exercises(db, lesson.id)
    return service.to_lesson_detail(lesson, course, exercises)
