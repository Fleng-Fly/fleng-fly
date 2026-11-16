"""Independent structure checks for learning content (see docs/qa/learning-content-audit.md).

These tests read the content directly and do not reuse the importer or the
validator, so they act as a second opinion on both. Invariants that hold today
are plain tests. Known content defects from the audit that are still open are
strict ``xfail`` tests: they document the defect, and fail loudly (XPASS) once it is fixed so
the marker gets removed.
"""

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from app.core.levels import LEARNING_LEVELS
from app.db.seed import SEED_COURSES, SEED_EXERCISES
from app.modules.exercises.grading import normalize_text

CONTENT = Path(__file__).resolve().parents[1] / "app/db/content/curriculum-a0-b2.json"
CURRICULUM = json.loads(CONTENT.read_text(encoding="utf-8"))
COURSES = CURRICULUM["courses"]
LESSONS = [(c, lesson) for c in COURSES for lesson in c["lessons"]]
EXERCISES = [(c, lesson, e) for c, lesson in LESSONS for e in lesson["exercises"]]
CYRILLIC = re.compile("[а-яіїєґ]", re.IGNORECASE)


def correct_text(exercise: dict) -> str:
    return next(o["text"] for o in exercise["options"] if o["id"] == exercise["correct_option_id"])


def ids(items):
    return [e["slug"] for *_, e in items]


# --------------------------------------------------------------------------- JSON curriculum


def test_slugs_are_globally_unique() -> None:
    for kind, slugs in {
        "course": [c["slug"] for c in COURSES],
        "lesson": [lesson["slug"] for _, lesson in LESSONS],
        "exercise": [e["slug"] for *_, e in EXERCISES],
    }.items():
        assert len(slugs) == len(set(slugs)), f"duplicate {kind} slug"


def test_courses_follow_cefr_order_and_lessons_are_contiguous() -> None:
    assert [c["level"] for c in COURSES] == ["A0", "A1", "A2", "B1", "B2"]
    assert [c["position"] for c in COURSES] == sorted(c["position"] for c in COURSES)
    for course in COURSES:
        assert [x["position"] for x in course["lessons"]] == list(range(1, 11)), course["slug"]
        for lesson in course["lessons"]:
            assert lesson["slug"].startswith(course["slug"] + "-")


def test_prerequisites_point_to_the_previous_lesson() -> None:
    order = [lesson["slug"] for _, lesson in LESSONS]
    for index, (_, lesson) in enumerate(LESSONS):
        expected = [order[index - 1]] if index else []
        assert lesson["prerequisites"] == expected, lesson["slug"]


@pytest.mark.parametrize("course,lesson", LESSONS, ids=[x["slug"] for _, x in LESSONS])
def test_lesson_has_complete_material(course: dict, lesson: dict) -> None:
    for field in ("title", "summary", "grammar", "theory", "reading"):
        assert lesson[field].strip(), field
        assert not re.search(r"todo|lorem|\?\?\?|tbd", lesson[field], re.IGNORECASE)
    assert len(lesson["examples"]) >= 3 and all(x.strip() for x in lesson["examples"])
    assert len(lesson["goals"]) >= 2 and all(x.strip() for x in lesson["goals"])
    words = [v["word"].casefold() for v in lesson["vocabulary"]]
    assert len(words) >= 10 and len(words) == len(set(words))
    phases = Counter(e["phase"] for e in lesson["exercises"])
    assert phases["practice"] >= 5 and phases["check"] >= 3


@pytest.mark.parametrize("course,lesson", LESSONS, ids=[x["slug"] for _, x in LESSONS])
def test_vocabulary_translations_are_ukrainian(course: dict, lesson: dict) -> None:
    for item in lesson["vocabulary"]:
        assert item["word"].strip() and item["translation"].strip()
        assert CYRILLIC.search(item["translation"]), item


@pytest.mark.parametrize("course,lesson,exercise", EXERCISES, ids=ids(EXERCISES))
def test_exercise_answer_is_well_formed(course: dict, lesson: dict, exercise: dict) -> None:
    option_ids = [o["id"] for o in exercise["options"]]
    texts = [o["text"].strip().casefold() for o in exercise["options"]]
    assert exercise["type"] == "single_choice"
    assert len(option_ids) == 3 and len(set(option_ids)) == 3
    assert len(set(texts)) == 3, "duplicate option text"
    assert exercise["correct_option_id"] in option_ids
    assert exercise["explanation"].strip()
    assert exercise["points"] == 1


@pytest.mark.parametrize("course,lesson,exercise", EXERCISES, ids=ids(EXERCISES))
def test_exercise_prompt_asks_for_an_answer(course: dict, lesson: dict, exercise: dict) -> None:
    prompt = exercise["prompt"]
    assert (
        "___" in prompt
        or "=" in prompt
        or prompt.rstrip().endswith("?")
        or re.match(r"(Choose|Write|Which)\b", prompt)
    ), prompt


@pytest.mark.parametrize("course,lesson,exercise", EXERCISES, ids=ids(EXERCISES))
def test_explanation_names_the_correct_answer(course: dict, lesson: dict, exercise: dict) -> None:
    answer = correct_text(exercise)
    assert answer in exercise["explanation"], exercise["explanation"]


def test_check_exercises_match_the_lesson_vocabulary() -> None:
    for _, lesson in LESSONS:
        vocab = {v["word"].casefold(): v["translation"] for v in lesson["vocabulary"]}
        translations = set(vocab.values())
        for e in lesson["exercises"]:
            if e["phase"] != "check":
                continue
            word = re.search(r'"([^"]+)"', e["prompt"]).group(1).casefold()
            assert vocab[word] == correct_text(e), e["slug"]
            assert {o["text"] for o in e["options"]} <= translations, e["slug"]


