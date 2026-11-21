"""Reading API schemas (camelCase JSON).

Quiz questions are exposed in two shapes: `ReadingQuestionPublic` (no answer key) while an
attempt is open, and `ReadingReviewItem` (with the key and explanation) only after submit.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, StrictInt

from app.core.schemas import CamelModel

ReadingLevel = Literal["A0", "A1", "A2", "B1", "B2"]


class ReadingCategoryRef(CamelModel):
    id: UUID
    slug: str
    title: str


class ReadingCategoryResponse(ReadingCategoryRef):
    description: str
    article_count: int


class ReadingProgressResponse(CamelModel):
    status: Literal["in_progress", "completed"]
    read_percent: int
    best_score_percent: int | None
    attempts_count: int
    xp_awarded: int


class ReadingArticleSummary(CamelModel):
    id: UUID
    slug: str
    title: str
    description: str
    level: ReadingLevel
    reading_minutes: int
    cover_image_url: str | None
    cover_alt: str | None
    category: ReadingCategoryRef
    published_at: datetime | None
    progress: ReadingProgressResponse | None
    bookmarked: bool


class ReadingArticleDetail(ReadingArticleSummary):
    content: str
    question_count: int
    points_possible: int


class ReadingArticleList(CamelModel):
    items: list[ReadingArticleSummary]
    total: int
    limit: int
    offset: int


class ReadingProgressUpdate(CamelModel):
    percent: StrictInt = Field(ge=0, le=100)


class ReadingBookmarkResponse(CamelModel):
    article_id: UUID
    bookmarked: bool


class ReadingPreferencesUpdate(CamelModel):
    category_ids: list[UUID] = Field(max_length=50)


class ReadingPreferencesResponse(CamelModel):
    categories: list[ReadingCategoryRef]


class ReadingAnswerPublic(CamelModel):
    id: UUID
    text: str


class ReadingQuestionPublic(CamelModel):
    id: UUID
    prompt: str
    points: int
    answers: list[ReadingAnswerPublic]


class ReadingReviewItem(CamelModel):
    question_id: UUID
    prompt: str
    answers: list[ReadingAnswerPublic]
    selected_answer_id: UUID | None
    correct_answer_id: UUID
    is_correct: bool
    points: int
    explanation: str | None


class ReadingAttemptResult(CamelModel):
    score_percent: int
    points_earned: int
    points_possible: int
    passed: bool
    pass_mark: int
    xp_awarded: int
    questions: list[ReadingReviewItem]


class ReadingAttemptResponse(CamelModel):
    id: UUID
    article_slug: str
    attempt_number: int
    status: Literal["in_progress", "submitted"]
    answers: dict[UUID, UUID]
    # Only while in progress; a submitted attempt carries `result` instead.
    questions: list[ReadingQuestionPublic] | None = None
    result: ReadingAttemptResult | None = None
    already_submitted: bool = False
    started_at: datetime
    submitted_at: datetime | None


class ReadingAttemptSummary(CamelModel):
    id: UUID
    attempt_number: int
    status: Literal["in_progress", "submitted"]
    score_percent: int | None
    passed: bool | None
    xp_awarded: int
    started_at: datetime
    submitted_at: datetime | None


class ReadingAnswersUpdate(CamelModel):
    answers: dict[UUID, UUID] = Field(max_length=100)


class ReadingSubmitRequest(CamelModel):
    answers: dict[UUID, UUID] | None = Field(default=None, max_length=100)
