"""Reading HTTP API (read side): catalog, articles, progress, bookmarks and preferences."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reading import content
from tests.test_reading import make_article, make_category

API = "/api/v1/reading"


async def login(client: AsyncClient, email: str = "reader@example.com") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery", "displayName": "Reader"},
    )
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json()["accessToken"]}


async def test_every_route_requires_a_session(client: AsyncClient):
    slug = "x"
    calls = [
        ("GET", "/categories"),
        ("GET", "/articles"),
        ("GET", f"/articles/{slug}"),
        ("PUT", f"/articles/{slug}/progress"),
        ("PUT", f"/articles/{slug}/bookmark"),
        ("DELETE", f"/articles/{slug}/bookmark"),
        ("GET", "/bookmarks"),
        ("GET", "/preferences"),
        ("PUT", "/preferences"),
    ]
    for method, path in calls:
        response = await client.request(method, API + path)
        assert response.status_code == 401, (method, path)


async def test_categories_count_only_published_articles(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    travel = await make_category(db_session, "travel")
    await make_category(db_session, "hidden", is_active=False)
    await make_article(db_session, travel, "one")
    await make_article(db_session, travel, "two", publish=False)
    body = (await client.get(f"{API}/categories", headers=auth)).json()
    assert [(c["slug"], c["articleCount"]) for c in body] == [("travel", 1)]
    assert set(body[0]) == {"id", "slug", "title", "description", "articleCount"}


async def test_list_is_paginated_filtered_and_hides_unavailable(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    travel, food = (
        await make_category(db_session, "travel"),
        await make_category(db_session, "food"),
    )
    for slug, cat, level in [("a", travel, "A0"), ("b", travel, "B1"), ("c", food, "A0")]:
        await make_article(db_session, cat, slug, level=level)
    await make_article(db_session, food, "draft", publish=False)

    body = (await client.get(f"{API}/articles", headers=auth)).json()
    assert body["total"] == 3 and body["limit"] == 20 and body["offset"] == 0
    assert "content" not in body["items"][0]
    assert {i["slug"] for i in body["items"]} == {"a", "b", "c"}

    page = (await client.get(f"{API}/articles?limit=2&offset=2", headers=auth)).json()
    assert page["total"] == 3 and len(page["items"]) == 1
    by_level = (await client.get(f"{API}/articles?level=A0", headers=auth)).json()
    assert by_level["total"] == 2
    cat = (await client.get(f"{API}/articles?categoryId={travel.id}", headers=auth)).json()
    assert {i["slug"] for i in cat["items"]} == {"a", "b"}
    for bad in ("level=C1", "limit=0", "limit=101", "offset=-1", "progress=weird", "categoryId=x"):
        assert (await client.get(f"{API}/articles?{bad}", headers=auth)).status_code == 422, bad


async def test_article_detail_has_content_but_no_answer_key(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    await make_article(db_session, await make_category(db_session), "story")
    response = await client.get(f"{API}/articles/story", headers=auth)
    body = response.json()
    assert response.status_code == 200
    assert body["content"].startswith("We went") and body["questionCount"] == 2
    assert body["pointsPossible"] == 5 and body["progress"] is None and body["bookmarked"] is False
    assert body["category"]["slug"] == "travel" and body["level"] == "A1"
    text = response.text
    assert "isCorrect" not in text and "explanation" not in text and "Because" not in text


async def test_unavailable_articles_are_404_everywhere(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    cat = await make_category(db_session)
    await make_article(db_session, cat, "draft", publish=False)
    archived = await make_article(db_session, cat, "old")
    await content.set_status(db_session, archived, "archived")
    for slug in ("draft", "old", "missing"):
        for method, path in [
            ("GET", f"/articles/{slug}"),
            ("PUT", f"/articles/{slug}/bookmark"),
        ]:
            assert (await client.request(method, API + path, headers=auth)).status_code == 404
        response = await client.put(
            f"{API}/articles/{slug}/progress", headers=auth, json={"percent": 10}
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_progress_is_saved_monotonic_and_shown_in_list_and_filters(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    cat = await make_category(db_session)
    await make_article(db_session, cat, "read")
    await make_article(db_session, cat, "fresh")
    url = f"{API}/articles/read/progress"
    first = await client.put(url, headers=auth, json={"percent": 40})
    assert first.status_code == 200
    assert first.json() == {
        "status": "in_progress",
        "readPercent": 40,
        "bestScorePercent": None,
        "attemptsCount": 0,
        "xpAwarded": 0,
    }
    assert (await client.put(url, headers=auth, json={"percent": 10})).json()["readPercent"] == 40

    items = {
        i["slug"]: i for i in (await client.get(f"{API}/articles", headers=auth)).json()["items"]
    }
    assert items["read"]["progress"]["readPercent"] == 40 and items["fresh"]["progress"] is None
    for state, expected in (("new", {"fresh"}), ("in_progress", {"read"}), ("completed", set())):
        body = (await client.get(f"{API}/articles?progress={state}", headers=auth)).json()
        assert {i["slug"] for i in body["items"]} == expected and body["total"] == len(expected)


async def test_progress_input_validation(client: AsyncClient, db_session: AsyncSession):
    auth = await login(client)
    await make_article(db_session, await make_category(db_session), "read")
    url = f"{API}/articles/read/progress"
    for bad in ({"percent": -1}, {"percent": 101}, {"percent": "50"}, {"percent": 1.5}, {}):
        assert (await client.put(url, headers=auth, json=bad)).status_code == 422, bad
    assert (await client.put(url, headers=auth, json={"percent": 0})).status_code == 200
    assert (await client.put(url, headers=auth, json={"percent": 100})).status_code == 200


async def test_progress_writes_are_rate_limited_per_user(
    client: AsyncClient, db_session: AsyncSession
):
    auth, other = await login(client), await login(client, "other@example.com")
    await make_article(db_session, await make_category(db_session), "read")
    url = f"{API}/articles/read/progress"
    codes = [
        (await client.put(url, headers=auth, json={"percent": i % 100})).status_code
        for i in range(62)
    ]
    assert codes.count(200) >= 60 and codes[-1] == 429
    limited = await client.put(url, headers=auth, json={"percent": 5})
    assert limited.status_code == 429 and limited.json()["error"]["code"] == "RATE_LIMITED"
    assert "retry-after" in limited.headers
    # another learner is unaffected
    assert (await client.put(url, headers=other, json={"percent": 5})).status_code == 200


async def test_progress_is_private_to_each_learner(client: AsyncClient, db_session: AsyncSession):
    a, b = await login(client, "a@example.com"), await login(client, "b@example.com")
    await make_article(db_session, await make_category(db_session), "read")
    await client.put(f"{API}/articles/read/progress", headers=a, json={"percent": 60})
    detail = (await client.get(f"{API}/articles/read", headers=b)).json()
    assert detail["progress"] is None


async def test_bookmarks_flow(client: AsyncClient, db_session: AsyncSession):
    auth, other = await login(client), await login(client, "other@example.com")
    cat = await make_category(db_session)
    await make_article(db_session, cat, "one")
    await make_article(db_session, cat, "two")
    for _ in range(2):  # idempotent
        response = await client.put(f"{API}/articles/one/bookmark", headers=auth)
        assert response.status_code == 200 and response.json()["bookmarked"] is True
    assert [b["slug"] for b in (await client.get(f"{API}/bookmarks", headers=auth)).json()] == [
        "one"
    ]
    assert (await client.get(f"{API}/bookmarks", headers=other)).json() == []
    assert (await client.get(f"{API}/articles/one", headers=auth)).json()["bookmarked"] is True
    only = (await client.get(f"{API}/articles?bookmarked=true", headers=auth)).json()
    rest = (await client.get(f"{API}/articles?bookmarked=false", headers=auth)).json()
    assert [i["slug"] for i in only["items"]] == ["one"] and rest["total"] == 1

    for _ in range(2):
        assert (
            await client.delete(f"{API}/articles/one/bookmark", headers=auth)
        ).status_code == 204
    assert (await client.get(f"{API}/bookmarks", headers=auth)).json() == []
    assert (await client.delete(f"{API}/articles/nope/bookmark", headers=auth)).status_code == 204


async def test_stale_bookmark_is_hidden_but_removable(
    client: AsyncClient, db_session: AsyncSession
):
    auth = await login(client)
    article = await make_article(db_session, await make_category(db_session), "one")
    await client.put(f"{API}/articles/one/bookmark", headers=auth)
    await content.set_status(db_session, article, "archived")
    assert (await client.get(f"{API}/bookmarks", headers=auth)).json() == []
    assert (await client.delete(f"{API}/articles/one/bookmark", headers=auth)).status_code == 204


async def test_preferences_replace_validate_and_isolate(
    client: AsyncClient, db_session: AsyncSession
):
    auth, other = await login(client), await login(client, "other@example.com")
    travel, food = (
        await make_category(db_session, "travel"),
        await make_category(db_session, "food"),
    )
    off = await make_category(db_session, "off", is_active=False)
    assert (await client.get(f"{API}/preferences", headers=auth)).json() == {"categories": []}

    put = await client.put(
        f"{API}/preferences", headers=auth, json={"categoryIds": [str(travel.id), str(food.id)]}
    )
    assert put.status_code == 200
    assert {c["slug"] for c in put.json()["categories"]} == {"travel", "food"}
    put = await client.put(f"{API}/preferences", headers=auth, json={"categoryIds": [str(food.id)]})
    assert [c["slug"] for c in put.json()["categories"]] == ["food"]
    assert (await client.get(f"{API}/preferences", headers=other)).json() == {"categories": []}

    for bad in ([str(uuid.uuid4())], [str(off.id)], ["not-a-uuid"]):
        response = await client.put(f"{API}/preferences", headers=auth, json={"categoryIds": bad})
        assert response.status_code == 422, bad
    assert [
        c["slug"]
        for c in (await client.get(f"{API}/preferences", headers=auth)).json()["categories"]
    ] == ["food"]
    assert (
        await client.put(f"{API}/preferences", headers=auth, json={"categoryIds": []})
    ).json() == {"categories": []}


# --- attempts -------------------------------------------------------------------------------


async def start(client, auth, slug="story"):
    return await client.post(f"{API}/articles/{slug}/attempts", headers=auth)


def choose(attempt: dict, *, right: bool, questions: list | None = None) -> dict[str, str]:
    """Pick answers using the learner-visible question list plus a known answer layout.

    Tests create answers as `opt 0..2` with `opt 0` correct, so the key is derivable by text.
    """
    wanted = "opt 0" if right else "opt 1"
    return {
        q["id"]: next(a["id"] for a in q["answers"] if a["text"] == wanted)
        for q in attempt["questions"]
    }


async def story(db_session, slug="story", **kw):
    return await make_article(db_session, await make_category(db_session, f"c-{slug}"), slug, **kw)


async def test_attempt_routes_require_a_session(client: AsyncClient):
    some = uuid.uuid4()
    for method, path in [
        ("POST", "/articles/x/attempts"),
        ("GET", "/articles/x/attempts"),
        ("GET", f"/attempts/{some}"),
        ("PATCH", f"/attempts/{some}/answers"),
        ("POST", f"/attempts/{some}/submit"),
    ]:
        assert (await client.request(method, API + path)).status_code == 401, path


async def test_start_hides_the_answer_key_and_resumes(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    first = await start(client, auth)
    assert first.status_code == 201
    body = first.json()
    assert body["status"] == "in_progress" and body["attemptNumber"] == 1
    assert body["articleSlug"] == "story" and body["result"] is None and body["answers"] == {}
    assert len(body["questions"]) == 2 and len(body["questions"][0]["answers"]) == 3
    for forbidden in ("isCorrect", "correctAnswerId", "explanation", "Because"):
        assert forbidden not in first.text

    again = await start(client, auth)
    assert again.status_code == 200 and again.json()["id"] == body["id"]
    assert (await client.get(f"{API}/attempts/{body['id']}", headers=auth)).json()["id"] == body[
        "id"
    ]


async def test_start_requires_a_quiz_and_a_visible_article(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session, "plain", questions=[])
    await story(db_session, "draft", publish=False)
    no_quiz = await start(client, auth, "plain")
    assert (no_quiz.status_code, no_quiz.json()["error"]["code"]) == (409, "NO_QUESTIONS")
    assert (await start(client, auth, "draft")).status_code == 404
    assert (await start(client, auth, "missing")).status_code == 404


async def test_save_and_restore_answers(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    attempt = (await start(client, auth)).json()
    picked = choose(attempt, right=False)
    first_q = next(iter(picked))
    saved = await client.patch(
        f"{API}/attempts/{attempt['id']}/answers",
        headers=auth,
        json={"answers": {first_q: picked[first_q]}},
    )
    assert saved.status_code == 200 and saved.json()["answers"] == {first_q: picked[first_q]}
    restored = (await start(client, auth)).json()  # resume
    assert restored["answers"] == {first_q: picked[first_q]}
    assert len(restored["questions"]) == 2


async def test_save_validation(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    attempt = (await start(client, auth)).json()
    q1, q2 = attempt["questions"]
    url = f"{API}/attempts/{attempt['id']}/answers"
    bad_bodies = [
        {"answers": {str(uuid.uuid4()): q1["answers"][0]["id"]}},
        {"answers": {q1["id"]: str(uuid.uuid4())}},
        {"answers": {q1["id"]: q2["answers"][0]["id"]}},
        {"answers": {"nope": "nope"}},
        {"answers": "x"},
        {},
    ]
    for bad in bad_bodies:
        assert (await client.patch(url, headers=auth, json=bad)).status_code == 422, bad
    error = await client.patch(url, headers=auth, json=bad_bodies[1])
    assert error.json()["error"]["code"] == "INVALID_ANSWER"


async def test_submit_grades_reveals_review_and_pays_xp_once(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    attempt = (await start(client, auth)).json()
    answers = choose(attempt, right=True)

    done = await client.post(
        f"{API}/attempts/{attempt['id']}/submit", headers=auth, json={"answers": answers}
    )
    body = done.json()
    assert done.status_code == 200 and body["status"] == "submitted"
    assert body["questions"] is None and body["alreadySubmitted"] is False
    result = body["result"]
    assert (result["scorePercent"], result["passed"], result["passMark"]) == (100, True, 70)
    assert (result["pointsEarned"], result["pointsPossible"], result["xpAwarded"]) == (5, 5, 5)
    review = result["questions"][0]
    assert review["isCorrect"] is True and review["explanation"].startswith("Because")
    assert review["prompt"] and len(review["answers"]) == 3

    me = (await client.get("/api/v1/progress/me", headers=auth)).json()
    assert me["xp"] == 5

    again = await client.post(f"{API}/attempts/{attempt['id']}/submit", headers=auth)
    assert again.status_code == 200
    assert again.json()["alreadySubmitted"] is True
    assert again.json()["result"] == result
    assert (await client.get("/api/v1/progress/me", headers=auth)).json()["xp"] == 5

    progress = (await client.get(f"{API}/articles/story", headers=auth)).json()["progress"]
    assert progress["status"] == "completed" and progress["xpAwarded"] == 5
    assert progress["bestScorePercent"] == 100 and progress["attemptsCount"] == 1


async def test_submit_without_body_grades_saved_answers(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    attempt = (await start(client, auth)).json()
    await client.patch(
        f"{API}/attempts/{attempt['id']}/answers",
        headers=auth,
        json={"answers": choose(attempt, right=True)},
    )
    done = await client.post(f"{API}/attempts/{attempt['id']}/submit", headers=auth)
    assert done.json()["result"]["passed"] is True


async def test_failed_then_retry_pays_once_and_lists_history(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    failed = (await start(client, auth)).json()
    result = (
        await client.post(
            f"{API}/attempts/{failed['id']}/submit",
            headers=auth,
            json={"answers": choose(failed, right=False)},
        )
    ).json()["result"]
    assert (result["passed"], result["xpAwarded"], result["scorePercent"]) == (False, 0, 0)
    assert (await client.get("/api/v1/progress/me", headers=auth)).json()["xp"] == 0

    retry = await start(client, auth)
    assert retry.status_code == 201 and retry.json()["attemptNumber"] == 2
    await client.post(
        f"{API}/attempts/{retry.json()['id']}/submit",
        headers=auth,
        json={"answers": choose(retry.json(), right=True)},
    )
    third = (await start(client, auth)).json()
    await client.post(
        f"{API}/attempts/{third['id']}/submit",
        headers=auth,
        json={"answers": choose(third, right=True)},
    )
    assert (await client.get("/api/v1/progress/me", headers=auth)).json()["xp"] == 5

    history = (await client.get(f"{API}/articles/story/attempts", headers=auth)).json()
    assert [h["attemptNumber"] for h in history] == [3, 2, 1]
    assert [h["xpAwarded"] for h in history] == [0, 5, 0]
    assert history[0]["passed"] is True and history[2]["passed"] is False


async def test_cannot_change_a_submitted_attempt(client: AsyncClient, db_session):
    auth = await login(client)
    await story(db_session)
    attempt = (await start(client, auth)).json()
    await client.post(f"{API}/attempts/{attempt['id']}/submit", headers=auth)
    response = await client.patch(
        f"{API}/attempts/{attempt['id']}/answers",
        headers=auth,
        json={"answers": choose(attempt, right=True)},
    )
    assert (response.status_code, response.json()["error"]["code"]) == (409, "ATTEMPT_SUBMITTED")
    reread = (await client.get(f"{API}/attempts/{attempt['id']}", headers=auth)).json()
    assert reread["questions"] is None and reread["result"]["scorePercent"] == 0


async def test_attempts_are_isolated_between_learners(client: AsyncClient, db_session):
    a, b = await login(client, "a@example.com"), await login(client, "b@example.com")
    await story(db_session)
    attempt = (await start(client, a)).json()
    for method, path, body in [
        ("GET", f"/attempts/{attempt['id']}", None),
        ("PATCH", f"/attempts/{attempt['id']}/answers", {"answers": {}}),
        ("POST", f"/attempts/{attempt['id']}/submit", {}),
    ]:
        response = await client.request(method, API + path, headers=b, json=body)
        assert response.status_code == 404, path
    assert (await client.get(f"{API}/attempts/{uuid.uuid4()}", headers=a)).status_code == 404
    assert (await client.get(f"{API}/attempts/not-a-uuid", headers=a)).status_code == 422
    mine = (await client.get(f"{API}/articles/story/attempts", headers=b)).json()
    assert mine == []
    own = await start(client, b)
    assert own.status_code == 201 and own.json()["id"] != attempt["id"]
    assert (await client.get("/api/v1/progress/me", headers=b)).json()["xp"] == 0


async def test_attempt_starts_are_rate_limited(client: AsyncClient, db_session):
    auth = await login(client)
    for i in range(31):
        await story(db_session, f"s{i}")
    codes = []
    for i in range(31):
        codes.append((await start(client, auth, f"s{i}")).status_code)
    assert codes[:30] == [201] * 30 and codes[30] == 429


async def test_submit_for_hidden_article_is_not_found(client: AsyncClient, db_session):
    auth = await login(client)
    article = await story(db_session)
    attempt = (await start(client, auth)).json()
    await content.set_status(db_session, article, "archived")
    response = await client.post(f"{API}/attempts/{attempt['id']}/submit", headers=auth)
    assert response.status_code == 404
