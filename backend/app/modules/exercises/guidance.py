"""Hints, explanations and lesson guides kept beside (never inside) the curriculum.

The curriculum JSON is pinned by a publication SHA, so learner guidance lives in a
separate, versioned sidecar file (`content/exercise-guidance-*.json`) keyed by the
existing lesson/exercise slugs. No database change and no AI/provider call: text is
authored content, served verbatim in English and Ukrainian.

Review gate: the file carries `review_status`. Anything other than `reviewed` is a
draft and is only served outside production, mirroring how draft curriculum is
treated elsewhere. Hints are public (they never contain the answer); explanations
and wrong-answer notes are only attached to a graded submission result.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.core.schemas import CamelModel

CONTENT = Path(__file__).resolve().parents[2] / "db" / "content" / "exercise-guidance-a0-a1.json"


class LocalizedText(CamelModel):
    """The same text in both interface languages (English is the fallback)."""

    en: str = Field(min_length=1, max_length=1200)
    uk: str = Field(min_length=1, max_length=1200)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExampleSpec(_Strict):
    en: str = Field(min_length=1, max_length=300)
    uk: str = Field(min_length=1, max_length=300)


class ExerciseGuidanceSpec(_Strict):
    hint: LocalizedText
    explanation: LocalizedText
    # Extra notes keyed by the casefolded *wrong option text* for this exercise only.
    wrong: dict[str, LocalizedText] = Field(default_factory=dict)


class LessonGuidanceSpec(_Strict):
    explanation: LocalizedText
    examples: list[ExampleSpec] = Field(min_length=2, max_length=5)
    # Notes keyed by the casefolded wrong option text, shared by the lesson's exercises.
    option_notes: dict[str, LocalizedText] = Field(default_factory=dict)
    exercises: dict[str, ExerciseGuidanceSpec]


class GuidanceFile(_Strict):
    version: Literal[1]
    review_status: Literal["draft", "reviewed"]
    levels: list[str]
    lessons: dict[str, LessonGuidanceSpec]


class ExampleResponse(CamelModel):
    en: str
    uk: str


class LessonGuideResponse(CamelModel):
    """Short plain-language explanation of the lesson rule with examples."""

    explanation: LocalizedText
    examples: list[ExampleResponse]


@lru_cache
def load_guidance(path: Path = CONTENT) -> GuidanceFile:
    return GuidanceFile.model_validate_json(path.read_text(encoding="utf-8"))


def drafts_allowed() -> bool:
    """Unreviewed guidance is never served in production."""
    return not get_settings().is_production


def _available() -> GuidanceFile | None:
    guidance = load_guidance()
    if guidance.review_status == "reviewed" or drafts_allowed():
        return guidance
    return None


def _lesson_slug(guidance: GuidanceFile, exercise_slug: str) -> str | None:
    return next((s for s in guidance.lessons if exercise_slug.startswith(s + "-")), None)


def hint_for(exercise_slug: str) -> LocalizedText | None:
    guidance = _available()
    if guidance is None:
        return None
    lesson = _lesson_slug(guidance, exercise_slug)
    entry = guidance.lessons[lesson].exercises.get(exercise_slug) if lesson else None
    return entry.hint if entry else None


def explanation_for(exercise_slug: str) -> LocalizedText | None:
    guidance = _available()
    if guidance is None:
        return None
    lesson = _lesson_slug(guidance, exercise_slug)
    entry = guidance.lessons[lesson].exercises.get(exercise_slug) if lesson else None
    return entry.explanation if entry else None


def wrong_note_for(exercise_slug: str, selected_text: str) -> LocalizedText | None:
    """Why the chosen (incorrect) option does not fit, when we have that knowledge."""
    guidance = _available()
    if guidance is None:
        return None
    lesson = _lesson_slug(guidance, exercise_slug)
    if lesson is None:
        return None
    key = selected_text.strip().casefold()
    entry = guidance.lessons[lesson].exercises.get(exercise_slug)
    if entry and key in entry.wrong:
        return entry.wrong[key]
    return guidance.lessons[lesson].option_notes.get(key)


def lesson_guide_for(lesson_slug: str) -> LessonGuideResponse | None:
    guidance = _available()
    entry = guidance.lessons.get(lesson_slug) if guidance else None
    if entry is None:
        return None
    return LessonGuideResponse(
        explanation=entry.explanation,
        examples=[ExampleResponse(en=e.en, uk=e.uk) for e in entry.examples],
    )
