"""Draft curriculum validation, safe import and existing API integration."""

from copy import deepcopy

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.db.curriculum import (
    Curriculum,
    content_sha,
    import_curriculum,
    load_curriculum,
    stable_id,
)
from app.db.models import Course, CourseVocabularyItem, Exercise, Lesson, VocabularyItem
from app.db.seed import seed_catalog
from app.modules.ai.schemas import GenerateRequest
from tests.test_learning_extensions import headers


def test_complete_content_structure():
    content = load_curriculum()
    assert len(content.courses) == 5
    assert sum(len(c.lessons) for c in content.courses) == 50
    assert (
        sum(len(lesson.vocabulary) for course in content.courses for lesson in course.lessons)
        == 500
    )
    assert (
        sum(len(lesson.exercises) for course in content.courses for lesson in course.lessons) == 400
    )
    assert content.status == "draft"
    assert GenerateRequest(level="A0", topic="greetings", exercise_type="fill_blank").level == "A0"


@pytest.mark.parametrize(
    "problem",
    [
        "level",
        "slug",
        "theory",
        "exercises",
        "answer",
        "translation",
        "duplicate-word",
        "prerequisite",
        "reference",
        "blank-options",
        "duplicate-options",
    ],
)
def test_reject_bad_content(problem):
    data = deepcopy(load_curriculum().model_dump())
    course = data["courses"][0]
    lesson = course["lessons"][0]
    if problem == "level":
        course["level"] = "D1"
    elif problem == "slug":
        course["lessons"][1]["slug"] = lesson["slug"]
    elif problem == "theory":
        lesson["theory"] = " "
    elif problem == "exercises":
        lesson["exercises"] = []
    elif problem == "answer":
        lesson["exercises"][0]["correct_option_id"] = "missing"
    elif problem == "translation":
        lesson["vocabulary"][0]["translation"] = " "
    elif problem == "duplicate-word":
        lesson["vocabulary"][1] = lesson["vocabulary"][0]
    elif problem == "prerequisite":
        lesson["prerequisites"] = [course["lessons"][-1]["slug"]]
    elif problem == "reference":
        lesson["exercises"][0]["slug"] = "fleng-wrong-course-question"
    elif problem == "blank-options":
        lesson["exercises"][0]["options"][0]["text"] = " "
    else:
        lesson["exercises"][0]["options"][1] = lesson["exercises"][0]["options"][0]
    with pytest.raises(ValidationError):
        Curriculum.model_validate(data)


async def test_draft_import_review_and_progress_preservation(client, db_session):
    await seed_catalog(db_session)
    auth = await headers(client)
    # Existing user work must survive adding and rerunning the new content.
    old = (await client.get("/api/v1/lessons/the-verb-to-be")).json()
    exercise = old["exercises"][0]
    submitted = await client.post(
        "/api/v1/lessons/the-verb-to-be/submit",
        headers=auth,
        json={"exerciseId": exercise["id"], "answer": "b"},
    )
    assert submitted.status_code == 200
    before = (await client.get("/api/v1/progress/me", headers=auth)).json()
    old_ids = set((await db_session.scalars(select(Course.id))).all())
    content = load_curriculum()
    report = await import_curriculum(db_session, content)
    assert not report["applied"] and report["new_rows"] > 0
    assert await db_session.scalar(select(func.count()).select_from(Course)) == 2
    imported = await import_curriculum(db_session, content, apply=True)
    assert imported["words"] == 500
    assert len((await client.get("/api/v1/courses")).json()) == 2
    assert (await client.get("/api/v1/lessons/fleng-a0-classroom")).status_code == 404
    assert (
        await client.get("/api/v1/vocabulary/course-words", headers=auth, params={"level": "A0"})
    ).json() == []
    repeated = await import_curriculum(db_session, content, apply=True)
    assert repeated["new_rows"] == 0
    assert repeated["existing_rows"] == imported["new_rows"]
    with pytest.raises(ValueError, match="SHA"):
        await import_curriculum(db_session, content, apply=True, reviewed_sha="wrong")
    # This explicit publication is confined to the isolated test database.
    await import_curriculum(db_session, content, apply=True, reviewed_sha=content_sha(content))
    await import_curriculum(db_session, content, apply=True)
    assert old_ids.issubset(set((await db_session.scalars(select(Course.id))).all()))
    after = (await client.get("/api/v1/progress/me", headers=auth)).json()
    for field in ["xp", "lessonsStarted", "lessonsCompleted", "exercisesCompleted", "studyMinutes"]:
        assert after[field] == before[field]
    assert (await client.get("/api/v1/lessons/the-verb-to-be")).json() == old
    assert await db_session.scalar(select(func.count()).select_from(VocabularyItem)) == 0
    assert await db_session.scalar(select(func.count()).select_from(CourseVocabularyItem)) == 500
    assert await db_session.scalar(select(func.count()).select_from(Exercise)) == 421
    for level in ["A0", "A1", "A2", "B1", "B2"]:
        courses = (await client.get("/api/v1/courses", params={"level": level})).json()
        course = next(c for c in courses if c["slug"] == f"fleng-{level.lower()}")
        assert course["lessonCount"] == 10
        lesson = next(c for c in content.courses if c.level == level).lessons[0]
        detail = (await client.get("/api/v1/lessons/" + lesson.slug)).json()
        assert detail["level"] == level and len(detail["exercises"]) == 8
        for item in detail["exercises"]:
            assert (
                not {"correctOptionId", "acceptedAnswers", "explanation", "modelAnswer"}
                & item.keys()
            )
        words = (
            await client.get(
                "/api/v1/vocabulary/course-words",
                headers=auth,
                params={"level": level, "limit": 100},
            )
        ).json()
        assert len(words) == 100
        result = (
            await client.post(
                "/api/v1/vocabulary/flashcards/sessions",
                headers=auth,
                json={"source": "course_words", "courseId": course["id"], "level": level},
            )
        ).json()
        assert result["total"] == 10
        path = "/api/v1/vocabulary/flashcards/sessions/" + result["sessionId"]
        assert (await client.post(path + "/complete", headers=auth)).json()["testReady"]
        assert (await client.get(path + "/test-words", headers=auth)).json()["cards"] == result[
            "cards"
        ]
    assert (
        await client.patch("/api/v1/users/me", headers=auth, json={"englishLevel": "A0"})
    ).json()["englishLevel"] == "A0"
    assert (await client.get("/api/v1/courses?level=D1")).status_code == 422
    assert (await client.get("/api/v1/progress/me", headers=auth)).json()["xp"] == before["xp"]
    # Existing grading still awards XP once for new curriculum exercises.
    lesson = content.courses[0].lessons[0]
    question = lesson.exercises[0]
    for attempt in range(2):
        response = await client.post(
            f"/api/v1/lessons/{lesson.slug}/submit",
            headers=auth,
            json={
                "exerciseId": str(stable_id("exercise", question.slug)),
                "answer": question.correct_option_id,
            },
        )
        assert response.status_code == 200
        assert response.json()["xpAwarded"] == (1 if attempt == 0 else 0)


