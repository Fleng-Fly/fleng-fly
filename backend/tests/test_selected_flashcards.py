from uuid import uuid4

import pytest

from app.db.models import Course, CourseVocabularyItem
from tests.test_learning_extensions import headers

BASE = "/api/v1/vocabulary/flashcards/sessions"


async def test_selected_personal_words_preserve_order_and_refuse_other_owners(client):
    auth = await headers(client)
    other = await headers(client, "other-selection@example.com")
    own = []
    for word in ("alpha", "beta", "gamma"):
        response = await client.post(
            "/api/v1/vocabulary", headers=auth, json={"word": word, "translation": word}
        )
        own.append(response.json()["id"])
    private = (
        await client.post(
            "/api/v1/vocabulary", headers=other, json={"word": "private", "translation": "private"}
        )
    ).json()["id"]
    selected = await client.post(
        BASE,
        headers=auth,
        json={"source": "my_words", "wordIds": [own[2], own[0]], "limit": 2},
    )
    assert selected.status_code == 201
    assert [card["wordId"] for card in selected.json()["cards"]] == [own[2], own[0]]
    for ids in ([own[0], private], [str(uuid4())], [own[0], own[0]]):
        denied = await client.post(
            BASE, headers=auth, json={"source": "my_words", "wordIds": ids}
        )
        assert denied.status_code == 400
        assert denied.json()["error"]["code"] == "INVALID_WORD_SELECTION"


async def test_course_selection_enforces_publication_and_filters(client, db_session):
    auth = await headers(client)
    words = []
    courses = []
    for level, published in [("A1", True), ("B2", True), ("A2", False)]:
        course = Course(
            slug=level, title=level, description="", level=level, is_published=published
        )
        db_session.add(course)
        await db_session.flush()
        word = CourseVocabularyItem(
            course_id=course.id, word=level, translation=level, example=""
        )
        db_session.add(word)
        await db_session.flush()
        words.append(str(word.id))
        courses.append(str(course.id))
    await db_session.commit()
    created = await client.post(
        BASE, headers=auth, json={"source": "course_words", "wordIds": words[:2], "limit": 1}
    )
    assert created.status_code == 201
    assert created.json()["cards"][0]["wordId"] == words[0]
    assert created.json()["total"] == 1
    for payload in (
        {"wordIds": [words[2]]},
        {"courseId": courses[0], "wordIds": [words[1]]},
        {"level": "A1", "wordIds": [words[1]]},
    ):
        denied = await client.post(BASE, headers=auth, json={"source": "course_words", **payload})
        assert denied.status_code == 400


@pytest.mark.parametrize("extra", [{"limit": 0}, {"limit": 51}, {"wordIds": []}])
async def test_selection_bounds(client, extra):
    auth = await headers(client)
    assert (
        await client.post(BASE, headers=auth, json={"source": "my_words", **extra})
    ).status_code == 422
