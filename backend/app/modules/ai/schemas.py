from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.core.schemas import CamelModel

Level = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class ChatRequest(CamelModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation_id: UUID | None = None
    lesson_id: UUID | None = None
    correct_grammar: bool = True


class ExplainRequest(CamelModel):
    exercise_id: UUID | None = None
    lesson_id: UUID | None = None
    student_answer: str = Field(min_length=1, max_length=4000)
    topic: str = Field(default="English grammar", min_length=1, max_length=200)


class GenerateRequest(CamelModel):
    level: Level | None = None
    topic: str = Field(min_length=1, max_length=200)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    exercise_type: Literal["multiple_choice", "fill_blank", "sentence_correction"]


class GeneratedExercise(CamelModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["multiple_choice", "fill_blank", "sentence_correction"]
    prompt: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(default_factory=list, max_length=6)
    answer: str = Field(min_length=1, max_length=1000)
    explanation: str = Field(min_length=1, max_length=2000)
    practice_only: Literal[True] = True

    @model_validator(mode="after")
    def valid_exercise(self):
        if not all(v.strip() for v in (self.prompt, self.answer, self.explanation)):
            raise ValueError("Empty exercise content")
        if self.type == "multiple_choice":
            if not 2 <= len(self.options) <= 6 or len(set(self.options)) != len(self.options):
                raise ValueError("Provide unique choices")
            if self.answer not in self.options or any(
                not x.strip() or len(x) > 500 for x in self.options
            ):
                raise ValueError("Answer must match a choice")
        elif self.options:
            raise ValueError("Options only belong to multiple choice")
        if self.type == "fill_blank" and "___" not in self.prompt:
            raise ValueError("Blank must be marked ___")
        return self


class Explanation(CamelModel):
    model_config = ConfigDict(extra="forbid")
    explanation: str = Field(min_length=1, max_length=4000)
    correct_example: str = Field(min_length=1, max_length=2000)
    rule: str = Field(min_length=1, max_length=2000)
    hint: str = Field(default="", max_length=1000)


class ConversationResponse(CamelModel):
    id: UUID
    model: str
    created_at: datetime


class MessageResponse(CamelModel):
    id: UUID
    role: str
    content: str
    model: str
    usage: dict | None
    created_at: datetime


class ChatResponse(CamelModel):
    conversation_id: UUID
    message: MessageResponse
