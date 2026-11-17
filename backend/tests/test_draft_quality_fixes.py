"""Guard the candidate's content, answer associations and separation from the release.

Mechanical checks do not establish English/CEFR correctness or teacher approval.
"""

import json
import re
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.db.curriculum import content_sha, import_curriculum, load_curriculum
from app.db.models import Course, Exercise
from app.db.prepare import OWNER_AUTHORIZED_CURRICULUM_SHA
from app.modules.exercises.grading import grade_objective

ROOT = Path(__file__).resolve().parents[1] / "app/db/content"
SOURCE = ROOT / "curriculum-a0-b2.json"
DRAFT = ROOT / "curriculum-a0-b2.draft.json"
RELEASE = json.loads(SOURCE.read_text())
CANDIDATE = json.loads(DRAFT.read_text())
LESSONS = [lesson for c in CANDIDATE["courses"] for lesson in c["lessons"]]
ORIGINAL = {lesson["slug"]: lesson for c in RELEASE["courses"] for lesson in c["lessons"]}
EXERCISES = [e for lesson in LESSONS for e in lesson["exercises"]]
CHANGED_ANSWERS = {
    "fleng-a0-letters-practice-3": "L-E-A",
    "fleng-a0-numbers-practice-1": "fourteen",
    "fleng-a0-numbers-practice-2": "eighteen",
    "fleng-a0-numbers-practice-3": "seven",
    "fleng-a0-objects-practice-3": "cups",
    "fleng-b1-opinion-practice-3": "The trial succeeded. However, demand was low.",
}


def answer(e):
    return next(o["text"] for o in e["options"] if o["id"] == e["correct_option_id"])


def contains(word, body):
    return re.search(r"(?<!\w)" + re.escape(word.casefold()) + r"(?!\w)", body.casefold())


def test_release_is_still_the_pinned_source_and_candidate_is_not_approved():
    assert content_sha(load_curriculum()) == OWNER_AUTHORIZED_CURRICULUM_SHA
    candidate = load_curriculum(DRAFT)
    assert content_sha(candidate) != OWNER_AUTHORIZED_CURRICULUM_SHA
    assert candidate.status == "draft" and all(c.status == "draft" for c in candidate.courses)
    assert len(candidate.courses) == 5
    assert len(LESSONS) == 50 and len(EXERCISES) == 400
    assert sum(len(lesson.vocabulary) for c in candidate.courses for lesson in c.lessons) == 500


def test_lesson_structure_metadata_and_glosses_unchanged():
    for before, after in zip(RELEASE["courses"], CANDIDATE["courses"], strict=True):
        assert {k: v for k, v in before.items() if k != "lessons"} == {
            k: v for k, v in after.items() if k != "lessons"
        }
    for lesson in LESSONS:
        old = ORIGINAL[lesson["slug"]]
        unchanged = set(old) - {"reading", "vocabulary", "exercises"}
        assert {k: old[k] for k in unchanged} == {k: lesson[k] for k in unchanged}
        assert [(v["word"], v["translation"]) for v in old["vocabulary"]] == [
            (v["word"], v["translation"]) for v in lesson["vocabulary"]
        ]
        assert [e["slug"] for e in old["exercises"]] == [e["slug"] for e in lesson["exercises"]]
        assert lesson["reading"].startswith(old["reading"])


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda lesson: lesson["slug"])
def test_examples_are_short_sentences_using_each_word(lesson):
    assert len(lesson["vocabulary"]) == 10
    for word in lesson["vocabulary"]:
        example = word["example"]
        assert contains(word["word"], example), (word["word"], example)
        assert example[0].isupper() and example[-1] in ".!?", example
        assert 2 <= len(example.split()) <= 25
        assert not re.search(r"<[^>]+>|___|TODO|TBD", example)
    # Context in the lesson itself, not only the separate vocabulary example field.
    body = " ".join(
        [lesson["theory"], lesson["reading"], *lesson["examples"]]
        + [e["prompt"] + " " + answer(e) for e in lesson["exercises"]]
    )
    for word in lesson["vocabulary"]:
        assert contains(word["word"], body), (lesson["slug"], word["word"])


@pytest.mark.parametrize("exercise", EXERCISES, ids=lambda e: e["slug"])
def test_every_key_selects_the_expected_answer_and_real_grader_agrees(exercise):
    lesson_slug = exercise["slug"].rsplit("-", 2)[0]
    old = next(e for e in ORIGINAL[lesson_slug]["exercises"] if e["slug"] == exercise["slug"])
    expected = CHANGED_ANSWERS.get(exercise["slug"], answer(old))
    assert answer(exercise) == expected
    assert expected in exercise["explanation"]
    assert exercise["type"] == old["type"] and exercise["points"] == old["points"]
    assert exercise["position"] == old["position"] and exercise["phase"] == old["phase"]
    if exercise["slug"] not in CHANGED_ANSWERS:
        old_texts = [o["text"] for o in old["options"]]
        if exercise["slug"] in {
            "fleng-a2-conditions-practice-2",
            "fleng-a2-travel-problem-practice-3",
        }:
            old_texts = ["was" if text == "would" else text for text in old_texts]
        assert Counter(o["text"] for o in exercise["options"]) == Counter(old_texts)
    if exercise["phase"] == "check":
        assert exercise["prompt"] == old["prompt"]
    model = Exercise(
        type="single_choice",
        options=exercise["options"],
        correct_option_id=exercise["correct_option_id"],
    )
    for option in exercise["options"]:
        assert grade_objective(model, option["id"]) is (option["text"] == expected)


def test_all_confirmed_repetitions_and_five_nonblank_copies_are_replaced():
    def norm(text):
        return re.sub(r"[^a-z0-9 ]", "", text.casefold().replace("’", "'").replace("'", ""))

    copies = blank_copies = 0
    for lesson in LESSONS:
        old = ORIGINAL[lesson["slug"]]
        for before, after in zip(old["exercises"], lesson["exercises"], strict=True):
            filled = re.sub(r"\([^)]*\)", "", before["prompt"]).replace("___", answer(before))
            repeated = before["phase"] == "practice" and norm(filled).strip() in norm(
                " ".join(old["examples"])
            )
            if repeated:
                copies += 1
                blank_copies += "___" in before["prompt"]
                # A punctuation-choice task has a generic stem; its complete-sentence
                # options, rather than its label, carry the independent question.
                assert (after["prompt"], answer(after)) != (before["prompt"], answer(before)), (
                    after["slug"]
                )
            else:
                assert after["prompt"] == before["prompt"], after["slug"]
    assert copies == 150 and blank_copies == 145


async def test_candidate_import_is_draft_and_rejects_existing_release_approval(db_session):
    candidate = load_curriculum(DRAFT)
    with pytest.raises(ValueError, match="SHA"):
        await import_curriculum(
            db_session, candidate, apply=True, owner_authorized_sha=OWNER_AUTHORIZED_CURRICULUM_SHA
        )
    report = await import_curriculum(db_session, candidate, apply=True)
    assert report["status"] == "draft"
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Course).where(Course.is_published.is_(True))
        )
        == 0
    )
