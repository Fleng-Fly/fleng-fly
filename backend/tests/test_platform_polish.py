"""Regression cases for persisted profile/vocabulary reliability."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VocabularyItem


async def test_normalized_word_length_cannot_poison_saved_collection(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": "words@example.com", "password": "correct-password", "displayName": "Words"},
    )
    headers = {"Authorization": "Bearer " + registered.json()["accessToken"]}
    # Unicode casefold expands each character; the stored form would exceed 120.
    response = await client.post(
        "/api/v1/vocabulary",
        headers=headers,
        json={"word": "ß" * 61, "translation": "example"},
    )
    assert response.status_code == 422
    assert await db_session.scalar(select(func.count()).select_from(VocabularyItem)) == 0
    valid = await client.post(
        "/api/v1/vocabulary",
        headers=headers,
        json={"word": "ß" * 60, "translation": "example"},
    )
    assert valid.status_code == 201
    assert valid.json()["word"] == "ss" * 60
    collection = await client.get("/api/v1/vocabulary", headers=headers)
    assert collection.status_code == 200
    assert len(collection.json()) == 1
    assert (
        await client.post(
            "/api/v1/vocabulary",
            headers=headers,
            json={"word": "SS" * 60, "translation": "duplicate"},
        )
    ).status_code == 409
