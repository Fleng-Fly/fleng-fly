"""Users endpoint tests: `/users/me` is authenticated and strictly read-only."""

from app.db.models import User
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ME = "/api/v1/users/me"
REGISTER = "/api/v1/auth/register"


async def test_users_me_returns_camel_case_profile(client: AsyncClient) -> None:
    registration = await client.post(
        REGISTER,
        json={"email": "me@example.com", "password": "correct-horse-battery", "displayName": "Me"},
    )
    token = registration.json()["accessToken"]

    response = await client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["displayName"] == "Me"
    assert body["level"] == 1
    assert body["xp"] == 0
    assert "createdAt" in body
    assert "passwordHash" not in body


async def test_users_me_never_creates_users(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    registration = await client.post(
        REGISTER,
        json={
            "email": "count@example.com",
            "password": "correct-horse-battery",
            "displayName": "C",
        },
    )
    token = registration.json()["accessToken"]

    for _ in range(3):
        response = await client.get(ME, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    count = await db_session.scalar(select(func.count()).select_from(User))
    assert count == 1
