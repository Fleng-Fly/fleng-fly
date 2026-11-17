"""Hints, EN/UK explanations and lesson guides (authored sidecar content, no AI)."""

import re
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.curriculum import content_sha, import_curriculum, load_curriculum
from app.db.prepare import OWNER_AUTHORIZED_CURRICULUM_SHA
from app.modules.exercises import guidance
from app.modules.exercises.guidance import load_guidance

PASSWORD = "correct-horse-battery"
LESSON = "fleng-a0-hello"


def _early_exercises():
    content = load_curriculum()
    for course in content.courses[:2]:
        for lesson in course.lessons:
            for exercise in lesson.exercises:
                yield lesson, exercise


def _norm(text: str) -> str:
    return text.casefold().strip()


def test_curriculum_is_untouched_by_guidance() -> None:
    """Guidance lives beside the pinned curriculum; its publication SHA must not move."""
    assert content_sha(load_curriculum()) == OWNER_AUTHORIZED_CURRICULUM_SHA


def test_every_a0_a1_exercise_has_bilingual_hint_and_explanation() -> None:
    file = load_guidance()
    assert file.levels == ["A0", "A1"]
    expected = {e.slug for _, e in _early_exercises()}
    covered = {slug for lesson in file.lessons.values() for slug in lesson.exercises}
    assert covered == expected and len(expected) == 160
    for lesson in file.lessons.values():
        for text in (lesson.explanation, *(ex.explanation for ex in lesson.exercises.values())):
            assert text.en.strip() and text.uk.strip()
        for entry in lesson.exercises.values():
            assert entry.hint.en.strip() and entry.hint.uk.strip()
            assert _norm(entry.hint.en) != _norm(entry.explanation.en)
            # Ukrainian text really is Ukrainian, not an English copy.
            assert re.search(r"[іїєґа-я]", entry.hint.uk, re.I)
            assert re.search(r"[іїєґа-я]", entry.explanation.uk, re.I)


def test_hints_never_contain_the_correct_answer() -> None:
    file = load_guidance()
    leaks = []
    for lesson, exercise in _early_exercises():
        options = {o.id: o.text for o in exercise.options}
        correct = options[exercise.correct_option_id]
        hint = file.lessons[lesson.slug].exercises[exercise.slug].hint
        if len(correct) < 2:
            continue  # single letters (a, I) occur in ordinary words
        pattern = r"(?<![\w'’-])" + re.escape(correct) + r"(?![\w'’-])"
        # Vocabulary checks quote the English word asked about, never the Ukrainian answer.
        if re.search(pattern, hint.en, re.I) or re.search(pattern, hint.uk, re.I):
            leaks.append((exercise.slug, correct))
    assert leaks == []


def test_wrong_answer_notes_refer_to_real_options() -> None:
    file = load_guidance()
    for lesson, exercise in _early_exercises():
        spec = file.lessons[lesson.slug]
        texts = {_norm(o.text) for o in exercise.options}
        correct = _norm({o.id: o.text for o in exercise.options}[exercise.correct_option_id])
        for key in spec.exercises[exercise.slug].wrong:
            assert key in texts and key != correct, (exercise.slug, key)
    for lesson in load_curriculum().courses[0].lessons + load_curriculum().courses[1].lessons:
        used = {_norm(o.text) for e in lesson.exercises for o in e.options}
        for key in file.lessons[lesson.slug].option_notes:
            assert key in used, (lesson.slug, key)


