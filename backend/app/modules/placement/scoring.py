"""Deterministic study guidance, not calibrated CEFR certification."""

from collections import Counter

from app.modules.placement.bank import LEVELS

SCORING_VERSION = "conservative-1"
LIMITATIONS = [
    "This is approximate study guidance, not a CEFR certificate or a full proficiency assessment.",
    "Only grammar, vocabulary and short reading are sampled; "
    "listening, speaking and writing are not tested.",
    "Item difficulty tags and score cutoffs have not been externally calibrated "
    "or approved by a CEFR examiner.",
    "C1/C2 questions are exploratory only. This MVP cannot confirm C1 or C2, "
    "even with a perfect score.",
    "Repeat attempts reuse this bank; familiarity may inflate later scores.",
]


def score(questions: list[dict], answers: dict[str, str]) -> dict:
    totals = Counter(q["level"] for q in questions)
    correct = Counter(q["level"] for q in questions if answers[q["id"]] == q["correct_option_id"])
    # Only consecutive lower bands with at least six items can support an estimate.
    # Five of six is a conservative product heuristic, not a validated CEFR cutoff.
    supported = []
    for band in LEVELS[:4]:
        if totals[band] < 6:
            break
        supported.append(band)
    level = None
    for band in LEVELS[:4]:
        if totals[band] < 6 or correct[band] * 6 < totals[band] * 5:
            break
        level = band
    ceiling = bool(level and supported and level == supported[-1])
    label = "Below the A1 threshold on this test; start with introductory practice"
    if level:
        label = f"Approximate {level} study starting point"
    if level == "B2":
        label = "B2 or above on this limited test; C1/C2 are not determined"
    if not supported:
        label = "Insufficient questions to estimate a study starting point"
    assessment_range = (
        f"A1–{supported[-1]}" if len(supported) > 1 else "A1" if supported else "Not established"
    )
    return dict(
        correct=sum(correct.values()),
        total=len(questions),
        estimated_level=level,
        label=label,
        assessment_range=assessment_range,
        ceiling_reached=ceiling,
        insufficient_evidence=not supported,
        reliability="limited",
        limitations=LIMITATIONS,
        bands=[dict(level=band, correct=correct[band], total=totals[band]) for band in LEVELS],
        review=[
            dict(
                question_id=q["id"],
                selected_option_id=answers[q["id"]],
                correct_option_id=q["correct_option_id"],
                is_correct=answers[q["id"]] == q["correct_option_id"],
                explanation=q["explanation"],
            )
            for q in questions
        ],
    )
