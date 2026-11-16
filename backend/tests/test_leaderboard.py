"""Ranking, privacy and own position use persisted learning data."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import LearningActivity, Profile, Progress


async def test_leaderboard_requires_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/leaderboard")).status_code == 401


async def test_ranking_and_own_position(client: AsyncClient, db_session: AsyncSession) -> None:
    tokens = []
    ids = []
    for i in range(4):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"rank{i}@example.com",
                "displayName": f"Learner {i}",
                "password": "correct-horse-battery",
            },
        )
        assert response.status_code == 201
        tokens.append(response.json()["accessToken"])
        ids.append(UUID(response.json()["user"]["id"]))
    profiles = list((await db_session.scalars(select(Profile).order_by(Profile.user_id))).all())
    for profile in profiles:
        profile.xp = 50
    # Own account stays below three equal-XP learners.
    own = next(profile for profile in profiles if profile.user_id == ids[0])
    own.xp = 10
    progress = await db_session.scalar(select(Progress).where(Progress.user_id == own.user_id))
    assert progress is not None
    progress.lessons_completed = 2
    today = datetime.now(ZoneInfo(get_settings().learning_timezone)).date()
    for delta in (0, 1, 2, 5):
        db_session.add(LearningActivity(user_id=own.user_id, day=today - timedelta(days=delta)))
    await db_session.commit()
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    response = await client.get("/api/v1/leaderboard?limit=2", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert [entry["rank"] for entry in body["entries"]] == [1, 2]
    expected = [p.display_name for p in profiles if p.user_id != own.user_id][:2]
    assert [entry["displayName"] for entry in body["entries"]] == expected
    assert body["currentUser"] == {
        "rank": 4,
        "displayName": own.display_name,
        "xp": 10,
        "lessonsCompleted": 2,
        "streak": 3,
        "isCurrentUser": True,
    }
    assert set(body["entries"][0]) == {
        "rank",
        "displayName",
        "xp",
        "lessonsCompleted",
        "streak",
        "isCurrentUser",
    }
    full = (await client.get("/api/v1/leaderboard", headers=headers)).json()
    assert len(full["entries"]) == 4
    assert full["entries"][-1] == body["currentUser"]
    assert (await client.get("/api/v1/leaderboard?limit=101", headers=headers)).status_code == 422


async def test_short_leaderboard(client: AsyncClient) -> None:
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "solo@example.com",
            "displayName": "<script>learner</script>",
            "password": "correct-horse-battery",
        },
    )
    headers = {"Authorization": f"Bearer {registration.json()['accessToken']}"}
    body = (await client.get("/api/v1/leaderboard", headers=headers)).json()
    assert body["total"] == 1
    assert body["entries"] == [body["currentUser"]]
    assert body["entries"][0]["xp"] == body["entries"][0]["streak"] == 0


async def test_empty_leaderboard(db_session: AsyncSession) -> None:
    from app.modules.gamification.service import leaderboard

    result = await leaderboard(db_session, uuid4(), 100)
    assert result.entries == []
    assert result.current_user is None
    assert result.total == 0