@pytest_asyncio.fixture
async def imported(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    content = load_curriculum()
    await import_curriculum(db_session, content, apply=True, reviewed_sha=content_sha(content))
    yield db_session


async def _token(client: AsyncClient, email: str = "guide@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "displayName": "Guide"},
    )
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


async def _lesson(client: AsyncClient) -> dict:
    return (await client.get(f"/api/v1/lessons/{LESSON}")).json()


async def test_lesson_exposes_hint_and_guide_but_no_answers(
    client: AsyncClient, imported: AsyncSession
) -> None:
    body = await _lesson(client)
    assert body["guide"]["explanation"]["en"] and body["guide"]["explanation"]["uk"]
    assert len(body["guide"]["examples"]) >= 2
    for exercise in body["exercises"]:
        assert exercise["hint"]["en"] and exercise["hint"]["uk"]
        for secret in ("correctOptionId", "explanation", "explanationLocalized", "wrongAnswerNote"):
            assert secret not in exercise
    # Nothing in the public payload carries the authored explanations.
    guidance_file = load_guidance().lessons[LESSON]
    raw = str(body)
    for entry in guidance_file.exercises.values():
        assert entry.explanation.en not in raw


async def test_submission_reveals_explanation_and_wrong_note_without_changing_xp(
    client: AsyncClient, imported: AsyncSession
) -> None:
    auth = await _token(client)
    lesson = await _lesson(client)
    exercise = next(e for e in lesson["exercises"] if e["slug"].endswith("practice-1"))
    await client.post(f"/api/v1/lessons/{LESSON}/start", headers=auth)
    wrong = next(o for o in exercise["options"] if o["text"] == "are")
    miss = await client.post(
        f"/api/v1/lessons/{LESSON}/submit",
        headers=auth,
        json={"exerciseId": exercise["id"], "answer": wrong["id"]},
    )
    result = miss.json()
    assert result["isCorrect"] is False and result["xpAwarded"] == 0
    assert result["explanationLocalized"]["uk"] and result["explanationLocalized"]["en"]
    assert "“are” goes with" in result["wrongAnswerNote"]["en"]
    assert result["explanation"]  # existing English field is unchanged
    right = next(o for o in exercise["options"] if o["id"] == result["correctOptionId"])
    hit = await client.post(
        f"/api/v1/lessons/{LESSON}/submit",
        headers=auth,
        json={"exerciseId": exercise["id"], "answer": right["id"]},
    )
    solved = hit.json()
    assert solved["isCorrect"] is True and solved["xpAwarded"] == 1
    assert solved["wrongAnswerNote"] is None and solved["explanationLocalized"]["uk"]


async def test_vocabulary_checks_name_the_word_behind_a_wrong_translation(
    client: AsyncClient, imported: AsyncSession
) -> None:
    auth = await _token(client, "vocab@example.com")
    lesson = await _lesson(client)
    exercise = next(e for e in lesson["exercises"] if e["slug"].endswith("check-1"))
    await client.post(f"/api/v1/lessons/{LESSON}/start", headers=auth)
    for option in exercise["options"]:
        result = (
            await client.post(
                f"/api/v1/lessons/{LESSON}/submit",
                headers=auth,
                json={"exerciseId": exercise["id"], "answer": option["id"]},
            )
        ).json()
        if not result["isCorrect"] and result["wrongAnswerNote"]:
            assert "not of" in result["wrongAnswerNote"]["en"]
            break
    else:
        pytest.fail("expected a wrong-answer note for a translation from the same lesson")


def test_unreviewed_guidance_is_never_served_in_production(monkeypatch) -> None:
    assert load_guidance().review_status == "draft"
    monkeypatch.setattr(guidance, "drafts_allowed", lambda: True)
    assert guidance.hint_for("fleng-a0-hello-practice-1") is not None
    monkeypatch.setattr(guidance, "drafts_allowed", lambda: False)
    assert guidance.hint_for("fleng-a0-hello-practice-1") is None
    assert guidance.lesson_guide_for(LESSON) is None
    assert guidance.wrong_note_for("fleng-a0-hello-practice-1", "are") is None


def test_unknown_or_later_level_exercises_have_no_guidance() -> None:
    assert guidance.hint_for("fleng-a2-routines-practice-1") is None
    assert guidance.lesson_guide_for("the-verb-to-be") is None
