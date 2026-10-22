"""Schemas for exercises, submissions and lesson progress."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.core.schemas import CamelModel

# Bounds the stored answer size; keeps payloads and rows small.
MAX_ANSWER_LENGTH = 2000


class ExerciseOptionResponse(CamelModel):
    id: str
    text: str


class ExercisePublicResponse(CamelModel):
    """Public exercise content.

    Deliberately excludes every grading secret (`correct_option_id`,
    `accepted_answers`, `model_answer`, `explanation`). Options are only present
    for `single_choice` exercises.
    """

    id: UUID
    slug: str
    position: int
    type: str
    prompt: str
    points: int
    options: list[ExerciseOptionResponse] | None = None


class SubmissionRequest(CamelModel):
    exercise_id: UUID
    answer: str = Field(max_length=MAX_ANSWER_LENGTH)
    self_assessment: Literal["correct", "incorrect"] | None = None


class LessonExerciseStateResponse(CamelModel):
    """The caller's state for one exercise within a lesson."""

    exercise_id: UUID
    completed: bool
    is_correct: bool | None
    attempts: int
    points_awarded: int
    answer: str | None = None


class LessonProgressResponse(CamelModel):
    """The caller's progress through a lesson."""

    lesson_slug: str
    lesson_title: str
    status: str
    completed: bool
    started_at: datetime | None
    completed_at: datetime | None
    exercises_total: int
    exercises_completed: int
    xp_earned: int
    exercises: list[LessonExerciseStateResponse]


class SubmissionResultResponse(CamelModel):
    """The result of one graded submission.

    The correct answer / model answer / explanation are revealed here (and only
    here) so the learner can review the attempt.
    """

    exercise_id: UUID
    type: str
    is_correct: bool | None
    completed: bool
    points: int
    xp_awarded: int
    feedback: str
    correct_option_id: str | None = None
    accepted_answers: list[str] | None = None
    model_answer: str | None = None
    explanation: str | None = None
    lesson: LessonProgressResponse
