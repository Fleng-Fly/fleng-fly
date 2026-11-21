"""Reading study-time HTTP API: heartbeat, statistics, progress integration and limits."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.modules.reading import content, study
from tests.test_reading import make_article, make_category
from tests.test_reading_api import API, login

T0 = datetime(2026, 11, 22, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def clock(monkeypatch):
    state = {"now": T0}
    monkeypatch.setattr(study, "_now", lambda: state["now"])

    def move(seconds: float) -> None:
        state["now"] = state["now"] + timedelta(seconds=seconds)

    return move


async def beat(client, auth, slug="story"):
    return await client.post(
        f"{API}/articles/{slug}/heartbeat", headers=auth, json={"active": True}
    )


async def make(db, slug="story", **kw):
    return await make_article(db, await make_category(db, f"c-{slug}"), slug, **kw)


async def test_routes_require_a_session(client: AsyncClient):
    assert (
        await client.post(f"{API}/articles/x/heartbeat", json={"active": True})
    ).status_code == 401
    assert (await client.get(f"{API}/study-time")).status_code == 401


async def test_heartbeat_credits_server_measured_time(client: AsyncClient, db_session, clock):
    auth = await login(client)
    await make(db_session)
    first = await beat(client, auth)
    assert first.status_code == 200
    assert first.json() == {
        "creditedSeconds": 0,
        "articleSeconds": 0,
        "todaySeconds": 0,
        "totalSeconds": 0,
        "nextBeatInSeconds": 15,
        "capped": False,
    }
    clock(15)
    second = (await beat(client, auth)).json()
    assert (second["creditedSeconds"], second["articleSeconds"], second["totalSeconds"]) == (
        15,
        15,
        15,
    )
    clock(2)  # too soon
    assert (await beat(client, auth)).json()["creditedSeconds"] == 0


async def test_request_body_is_validated_and_client_cannot_claim_time(
    client: AsyncClient, db_session, clock
):
    auth = await login(client)
    await make(db_session)
    url = f"{API}/articles/story/heartbeat"
    for bad in ({"active": False}, {}, {"active": "yes"}, {"active": True, "seconds": 999}):
        response = await client.post(url, headers=auth, json=bad)
        if bad == {"active": True, "seconds": 999}:
            assert response.status_code == 200  # extra fields are ignored, never trusted
            assert response.json()["creditedSeconds"] == 0
        else:
            assert response.status_code == 422, bad
    assert (await client.post(url, headers=auth)).status_code == 422


async def test_unavailable_and_unknown_articles_are_404(client: AsyncClient, db_session, clock):
    auth = await login(client)
    await make(db_session, "draft", publish=False)
    archived = await make(db_session, "old")
    await content.set_status(db_session, archived, "archived")
    for slug in ("draft", "old", "missing"):
        assert (await beat(client, auth, slug)).status_code == 404


async def test_study_time_statistics_and_per_article_seconds(
    client: AsyncClient, db_session, clock
):
    auth = await login(client)
    await make(db_session, "one")
    await make(db_session, "two")
    await beat(client, auth, "one")
    for _ in range(2):
        clock(15)
        await beat(client, auth, "one")
    clock(15)
    await beat(client, auth, "two")

    stats = (await client.get(f"{API}/study-time?days=3", headers=auth)).json()
    assert (stats["totalSeconds"], stats["todaySeconds"]) == (45, 45)
    assert [d["seconds"] for d in stats["days"]] == [0, 0, 45]
    assert stats["days"][-1]["date"] == "2026-11-22"
    assert {(a["slug"], a["seconds"]) for a in stats["byArticle"]} == {("one", 30), ("two", 15)}

    detail = (await client.get(f"{API}/articles/one", headers=auth)).json()
    assert detail["progress"] is None  # no reading progress row yet; time lives elsewhere
    await client.put(f"{API}/articles/one/progress", headers=auth, json={"percent": 10})
    detail = (await client.get(f"{API}/articles/one", headers=auth)).json()
    assert detail["progress"]["activeSeconds"] == 30
    listing = (await client.get(f"{API}/articles", headers=auth)).json()["items"]
    assert {i["slug"]: (i["progress"] or {}).get("activeSeconds") for i in listing}["one"] == 30
    for bad in ("days=0", "days=366", "days=x"):
        assert (await client.get(f"{API}/study-time?{bad}", headers=auth)).status_code == 422


async def test_study_time_is_private_per_learner(client: AsyncClient, db_session, clock):
    a, b = await login(client, "a@example.com"), await login(client, "b@example.com")
    await make(db_session)
    await beat(client, a)
    clock(15)
    await beat(client, a)
    mine = (await client.get(f"{API}/study-time", headers=a)).json()
    theirs = (await client.get(f"{API}/study-time", headers=b)).json()
    assert mine["totalSeconds"] == 15
    assert theirs["totalSeconds"] == 0 and theirs["byArticle"] == []


async def test_heartbeats_are_rate_limited_per_learner(client: AsyncClient, db_session, clock):
    auth, other = await login(client), await login(client, "other@example.com")
    await make(db_session)
    codes = [(await beat(client, auth)).status_code for _ in range(22)]
    assert codes[:20] == [200] * 20 and codes[20] == 429
    limited = await beat(client, auth)
    assert limited.json()["error"]["code"] == "RATE_LIMITED" and "retry-after" in limited.headers
    assert (await beat(client, other)).status_code == 200


async def test_reading_time_gives_no_xp_and_leaves_study_minutes_alone(
    client: AsyncClient, db_session, clock
):
    auth = await login(client)
    await make(db_session)
    await beat(client, auth)
    for _ in range(6):
        clock(15)
        await beat(client, auth)
    progress = (await client.get("/api/v1/progress/me", headers=auth)).json()
    assert progress["xp"] == 0 and progress["studyMinutes"] == 0
    streak = (await client.get("/api/v1/streaks/me", headers=auth)).json()
    assert streak["current"] >= 1  # 60+ seconds of reading counts as a learning day
