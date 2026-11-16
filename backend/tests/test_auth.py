"""Authentication flow tests (register, login, refresh, rotation, reuse, logout)."""

from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import RefreshToken, User
from app.modules.auth.security import hash_refresh_token
from app.modules.auth.service import _normalize_email

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/users/me"
PROGRESS = "/api/v1/progress/me"
COOKIE = get_settings().refresh_cookie_name

PASSWORD = "correct-horse-battery"


async def register(
    client: AsyncClient,
    email: str = "learner@example.com",
    password: str = PASSWORD,
    display_name: str = "Learner",
):
    return await client.post(
        REGISTER,
        json={"email": email, "password": password, "displayName": display_name},
    )


async def login(client: AsyncClient, email: str, password: str):
    return await client.post(LOGIN, json={"email": email, "password": password})


async def test_register_returns_access_token_and_user(client: AsyncClient) -> None:
    response = await register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["accessToken"]
    assert body["expiresIn"] > 0
    assert body["user"]["email"] == "learner@example.com"
    assert body["user"]["displayName"] == "Learner"
    assert body["user"]["level"] == 1
    assert body["user"]["xp"] == 0
    assert "passwordHash" not in body["user"]
    assert client.cookies.get(COOKIE)


async def test_register_hashes_password(client: AsyncClient, db_session: AsyncSession) -> None:
    await register(client, email="hash@example.com")
    user = (
        await db_session.execute(select(User).where(User.email == "hash@example.com"))
    ).scalar_one()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2id$")


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    assert (await register(client)).status_code == 201
    duplicate = await register(client)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_TAKEN"


async def test_register_weak_password_is_rejected(client: AsyncClient) -> None:
    response = await register(client, password="short")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_login_success(client: AsyncClient) -> None:
    await register(client)
    response = await login(client, "learner@example.com", PASSWORD)
    assert response.status_code == 200
    assert response.json()["accessToken"]


async def test_login_wrong_password(client: AsyncClient) -> None:
    await register(client)
    response = await login(client, "learner@example.com", "not-the-password")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_email_is_generic(client: AsyncClient) -> None:
    response = await login(client, "nobody@example.com", PASSWORD)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_refresh_rotates_the_token(client: AsyncClient, db_session: AsyncSession) -> None:
    await register(client)
    old_cookie = client.cookies.get(COOKIE)
    old_hash = hash_refresh_token(old_cookie)

    response = await client.post(REFRESH)
    assert response.status_code == 200
    assert response.json()["accessToken"]
    new_cookie = client.cookies.get(COOKIE)
    assert new_cookie and new_cookie != old_cookie

    old_record = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == old_hash)
        )
    ).scalar_one()
    assert old_record.revoked_at is not None
    assert old_record.replaced_by_id is not None


async def test_refresh_without_cookie_is_rejected(client: AsyncClient) -> None:
    response = await client.post(REFRESH)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


async def test_refresh_reuse_revokes_every_session(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await register(client)
    old_cookie = client.cookies.get(COOKIE)

    rotated = await client.post(REFRESH)
    assert rotated.status_code == 200
    new_cookie = client.cookies.get(COOKIE)

    # Replay the already-rotated token: this is reuse.
    client.cookies.clear()
    client.cookies.set(COOKIE, old_cookie)
    replay = await client.post(REFRESH)
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"

    # The whole session set is revoked, including the newest token.
    rows = (await db_session.execute(select(RefreshToken))).scalars().all()
    assert rows
    assert all(row.revoked_at is not None for row in rows)

    client.cookies.clear()
    client.cookies.set(COOKIE, new_cookie)
    still_dead = await client.post(REFRESH)
    assert still_dead.status_code == 401


async def test_logout_revokes_and_clears_cookie(client: AsyncClient) -> None:
    await register(client)
    assert (await client.post(LOGOUT)).status_code == 204
    assert client.cookies.get(COOKIE) is None
    assert (await client.post(REFRESH)).status_code == 401


async def test_login_accepts_same_origin(client: AsyncClient) -> None:
    # The static frontend is served by this app, so browsers send this Origin on
    # same-origin POSTs. It must not be rejected by the CSRF origin check.
    await register(client)
    response = await client.post(
        LOGIN,
        json={"email": "learner@example.com", "password": PASSWORD},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200


async def test_login_rejects_untrusted_origin(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        LOGIN,
        json={"email": "learner@example.com", "password": PASSWORD},
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_logout_accepts_same_origin(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(LOGOUT, headers={"Origin": "http://testserver"})
    assert response.status_code == 204


async def test_users_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(ME)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_users_me_with_valid_token(client: AsyncClient) -> None:
    registration = await register(client)
    token = registration.json()["accessToken"]
    response = await client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "learner@example.com"


async def test_invalid_access_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get(ME, headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_expired_access_token_is_rejected(client: AsyncClient) -> None:
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_access_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = await client.get(ME, headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


async def test_users_cannot_see_each_other(client: AsyncClient) -> None:
    first = await register(client, email="a@example.com", display_name="A")
    token_a = first.json()["accessToken"]
    second = await register(client, email="b@example.com", display_name="B")
    token_b = second.json()["accessToken"]

    me_a = (await client.get(ME, headers={"Authorization": f"Bearer {token_a}"})).json()
    me_b = (await client.get(ME, headers={"Authorization": f"Bearer {token_b}"})).json()
    assert me_a["email"] == "a@example.com"
    assert me_b["email"] == "b@example.com"
    assert me_a["id"] != me_b["id"]

    progress_a = (
        await client.get(PROGRESS, headers={"Authorization": f"Bearer {token_a}"})
    ).json()
    progress_b = (
        await client.get(PROGRESS, headers={"Authorization": f"Bearer {token_b}"})
    ).json()
    assert progress_a["userId"] == me_a["id"]
    assert progress_b["userId"] == me_b["id"]
    assert progress_a["userId"] != progress_b["userId"]


def test_email_normalization() -> None:
    # Duplicate detection is case-insensitive: emails are lower-cased on the way in.
    assert _normalize_email("  Learner@Example.COM  ") == "learner@example.com"


async def test_register_is_case_insensitive(client: AsyncClient) -> None:
    assert (await register(client, email="Case@Example.com")).status_code == 201
    duplicate = await register(client, email="case@example.com")
    assert duplicate.status_code == 409
