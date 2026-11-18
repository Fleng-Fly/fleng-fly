"""Refresh rotation: a lost response can be retried briefly; replay protection stays strict."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models import RefreshToken
from app.main import app

COOKIE = get_settings().refresh_cookie_name
REFRESH = "/api/v1/auth/refresh"
PASSWORD = "correct-horse-battery"


async def sign_up(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "grace@example.com", "password": PASSWORD, "displayName": "G"},
    )
    assert response.status_code == 201
    return response.json()["accessToken"]


def current(client: AsyncClient) -> str | None:
    """The refresh cookie the browser would send next (the newest one the server set)."""
    values = [c.value for c in client.cookies.jar if c.name == COOKIE]
    return values[-1] if values else None


def use_cookie(client: AsyncClient, value: str | None) -> None:
    client.cookies.clear()
    if value:
        client.cookies.set(COOKIE, value)


async def refresh_with(client: AsyncClient, cookie: str | None):
    use_cookie(client, cookie)
    return await client.post(REFRESH)


async def active(db: AsyncSession) -> int:
    rows = (await db.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))).all()
    return len(rows)


async def age_rotations(db: AsyncSession, seconds: int) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.revoked_at.is_not(None))
        .values(revoked_at=datetime.now(UTC) - timedelta(seconds=seconds))
    )
    await db.commit()


async def test_lost_rotation_response_can_be_retried_with_the_old_cookie(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)

    lost = await client.post(REFRESH)  # the server rotated; assume this response never arrived
    assert lost.status_code == 200
    assert current(client) != original

    retry = await refresh_with(client, original)  # the browser still holds the old cookie
    assert retry.status_code == 200
    healed = current(client)
    assert healed not in (None, original)
    # Exactly one live token remains, and it is the one the browser now holds.
    assert await active(db_session) == 1
    assert (await refresh_with(client, healed)).status_code == 200


async def test_the_unused_successor_of_a_lost_response_cannot_be_used_twice(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)
    await client.post(REFRESH)
    stale_successor = current(client)

    assert (await refresh_with(client, original)).status_code == 200  # graced retry
    # The successor the lost response carried was consumed by that retry: another holder of it
    # is replaying an old token, so it is reuse and everything is revoked after the window.
    await age_rotations(db_session, 60)
    replay = await refresh_with(client, stale_successor)
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    assert await active(db_session) == 0


async def test_replay_after_the_window_revokes_every_session(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200
    await age_rotations(db_session, 11)  # just beyond the default 10 s
    replay = await refresh_with(client, original)
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    assert await active(db_session) == 0


async def test_stale_duplicate_request_after_the_chain_advanced_is_absorbed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An aborted page's request can reach the server after the next pages already refreshed."""
    await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200  # original -> A (new page's request)
    assert (await client.post(REFRESH)).status_code == 200  # A -> B (page after that)
    late = await refresh_with(client, original)  # the first page's request, processed late
    assert late.status_code == 200
    assert await active(db_session) == 1  # one live chain, no second branch
    # ...but the same stale token is reuse once the window has passed.
    await age_rotations(db_session, 11)
    replay = await refresh_with(client, original)
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    assert await active(db_session) == 0


async def test_logout_in_the_middle_of_the_chain_stops_the_walk(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200
    assert (await client.post(REFRESH)).status_code == 200
    assert (await client.post("/api/v1/auth/logout")).status_code == 204
    assert (await refresh_with(client, original)).status_code == 401
    assert await active(db_session) == 0


async def test_logout_is_not_undone_by_the_retry_window(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200
    assert (await client.post("/api/v1/auth/logout")).status_code == 204  # revokes the successor
    replay = await refresh_with(client, original)
    assert replay.status_code == 401
    assert await active(db_session) == 0


async def test_password_change_is_not_undone_by_the_retry_window(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    access = await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200
    changed = await client.post(
        "/api/v1/users/me/password",
        json={"currentPassword": PASSWORD, "newPassword": "another-long-password"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert changed.status_code == 204
    assert (await refresh_with(client, original)).status_code == 401
    assert await active(db_session) == 0


async def test_expired_successor_is_not_resurrected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await sign_up(client)
    original = current(client)
    assert (await client.post(REFRESH)).status_code == 200
    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.revoked_at.is_(None))
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    await db_session.commit()
    assert (await refresh_with(client, original)).status_code == 401


@pytest.mark.parametrize("seconds", [0])
async def test_grace_can_be_disabled_for_strict_reuse_detection(
    client: AsyncClient, db_session: AsyncSession, seconds: int
) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(refresh_reuse_grace_seconds=seconds)
    try:
        await sign_up(client)
        original = current(client)
        assert (await client.post(REFRESH)).status_code == 200
        replay = await refresh_with(client, original)
        assert replay.status_code == 401
        assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
        assert await active(db_session) == 0
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_grace_window_is_bounded() -> None:
    assert Settings().refresh_reuse_grace_seconds == 10
    with pytest.raises(ValueError):
        Settings(refresh_reuse_grace_seconds=61)
    with pytest.raises(ValueError):
        Settings(refresh_reuse_grace_seconds=-1)
