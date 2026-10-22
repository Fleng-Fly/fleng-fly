"""Answer normalisation and objective grading.

Only `single_choice` and `text` exercise types are graded objectively.
`self_check` is never graded by the server — the caller records the learner's
own assessment instead (see `service.submit_answer`).
"""

from app.db.models import Exercise


def normalize_text(value: str) -> str:
    """Trim, collapse internal whitespace and casefold for comparison."""
    return " ".join(value.strip().casefold().split())


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
