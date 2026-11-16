from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.models import Course, CourseVocabularyItem, Profile
from tests.test_learning_extensions import headers

BASE = "/api/v1/vocabulary/flashcards/sessions"


@pytest.mark.parametrize("count", [0, 3, 12])
async def test_personal_sets_and_handoff(client, db_session, count):
    auth = await headers(client)
    other = await headers(client, "other@example.com")
    for i in range(count):
        assert (
            await client.post(
                "/api/v1/vocabulary",
                headers=auth,
                json={"word": f"word{i}", "translation": f"translation{i}"},
            )
        ).status_code == 201
    await client.post(
        "/api/v1/vocabulary", headers=other, json={"word": "private", "translation": "secret"}
    )
    assert len((await client.get("/api/v1/vocabulary", headers=auth)).json()) == count
    created = await client.post(BASE, headers=auth, json={"source": "my_words"})
    assert created.status_code == 201
    result = created.json()
    assert result["total"] == min(count, 10)
    assert result["status"] == ("active" if count else "empty")
    assert all(c["word"] != "private" for c in result["cards"])
    path = BASE + "/" + result["sessionId"]
    for suffix, method in [("", "get"), ("/complete", "post"), ("/test-words", "get")]:
        assert (await getattr(client, method)(path + suffix, headers=other)).status_code == 404
        assert (await getattr(client, method)(path + suffix)).status_code == 401
    assert (await client.get(path + "/test-words", headers=auth)).status_code == 409
    # New sessions are independent; reading an existing one preserves order and IDs.
    again = (await client.post(BASE, headers=auth, json={"source": "my_words"})).json()
    assert again["sessionId"] != result["sessionId"]
    assert again["cards"] == result["cards"]
    if count:
        await client.delete("/api/v1/vocabulary/" + result["cards"][0]["wordId"], headers=auth)
    assert (await client.get(path, headers=auth)).json() == result
    for _ in range(2):
        done = await client.post(path + "/complete", headers=auth)
        assert done.status_code == (200 if count else 400)
        if count:
            assert done.json()["testReady"] is True
            assert done.json()["status"] == "completed"
    if count:
        assert (await client.get(path + "/test-words", headers=auth)).json()["cards"] == result[
            "cards"
        ]
    assert all(xp == 0 for xp in (await db_session.scalars(select(Profile.xp))).all())


async def test_course_words_filters_and_sessions(client, db_session):
    auth = await headers(client)
    courses = []
    for level, published in [("A1", True), ("B2", True), ("A2", False)]:
        course = Course(
            slug=level, title=level, description="", level=level, is_published=published
        )
        db_session.add(course)
        await db_session.flush()
        courses.append(course)
        db_session.add(
            CourseVocabularyItem(course_id=course.id, word="example", translation=level, example="")
        )
    await db_session.commit()
    route = "/api/v1/vocabulary/course-words"
    assert (await client.get(route)).status_code == 401
    assert len((await client.get(route, headers=auth)).json()) == 2
    for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]:
        rows = (await client.get(route, headers=auth, params={"level": level})).json()
        assert len(rows) == (1 if level in ["A1", "B2"] else 0)
    for course in courses[:2]:
        rows = (await client.get(route, headers=auth, params={"courseId": str(course.id)})).json()
        result = (
            await client.post(
                BASE,
                headers=auth,
                json={"source": "course_words", "courseId": str(course.id), "level": course.level},
            )
        ).json()
        assert result["cards"][0]["wordId"] == rows[0]["id"]
        assert result["cards"][0]["translation"] == course.level
    for course_id in [uuid4(), courses[2].id]:
        assert (
            await client.get(route, headers=auth, params={"courseId": str(course_id)})
        ).status_code == 404
        assert (
            await client.post(
                BASE, headers=auth, json={"source": "course_words", "courseId": str(course_id)}
            )
        ).status_code == 404
    for payload, code in [
        ({"source": "my_words", "level": "A1"}, 400),
        ({"source": "course_words"}, 400),
        ({"source": "course_words", "level": "D1"}, 422),
        ({"source": "course_words", "courseId": "bad"}, 422),
        ({"source": "my_words", "cards": []}, 422),
        ({"source": "my_words", "userId": str(uuid4())}, 422),
    ]:
        assert (await client.post(BASE, headers=auth, json=payload)).status_code == code
    assert (await client.get(route, headers=auth, params={"level": "D1"})).status_code == 422
    assert (await client.get(BASE + "/" + str(uuid4()), headers=auth)).status_code == 404


@pytest.mark.parametrize("count", [0, 3, 12])
async def test_course_set_size(client, db_session, count):
    auth = await headers(client)
    course = Course(slug="test-course", title="Test", description="", level="A1", is_published=True)
    db_session.add(course)
    await db_session.flush()
    for i in range(count):
        db_session.add(
            CourseVocabularyItem(course_id=course.id, word=f"word{i}", translation="test")
        )
    await db_session.commit()
    result = await client.post(
        BASE, headers=auth, json={"source": "course_words", "courseId": str(course.id)}
    )
    assert result.status_code == 201
    assert result.json()["total"] == min(count, 10)
    assert len({card["wordId"] for card in result.json()["cards"]}) == min(count, 10)