def test_no_prompt_is_repeated() -> None:
    prompts = Counter(e["prompt"].strip().casefold() for *_, e in EXERCISES)
    assert [p for p, n in prompts.items() if n > 1] == []


# --------------------------------------------------------------------------- seed catalog


def seed_lessons():
    return [(c, lesson) for c in SEED_COURSES for lesson in c["lessons"]]


def seed_exercises():
    return [(slug, e) for slug, items in SEED_EXERCISES.items() for e in items]


def test_seed_catalog_is_consistent() -> None:
    lessons = seed_lessons()
    slugs = [lesson["slug"] for _, lesson in lessons]
    assert len(slugs) == len(set(slugs))
    assert set(SEED_EXERCISES) <= set(slugs), "exercises reference unknown lessons"
    assert set(slugs) <= set(SEED_EXERCISES), "lesson without exercises"
    assert all(c["level"] in LEARNING_LEVELS for c in SEED_COURSES)
    for course in SEED_COURSES:
        assert [x["position"] for x in course["lessons"]] == list(
            range(1, len(course["lessons"]) + 1)
        )
    exercise_slugs = [e["slug"] for _, e in seed_exercises()]
    assert len(exercise_slugs) == len(set(exercise_slugs))
    for lesson_slug, items in SEED_EXERCISES.items():
        assert [e["position"] for e in items] == list(range(1, len(items) + 1))
        assert all(e["slug"].startswith(lesson_slug + "-") for e in items)


@pytest.mark.parametrize(
    "lesson_slug,exercise", seed_exercises(), ids=lambda x: x if isinstance(x, str) else x["slug"]
)
def test_seed_exercise_grading_data(lesson_slug: str, exercise: dict) -> None:
    assert exercise["prompt"].strip() and exercise["explanation"].strip()
    kind = exercise["type"]
    if kind == "single_choice":
        option_ids = [o["id"] for o in exercise["options"]]
        assert len(set(option_ids)) == len(option_ids) >= 2
        assert exercise["correct_option_id"] in option_ids
        assert len({o["text"].casefold() for o in exercise["options"]}) == len(option_ids)
    elif kind == "text":
        answers = exercise["accepted_answers"]
        assert answers
        # Grading normalises the submission only, so stored answers must already be normalised.
        assert all(a == normalize_text(a) for a in answers)
        tiles = exercise.get("letter_tiles")
        if tiles:
            blanks = tiles["pattern"].count("_")
            for answer in answers:
                assert len(answer) == len(tiles["pattern"])
                missing = [ch for ch, p in zip(answer, tiles["pattern"], strict=True) if p == "_"]
                assert len(missing) == blanks
                assert not (Counter(missing) - Counter(tiles["letters"])), (
                    "letters cannot fill blanks"
                )
    else:
        assert kind == "self_check" and exercise["model_answer"].strip()


# --------------------------------------------------------------------------- known defects (audit)

AUDIT = "docs/qa/learning-content-audit.md"


@pytest.mark.xfail(strict=True, reason=f"{AUDIT}: all 500 vocabulary examples are empty")
def test_vocabulary_has_example_sentences() -> None:
    assert all(v["example"].strip() for _, lesson in LESSONS for v in lesson["vocabulary"])


@pytest.mark.xfail(strict=True, reason=f"{AUDIT}: every lesson uses the same answer positions")
def test_correct_answer_positions_vary_between_lessons() -> None:
    patterns = {tuple(e["correct_option_id"] for e in lesson["exercises"]) for _, lesson in LESSONS}
    assert len(patterns) > 1


@pytest.mark.xfail(strict=True, reason=f"{AUDIT}: 145 practice items repeat the worked examples")
def test_practice_items_are_not_the_worked_examples() -> None:
    def norm(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", text.casefold().replace("’", "'").replace("'", ""))

    repeated = 0
    for _, lesson in LESSONS:
        examples = norm(" ".join(lesson["examples"]))
        for e in lesson["exercises"]:
            if e["phase"] == "practice" and "___" in e["prompt"]:
                filled = re.sub(r"\([^)]*\)", "", e["prompt"]).replace("___", correct_text(e))
                repeated += norm(filled).strip() in examples
    assert repeated == 0


@pytest.mark.xfail(strict=True, reason=f"{AUDIT}: 83 vocabulary words never appear in the lesson")
def test_every_vocabulary_word_is_used_in_its_lesson() -> None:
    def norm(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", text.casefold().replace("’", "'").replace("'", ""))

    for _, lesson in LESSONS:
        body = norm(
            " ".join(
                [lesson["theory"], lesson["reading"], *lesson["examples"]]
                + [
                    e["prompt"] + " " + " ".join(o["text"] for o in e["options"])
                    for e in lesson["exercises"]
                ]
            )
        )
        for v in lesson["vocabulary"]:
            assert norm(v["word"]) in body, (lesson["slug"], v["word"])


# Fixed after the audit (branch fix/published-content): kept as regression tests.


def test_seed_text_answers_accept_typographic_apostrophe() -> None:
    for _, e in seed_exercises():
        for answer in e.get("accepted_answers") or []:
            if "'" in answer:
                curly = answer.replace("'", "\u2019")
                assert normalize_text(curly) in {normalize_text(a) for a in e["accepted_answers"]}


def test_seed_lessons_have_distinct_theory() -> None:
    theories = Counter(lesson["theory"] for _, lesson in seed_lessons())
    assert max(theories.values()) == 1
