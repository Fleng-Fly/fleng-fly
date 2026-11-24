"""Placement is owned, deterministic, resumable and independent of learning writes."""

import copy
from collections import Counter
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.models import (
    Achievement,
    Course,
    ExerciseSubmission,
    LearningActivity,
    LessonProgress,
    PlacementAttempt,
    Profile,
    Progress,
    UserAchievement,
)
from app.db.seed import seed_catalog
from app.modules.placement import bank, scoring
from tests.test_learning_extensions import headers

BASE = "/api/v1/placement-test/attempts"


async def start(client, auth):
    response = await client.post(BASE, headers=auth)
    assert response.status_code == 201, response.text
    return response.json()


def private_answers(questions, correct=True):
    return {
        q["id"]: q["correct_option_id"]
        if correct
        else next(option["id"] for option in q["options"] if option["id"] != q["correct_option_id"])
        for q in questions
    }


async def fill(client, auth, attempt, answers):
    response = await client.put(
        f"{BASE}/{attempt['id']}/answers",
        headers=auth,
        json={
            "answers": [{"questionId": key, "optionId": value} for key, value in answers.items()]
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def assert_private(value):
    if isinstance(value, dict):
        assert (
            not {"correctOptionId", "correct_option_id", "explanation", "isCorrect"} & value.keys()
        )
        for child in value.values():
            assert_private(child)
    elif isinstance(value, list):
        for child in value:
            assert_private(child)


def test_bank_integrity_and_originality_metadata():
    data = bank.load_bank()
    assert len(data["questions"]) == 36
    assert Counter(q["level"] for q in data["questions"]) == dict.fromkeys(bank.LEVELS, 6)
    assert data["review_status"] == "internal_checks_only"
    assert "no external" in data["provenance"]
    assert {q["correct_option_id"] for q in data["questions"]} == {"a", "b", "c", "d"}
    for question in data["questions"]:
        assert (
            sum(option["id"] == question["correct_option_id"] for option in question["options"])
            == 1
        )
        assert len(question["explanation"]) > 20


@pytest.mark.parametrize(
    "correct_bands,expected",
    [
        ([], None),
        (["A1"], "A1"),
        (["A1", "A2"], "A2"),
        (["A1", "A2", "B1"], "B1"),
        (list(bank.LEVELS), "B2"),
        (["B2", "C1", "C2"], None),
        (["A1", "B1", "B2", "C1", "C2"], "A1"),
    ],
)
def test_consecutive_bands_and_advanced_ceiling(correct_bands, expected):
    questions = bank.load_bank()["questions"]
    answers = private_answers(questions, False)
    for q in questions:
        if q["level"] in correct_bands:
            answers[q["id"]] = q["correct_option_id"]
    result = scoring.score(questions, answers)
    assert result["estimated_level"] == expected
    assert result["reliability"] == "limited"
    assert result["assessment_range"] == "A1–B2"
    assert len(result["review"]) == 36
    if expected == "B2":
        assert result["ceiling_reached"] is True
        assert "C1/C2 are not determined" in result["label"]


def test_five_of_six_boundary_and_insufficient_bank():
    questions = copy.deepcopy(bank.load_bank()["questions"])
    answers = private_answers(questions)
    a1 = [q for q in questions if q["level"] == "A1"]
    answers[a1[0]["id"]] = private_answers(a1, False)[a1[0]["id"]]
    assert scoring.score(questions, answers)["estimated_level"] == "B2"
    answers[a1[1]["id"]] = private_answers(a1, False)[a1[1]["id"]]
    assert scoring.score(questions, answers)["estimated_level"] is None
    short = [q for q in questions if q["level"] in {"A1", "A2"}]
    result = scoring.score(short, private_answers(short))
    assert result["estimated_level"] == "A2" and result["assessment_range"] == "A1–A2"
    too_short = a1[:5]
    result = scoring.score(too_short, private_answers(too_short))
    assert result["estimated_level"] is None and result["insufficient_evidence"] is True
    assert result["assessment_range"] == "Not established"


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("post", BASE, None),
        ("get", BASE, None),
        ("get", BASE + "/00000000-0000-0000-0000-000000000001", None),
        (
            "put",
            BASE + "/00000000-0000-0000-0000-000000000001/answers",
            {"answers": [{"questionId": "q01", "optionId": "a"}]},
        ),
        ("post", BASE + "/00000000-0000-0000-0000-000000000001/complete", None),
    ],
)
async def test_placement_requires_authentication(client, method, path, payload):
    response = (
        await getattr(client, method)(path, json=payload)
        if method != "get"
        else await client.get(path)
    )
    assert response.status_code == 401


