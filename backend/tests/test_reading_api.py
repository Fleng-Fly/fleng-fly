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
