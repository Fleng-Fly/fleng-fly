"""Published seed content: equivalent answers are accepted, wrong answers stay wrong."""

import zlib
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed import SEED_COURSES, SEED_EXERCISES, seed_catalog
from app.modules.exercises.grading import grade_objective, normalize_text

TEXT_EXERCISES = [
    (slug, e) for slug, items in SEED_EXERCISES.items() for e in items if e["type"] == "text"
]


def text_exercise(answers: list[str]) -> SimpleNamespace:
    return SimpleNamespace(type="text", accepted_answers=answers)


# ------------------------------------------------------------------ normalisation


@pytest.mark.parametrize(
    "raw",
    ["I’m", "I‘m", "I´m", "I`m", "Iʼm", "  I'M  ", "I'm.", "I'm!", "“I’m”"],
)
def test_apostrophes_case_and_end_punctuation_are_equivalent(raw: str) -> None:
    assert normalize_text(raw) == "i'm"
    assert grade_objective(text_exercise(["i'm"]), raw)


@pytest.mark.parametrize(
    "raw",
    [
        "Nice to meet you too.",
        "nice to meet you, too",
        "Nice to meet you too!",
        "NICE   TO MEET  YOU TOO",
        "Nice to meet you too…",
    ],
)
def test_optional_punctuation_does_not_change_a_correct_phrase(raw: str) -> None:
    assert grade_objective(text_exercise(["nice to meet you too"]), raw)


def test_accepted_answers_are_normalised_the_same_way() -> None:
    exercise = text_exercise(["I’m", "Nice to meet you, too."])
    assert grade_objective(exercise, "i'm")
    assert grade_objective(exercise, "nice to meet you too")


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "...",
        "too",
        "meet you too",
        "nice to meet you",
        "nice to meet you too much",
        "nice to meet you tho",
        "im m",
        "i am",
        "i’m not",
    ],
)
def test_wrong_or_incomplete_answers_stay_wrong(raw: str) -> None:
    exercise = text_exercise(["nice to meet you too", "i'm"])
    assert not grade_objective(exercise, raw)


def test_punctuation_never_joins_or_alters_words() -> None:
    assert normalize_text("nice,to.meet") == "nice to meet"
    assert normalize_text("well-known") == "well-known"
    assert not grade_objective(text_exercise(["been"]), "bean")
    assert not grade_objective(text_exercise(["ever"]), "never")
    assert not grade_objective(text_exercise(["twelve"]), "twelf")
    assert not grade_objective(text_exercise(["twelve"]), "twelve twelve")


def test_single_choice_is_still_an_exact_id_match() -> None:
    exercise = SimpleNamespace(type="single_choice", correct_option_id="b")
    assert grade_objective(exercise, "b")
    for wrong in ("B", " b", "b.", "a", ""):
        assert not grade_objective(exercise, wrong)


# ------------------------------------------------------------------ every published text exercise


@pytest.mark.parametrize(
    "lesson_slug,exercise", TEXT_EXERCISES, ids=lambda x: x if isinstance(x, str) else x["slug"]
)
def test_every_published_answer_survives_typing_variants(lesson_slug: str, exercise: dict) -> None:
    graded = SimpleNamespace(type="text", accepted_answers=exercise["accepted_answers"])
    for answer in exercise["accepted_answers"]:
        for variant in (
            answer,
            answer.upper(),
            f"  {answer}. ",
            f"{answer}!",
            answer.replace("'", "’"),
        ):
            assert grade_objective(graded, variant), (exercise["slug"], variant)
        # Dropping a letter or adding one must be rejected (strict for real mistakes).
        assert not grade_objective(graded, answer[:-1]), (exercise["slug"], answer)
        assert not grade_objective(graded, answer + "x"), (exercise["slug"], answer)


def test_published_exercises_have_equivalent_answers_listed() -> None:
    replies = next(e for e in SEED_EXERCISES["greetings-and-introductions"] if e["position"] == 2)
    graded = SimpleNamespace(type="text", accepted_answers=replies["accepted_answers"])
    for ok in ("You too!", "Likewise.", "It’s nice to meet you too", "Pleased to meet you, too"):
        assert grade_objective(graded, ok), ok
    for bad in ("Nice to meet you", "Goodbye", "Hello", "Me neither"):
        assert not grade_objective(graded, bad), bad


def test_present_perfect_practice_has_its_own_material() -> None:
    lessons = {lesson["slug"]: lesson for c in SEED_COURSES for lesson in c["lessons"]}
    practice = lessons["present-perfect-practice"]
    original = lessons["past-experiences"]
    assert practice["theory"] != original["theory"]
    practice_prompts = {e["prompt"] for e in SEED_EXERCISES["present-perfect-practice"]}
    original_prompts = {e["prompt"] for e in SEED_EXERCISES["past-experiences"]}
    assert not practice_prompts & original_prompts
    # No exercise reuses the stem of "Have you ___ been to Ireland?" from the original lesson.
    assert all("Have you ___ been to Ireland" not in p for p in practice_prompts)


# ------------------------------------------------------------------ through the API


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_catalog(db_session)
    return db_session


async def _answer(client: AsyncClient, email: str, lesson: str, exercise: str, answer: str) -> dict:
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery", "displayName": "Learner"},
    )
    headers = {"Authorization": f"Bearer {registered.json()['accessToken']}"}
    body = (await client.get(f"/api/v1/lessons/{lesson}")).json()
    exercise_id = next(e["id"] for e in body["exercises"] if e["slug"] == exercise)
    response = await client.post(
        f"/api/v1/lessons/{lesson}/submit",
        json={"exerciseId": exercise_id, "answer": answer},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    "lesson,exercise,answer,correct",
    [
        ("the-verb-to-be", "the-verb-to-be-q2", "I’m", True),
        ("the-verb-to-be", "the-verb-to-be-q2", "I'm.", True),
        ("the-verb-to-be", "the-verb-to-be-q2", "I am", False),
        (
            "greetings-and-introductions",
            "greetings-and-introductions-q2",
            "Nice to meet you too.",
            True,
        ),
        ("greetings-and-introductions", "greetings-and-introductions-q2", "You too!", True),
        ("greetings-and-introductions", "greetings-and-introductions-q2", "Goodbye", False),
        ("present-perfect-practice", "present-perfect-practice-q3", "Never.", True),
        ("present-perfect-practice", "present-perfect-practice-q3", "ever", False),
    ],
)
async def test_submission_endpoint_uses_equivalence_rules(
    client: AsyncClient,
    seeded: AsyncSession,
    lesson: str,
    exercise: str,
    answer: str,
    correct: bool,
) -> None:
    email = f"learner-{abs(zlib.crc32(f'{exercise}|{answer}'.encode()))}@example.com"
    result = await _answer(client, email, lesson, exercise, answer)
    assert result["isCorrect"] is correct