async def test_ownership_history_and_answers_are_private(client):
    owner = await headers(client)
    other = await headers(client, "placement-other@example.com")
    attempt = await start(client, owner)
    assert_private(attempt)
    assert attempt["result"] is None and attempt["answers"] == {}
    assert len(attempt["questions"]) == 36
    for method, suffix in [("get", ""), ("put", "/answers"), ("post", "/complete")]:
        kwargs = {"headers": other}
        if method == "put":
            kwargs["json"] = {"answers": [{"questionId": "q01", "optionId": "a"}]}
        response = await getattr(client, method)(f"{BASE}/{attempt['id']}{suffix}", **kwargs)
        assert response.status_code == 404
    assert (await client.get(BASE, headers=other)).json() == []
    own_history = (await client.get(BASE, headers=owner)).json()
    assert len(own_history) == 1 and own_history[0]["id"] == attempt["id"]
    assert_private(own_history)
    assert (await client.get(f"{BASE}/{uuid4()}", headers=owner)).status_code == 404


async def test_autosave_resume_validation_and_no_early_feedback(client):
    auth = await headers(client)
    attempt = await start(client, auth)
    endpoint = f"{BASE}/{attempt['id']}"
    q = attempt["questions"][0]
    answer = {q["id"]: q["options"][0]["id"]}
    saved = await fill(client, auth, attempt, answer)
    assert saved["answers"] == answer and saved["answered"] == 1
    assert_private(saved)
    assert (await client.get(endpoint, headers=auth)).json()["answers"] == answer
    incomplete = await client.post(endpoint + "/complete", headers=auth)
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "PLACEMENT_INCOMPLETE"
    assert_private((await client.get(endpoint, headers=auth)).json())
    for payload in [
        {"answers": []},
        {"answers": [{"questionId": "unknown", "optionId": "a"}]},
        {"answers": [{"questionId": q["id"], "optionId": "unknown"}]},
        {"answers": [{"questionId": q["id"], "optionId": "a"}] * 2},
        {"answers": [{"questionId": q["id"], "optionId": "a", "isCorrect": True}]},
        {"answers": [{"questionId": q["id"], "optionId": "a"}], "estimatedLevel": "C2"},
    ]:
        response = await client.put(endpoint + "/answers", headers=auth, json=payload)
        assert response.status_code == 422, response.text
    assert (await client.get(endpoint, headers=auth)).json()["answers"] == answer
    changed = await client.put(
        endpoint + "/answers",
        headers=auth,
        json={"answers": [{"questionId": q["id"], "optionId": q["options"][1]["id"]}]},
    )
    assert changed.status_code == 409
    assert (await fill(client, auth, attempt, answer))["answers"] == answer


async def learning_snapshot(db):
    profile = await db.scalar(select(Profile))
    progress = await db.scalar(select(Progress))
    values = {
        "profile": (profile.xp, profile.level, profile.english_level),
        "progress": (
            progress.lessons_started,
            progress.lessons_completed,
            progress.study_minutes,
            progress.last_activity_at,
        ),
    }
    for model in [
        Course,
        ExerciseSubmission,
        LessonProgress,
        LearningActivity,
        UserAchievement,
        Achievement,
    ]:
        values[model.__name__] = await db.scalar(select(func.count()).select_from(model))
    return values