async def test_import_collision_and_drift_abort(db_session):
    content = load_curriculum()
    course = Course(slug="fleng-b2", title="Other author's course", description="Keep", level="B2")
    db_session.add(course)
    await db_session.commit()
    with pytest.raises(ValueError, match="owned by other"):
        await import_curriculum(db_session, content, apply=True)
    assert await db_session.scalar(select(func.count()).select_from(Course)) == 1
    assert await db_session.scalar(select(func.count()).select_from(Lesson)) == 0


async def test_existing_curriculum_is_not_overwritten(db_session):
    content = load_curriculum()
    await import_curriculum(db_session, content, apply=True)
    lesson = await db_session.get(Lesson, stable_id("lesson", content.courses[0].lessons[0].slug))
    lesson.theory = "Teacher's edited content"
    await db_session.commit()
    with pytest.raises(ValueError, match="refusing overwrite"):
        await import_curriculum(db_session, content, apply=True)
    assert lesson.theory == "Teacher's edited content"


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "B1", "B2"])
@pytest.mark.parametrize("count", [0, 3])
async def test_small_course_flashcard_sets(client, db_session, level, count):
    auth = await headers(client)
    course = Course(
        slug="small-set", title="Small set", description="Test", level=level, is_published=True
    )
    db_session.add(course)
    await db_session.flush()
    for i in range(count):
        db_session.add(
            CourseVocabularyItem(course_id=course.id, word=f"test{i}", translation=f"тест{i}")
        )
    await db_session.commit()
    response = await client.post(
        "/api/v1/vocabulary/flashcards/sessions",
        headers=auth,
        json={"source": "course_words", "level": level},
    )
    assert response.status_code == 201
    assert response.json()["total"] == count
    assert response.json()["status"] == ("active" if count else "empty")


async def test_seed_level_validation(db_session, monkeypatch):
    from app.db import seed

    data = deepcopy(seed.SEED_COURSES)
    data[0]["level"] = "D1"
    monkeypatch.setattr(seed, "SEED_COURSES", data)
    with pytest.raises(ValueError, match="learning level"):
        await seed_catalog(db_session)
    assert await db_session.scalar(select(func.count()).select_from(Course)) == 0
    data[0]["level"] = "A0"
    await seed_catalog(db_session)
    assert (
        await db_session.scalar(select(Course).where(Course.slug == data[0]["slug"]))
    ).level == "A0"


def test_all_existing_levels_remain_valid():
    from app.core.levels import LEARNING_LEVELS
    from app.modules.users.schemas import ProfileUpdate

    for level in LEARNING_LEVELS:
        assert ProfileUpdate(english_level=level).english_level == level
        assert GenerateRequest(level=level, topic="test", exercise_type="fill_blank").level == level


async def test_owner_publication_is_sha_bound_and_does_not_claim_editorial_review(
    client, db_session
):
    content = load_curriculum()
    await seed_catalog(db_session)
    await import_curriculum(db_session, content, apply=True)
    ids = set((await db_session.scalars(select(Course.id))).all())
    with pytest.raises(ValueError, match="SHA"):
        await import_curriculum(db_session, content, apply=True, owner_authorized_sha="wrong")
    with pytest.raises(ValueError, match="not both"):
        await import_curriculum(
            db_session,
            content,
            apply=True,
            reviewed_sha=content_sha(content),
            owner_authorized_sha=content_sha(content),
        )
    assert len((await client.get("/api/v1/courses")).json()) == 2
    report = await import_curriculum(
        db_session, content, apply=True, owner_authorized_sha=content_sha(content)
    )
    assert report["status"] == "owner_authorized" and report["new_rows"] == 0
    assert content.status == "draft"  # Source editorial status was not fabricated.
    assert set((await db_session.scalars(select(Course.id))).all()) == ids
    assert len((await client.get("/api/v1/courses")).json()) == 7
    repeated = await import_curriculum(
        db_session, content, apply=True, owner_authorized_sha=content_sha(content)
    )
    assert repeated["new_rows"] == 0


def test_startup_release_approval_matches_exact_packaged_content():
    from app.db.prepare import OWNER_AUTHORIZED_CURRICULUM_SHA

    assert content_sha(load_curriculum()) == OWNER_AUTHORIZED_CURRICULUM_SHA
