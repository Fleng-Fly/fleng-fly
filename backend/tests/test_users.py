"""Users endpoint tests: `/users/me` is authenticated and strictly read-only."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

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


async def test_users_me_never_creates_users(client: AsyncClient, db_session: AsyncSession) -> None:
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


async def test_settings_updates_profile_email_and_language(client: AsyncClient) -> None:
    registration = await client.post(
        REGISTER,
        json={
            "email": "settings@example.com",
            "password": "correct-horse-battery",
            "displayName": "First",
        },
    )
    headers = {"Authorization": f"Bearer {registration.json()['accessToken']}"}
    changed = await client.patch(
        ME,
        headers=headers,
        json={
            "displayName": "Second",
            "email": "NEW@example.com",
            "preferredLanguage": "Ukrainian",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["email"] == "new@example.com"
    assert changed.json()["displayName"] == "Second"
    assert changed.json()["preferredLanguage"] == "Ukrainian"
    assert (await client.get(ME, headers=headers)).json()["preferredLanguage"] == "Ukrainian"
    login = await client.post(
        "/api/v1/auth/login", json={"email": "new@example.com", "password": "correct-horse-battery"}
    )
    assert login.status_code == 200
    assert login.json()["user"]["displayName"] == "Second"


async def test_settings_rejects_invalid_and_duplicate_email(client: AsyncClient) -> None:
    first = await client.post(
        REGISTER,
        json={
            "email": "first@example.com",
            "password": "correct-horse-battery",
            "displayName": "First",
        },
    )
    await client.post(
        REGISTER,
        json={
            "email": "second@example.com",
            "password": "correct-horse-battery",
            "displayName": "Second",
        },
    )
    headers = {"Authorization": f"Bearer {first.json()['accessToken']}"}
    invalid = await client.patch(ME, headers=headers, json={"email": "not-an-email"})
    assert invalid.status_code == 422
    duplicate = await client.patch(ME, headers=headers, json={"email": "SECOND@example.com"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_TAKEN"
    assert (await client.get(ME, headers=headers)).json()["email"] == "first@example.com"


async def test_settings_password_change(client: AsyncClient) -> None:
    registration = await client.post(
        REGISTER,
        json={
            "email": "password@example.com",
            "password": "correct-horse-battery",
            "displayName": "Learner",
        },
    )
    headers = {"Authorization": f"Bearer {registration.json()['accessToken']}"}
    endpoint = f"{ME}/password"
    assert (
        await client.post(
            endpoint, json={"currentPassword": "x", "newPassword": "new-password-123"}
        )
    ).status_code == 401
    wrong = await client.post(
        endpoint,
        headers=headers,
        json={"currentPassword": "wrong", "newPassword": "new-password-123"},
    )
    assert wrong.status_code == 400
    weak = await client.post(
        endpoint,
        headers=headers,
        json={"currentPassword": "correct-horse-battery", "newPassword": "short"},
    )
    assert weak.status_code == 422
    changed = await client.post(
        endpoint,
        headers=headers,
        json={"currentPassword": "correct-horse-battery", "newPassword": "new-password-123"},
    )
    assert changed.status_code == 204
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "correct-horse-battery"},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "new-password-123"},
        )
    ).status_code == 200
