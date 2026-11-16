from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.core.levels import LearningLevel
from app.core.schemas import CamelModel


class VocabularyCreate(CamelModel):
    word: str = Field(min_length=1, max_length=120)
    translation: str = Field(min_length=1, max_length=300)
    example: str = Field(default="", max_length=1000)
    lesson_id: UUID | None = None

    @field_validator("word", "translation")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()


class VocabularyUpdate(CamelModel):
    learned: bool


class VocabularyStatsResponse(CamelModel):
    words_learned: int


class ReviewRequest(CamelModel):
    remembered: bool


class VocabularyResponse(VocabularyCreate):
    id: UUID
    learned: bool
    due_at: datetime
    created_at: datetime


class ReviewResponse(CamelModel):
    id: UUID
    remembered: bool
    created_at: datetime


# Use the repository's camelCase JSON convention, accepting snake_case on input.
CefrLevel = LearningLevel


class FlashcardCreate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["my_words", "course_words"]
    course_id: UUID | None = None
    level: CefrLevel | None = None


class Flashcard(CamelModel):
    word_id: UUID
    word: str
    translation: str
    example: str


class FlashcardResponse(CamelModel):
    session_id: UUID
    source: Literal["my_words", "course_words"]
    status: Literal["active", "completed", "empty"]
    total: int
    cards: list[Flashcard]
    test_ready: bool


class CourseWordResponse(CamelModel):
    id: UUID
    course_id: UUID
    word: str
    translation: str
    example: str
