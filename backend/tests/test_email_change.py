"""Email changes preserve identity until a password-authorized mailbox confirmation."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models import EmailChange, RefreshToken
from app.main import app
from app.modules.users import email_change


@pytest.mark.parametrize(
    "mode", ["success", "expired", "password_changed", "superseded", "delivery_failed", "taken"]
)
async def test_email_change(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, mode: str
) -> None:
    sent = []

    async def deliver(email, raw, settings):
        sent.append((email, raw))
        if mode == "delivery_failed":
            raise OSError("offline")

    monkeypatch.setattr(email_change, "deliver", deliver)
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "old@example.com", "password": "correct-password", "displayName": "Learner"},
    )
    headers = {"Authorization": "Bearer " + registration.json()["accessToken"]}
    endpoint = "/api/v1/users/me/email-change/"
    payload = {"email": "new@example.com", "currentPassword": "correct-password"}
    assert (
        await client.post(endpoint + "request", headers=headers, json=payload)
    ).status_code == 503
    app.dependency_overrides[get_settings] = lambda: Settings(reset_delivery="smtp")
    assert (
        await client.post(
            endpoint + "request", headers=headers, json={**payload, "currentPassword": "wrong"}
        )
    ).status_code == 400
    response = await client.post(endpoint + "request", headers=headers, json=payload)
    assert response.status_code == (503 if mode == "delivery_failed" else 204)
    assert (await client.get("/api/v1/users/me", headers=headers)).json()[
        "email"
    ] == "old@example.com"
    record = await db_session.scalar(select(EmailChange))
    assert record is not None
    raw = sent[0][1]
    assert record.token_hash != raw
    assert sent[0][0] == "new@example.com"
    if mode == "expired":
        record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await db_session.commit()
    elif mode == "password_changed":
        assert (
            await client.post(
                "/api/v1/users/me/password",
                headers=headers,
                json={"currentPassword": "correct-password", "newPassword": "replacement-password"},
            )
        ).status_code == 204
    elif mode == "superseded":
        assert (
            await client.post(endpoint + "request", headers=headers, json=payload)
        ).status_code == 204
    elif mode == "taken":
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "correct-password",
                "displayName": "Other",
            },
        )
    confirmed = await client.post(endpoint + "confirm", json={"token": raw})
    assert confirmed.status_code == (204 if mode == "success" else 409 if mode == "taken" else 400)
    if mode == "success":
        assert (await client.get("/api/v1/users/me", headers=headers)).json()[
            "email"
        ] == "new@example.com"
        sessions = (await db_session.scalars(select(RefreshToken))).all()
        assert all(session.revoked_at is not None for session in sessions)
        assert (await client.post(endpoint + "confirm", json={"token": raw})).status_code == 400
