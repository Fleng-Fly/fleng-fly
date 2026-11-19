from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.core.schemas import CamelModel
from app.modules.catalog.schemas import CourseSummaryResponse

PlacementLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class PlacementOption(CamelModel):
    id: str
    text: str


class PlacementQuestion(CamelModel):
    id: str
    level: PlacementLevel
    skill: str
    prompt: str
    options: list[PlacementOption]


class PlacementAnswer(CamelModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1, max_length=40)
    option_id: str = Field(min_length=1, max_length=40)


class PlacementAnswers(CamelModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[PlacementAnswer] = Field(min_length=1, max_length=100)


class PlacementBandScore(CamelModel):
    level: PlacementLevel
    correct: int
    total: int


class PlacementReview(CamelModel):
    question_id: str
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    explanation: str


class PlacementResult(CamelModel):
    correct: int
    total: int
    estimated_level: Literal["A1", "A2", "B1", "B2"] | None
    label: str
    assessment_range: str
    ceiling_reached: bool
    insufficient_evidence: bool
    reliability: Literal["limited"]
    limitations: list[str]
    bands: list[PlacementBandScore]
    review: list[PlacementReview]


class PlacementSummary(CamelModel):
    id: UUID
    status: Literal["in_progress", "completed"]
    bank_version: str
    scoring_version: str
    started_at: datetime
    completed_at: datetime | None
    answered: int
    total: int
    estimated_level: Literal["A1", "A2", "B1", "B2"] | None
    result_label: str | None
    # Correct answers of a completed attempt (out of `total`); null while in progress.
    correct: int | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def utc_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class PlacementDetail(PlacementSummary):
    questions: list[PlacementQuestion]
    answers: dict[str, str]
    result: PlacementResult | None
    recommended_courses: list[CourseSummaryResponse]
    recommendation_note: str