async def test_complete_retake_recommendations_and_zero_learning_writes(client, db_session):
    auth = await headers(client)
    await seed_catalog(db_session)
    from tests.test_exercises import _complete_greetings

    await _complete_greetings(client, auth["Authorization"].removeprefix("Bearer "))
    db_session.add_all(
        [
            Course(
                slug="placement-b2",
                title="B2 published",
                description="Course",
                level="B2",
                is_published=True,
            ),
            Course(
                slug="placement-draft",
                title="B2 draft",
                description="Draft",
                level="B2",
                is_published=False,
            ),
        ]
    )
    await db_session.commit()
    before = await learning_snapshot(db_session)
    assert before["profile"][0] > 0
    assert before["progress"][1] > 0
    first = await start(client, auth)
    private = await db_session.get(PlacementAttempt, UUID(first["id"]))
    await fill(client, auth, first, private_answers(private.questions))
    complete_url = f"{BASE}/{first['id']}/complete"
    result = (await client.post(complete_url, headers=auth)).json()
    assert result["result"]["correct"] == 36
    assert result["result"]["estimatedLevel"] == "B2"
    assert len(result["result"]["review"]) == 36
    listed = {a["id"]: a for a in (await client.get(BASE, headers=auth)).json()}[first["id"]]
    assert (listed["correct"], listed["total"], listed["estimatedLevel"]) == (36, 36, "B2")
    assert [c["slug"] for c in result["recommendedCourses"]] == ["placement-b2"]
    again = (await client.post(complete_url, headers=auth)).json()
    assert result == again
    immutable = await client.put(
        f"{BASE}/{first['id']}/answers",
        headers=auth,
        json={"answers": [{"questionId": "q01", "optionId": "a"}]},
    )
    assert immutable.status_code == 409
    second = await start(client, auth)
    assert second["id"] != first["id"] and second["answers"] == {}
    private_second = await db_session.get(PlacementAttempt, UUID(second["id"]))
    await fill(client, auth, second, private_answers(private_second.questions, False))
    low = (await client.post(f"{BASE}/{second['id']}/complete", headers=auth)).json()
    assert low["result"]["correct"] == 0 and low["result"]["estimatedLevel"] is None
    assert all(c["level"] == "A0" for c in low["recommendedCourses"])
    history = (await client.get(BASE, headers=auth)).json()
    assert len(history) == 2 and all(row["status"] == "completed" for row in history)
    assert (await client.get(f"{BASE}/{first['id']}", headers=auth)).json() == result

    retry = await client.post(f"{BASE}/{second['id']}/retry-mistakes", headers=auth)
    assert retry.status_code == 201
    practice = retry.json()
    assert practice["practice"] is True and practice["total"] == 36
    await fill(client, auth, practice, private_answers(private_second.questions))
    reviewed = (await client.post(f"{BASE}/{practice['id']}/complete", headers=auth)).json()
    assert reviewed["result"]["correct"] == 36
    assert reviewed["result"]["estimatedLevel"] is None
    assert reviewed["recommendedCourses"] == []
    assert (await client.get(BASE, headers=auth)).json() == history
    assert before == await learning_snapshot(db_session)


async def test_existing_snapshot_survives_bank_change_and_no_course_fabrication(
    client, db_session, monkeypatch
):
    auth = await headers(client)
    attempt = await start(client, auth)
    private = await db_session.get(PlacementAttempt, UUID(attempt["id"]))
    answers = private_answers(private.questions)
    monkeypatch.setattr("app.modules.placement.service.load_bank", lambda: {"questions": []})
    await fill(client, auth, attempt, answers)
    result = (await client.post(f"{BASE}/{attempt['id']}/complete", headers=auth)).json()
    assert result["result"]["correct"] == 36
    assert result["recommendedCourses"] == []
    assert "No published B2 course" in result["recommendationNote"]


async def test_history_pagination_validation_and_start_limit(client):
    auth = await headers(client)
    for _ in range(20):
        await start(client, auth)
    assert len((await client.get(BASE + "?limit=7&offset=7", headers=auth)).json()) == 7
    assert (await client.get(BASE + "?offset=20", headers=auth)).json() == []
    assert (await client.get(BASE + "?limit=101", headers=auth)).status_code == 422
    assert (await client.get(BASE + "?offset=-1", headers=auth)).status_code == 422
    refused = await client.post(BASE, headers=auth)
    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 0


async def test_placement_page_and_assets_are_served(client):
    for path in [
        "/placement-test.html",
        "/js/placement-test.js",
        "/js/placement-api.js",
        "/css/placement-test.css",
    ]:
        assert (await client.get(path)).status_code == 200
    assert (await client.get("/app/db/content/placement-v1.json")).status_code == 404
