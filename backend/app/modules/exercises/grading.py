"""Answer normalisation and objective grading.

Only `single_choice` and `text` exercise types are graded objectively.
`self_check` is never graded by the server — the caller records the learner's
own assessment instead (see `service.submit_answer`).
"""

import re
import unicodedata

from app.db.models import Exercise

# Typographic apostrophes (phone keyboards insert U+2019) and look-alikes.
_APOSTROPHES = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u02bc": "'", "\u0060": "'", "\u00b4": "'"}
)
# Sentence punctuation is optional in a short answer. Apostrophes and hyphens are
# part of words (I'm, well-known) and are kept.
_OPTIONAL_PUNCTUATION = re.compile(r"[.,;:!?\u2026\"\u201c\u201d()]")


def normalize_text(value: str) -> str:
    """Normalise a short answer for comparison.

    Applies NFKC, unifies typographic apostrophes, drops optional sentence
    punctuation (so "Nice to meet you too." and "Nice to meet you, too" match),
    trims, collapses whitespace and casefolds. Letters are never changed or
    merged, so a wrong word stays wrong.
    """
    # Map apostrophes first: NFKC would turn U+00B4 into a combining accent.
    text = unicodedata.normalize("NFKC", value.translate(_APOSTROPHES))
    text = _OPTIONAL_PUNCTUATION.sub(" ", text)
    return " ".join(text.casefold().split())


def option_ids(exercise: Exercise) -> set[str]:
    return {str(option["id"]) for option in (exercise.options or [])}


def grade_objective(exercise: Exercise, answer: str) -> bool:
    """Return whether `answer` is objectively correct.

    Raises `ValueError` if called for a type that is not objectively graded.
    """
    if exercise.type == "single_choice":
        return answer == exercise.correct_option_id
    if exercise.type == "text":
        accepted = {normalize_text(item) for item in (exercise.accepted_answers or [])}
        return normalize_text(answer) in accepted
    raise ValueError(f"exercise type {exercise.type!r} is not objectively graded")
