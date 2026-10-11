"""Pydantic response schemas for the course/lesson catalog.

These are public read models: they deliberately do not expose `is_published`,
timestamps or any internal bookkeeping.
"""

from uuid import UUID

from app.core.schemas import CamelModel


class CourseSummaryResponse(CamelModel):
    """A course in the catalog list."""

    id: UUID
    slug: str
    title: str
    description: str
    level: str
    lesson_count: int


class LessonSummaryResponse(CamelModel):
    """A lesson inside a course detail response (no theory body)."""

    id: UUID
    slug: str
    title: str
    summary: str
    position: int
    estimated_minutes: int


class CourseDetailResponse(CamelModel):
    """A course with its published lessons."""

    id: UUID
    slug: str
    title: str
    description: str
    level: str
    lessons: list[LessonSummaryResponse]


class LessonDetailResponse(CamelModel):
    """A single lesson with its course context and theory body."""

    id: UUID
    slug: str
    title: str
    summary: str
    theory: str
    position: int
    estimated_minutes: int
    course_slug: str
    course_title: str
    level: str
