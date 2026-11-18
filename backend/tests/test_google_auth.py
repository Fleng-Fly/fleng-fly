"""Google sign-in: state/PKCE handling, ID-token validation and safe account linking."""

import time
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models import OAuthIdentity, RefreshToken, User
from app.main import app
from app.modules.auth import google
from app.modules.auth.google import GoogleAuthError, GoogleProfile, verify_claims

START = "/api/v1/auth/google/start"
CALLBACK = "/api/v1/auth/google/callback"
CLIENT_ID = "test-client.apps.googleusercontent.com"
SETTINGS = Settings(
    google_client_id=CLIENT_ID,
    google_client_secret="secret",
    google_redirect_uri="http://testserver/api/v1/auth/google/callback",
)
COOKIE = get_settings().refresh_cookie_name


class FakeGoogle:
    """Stands in for Google's token endpoint and JWKS."""

    def __init__(self) -> None:
        self.profile = GoogleProfile(subject="sub-1", email="ada@example.com", name="Ada")
        self.codes: list[tuple[str, str]] = []
        self.fail: str | None = None

    async def exchange_code(self, code: str, verifier: str) -> str:
        self.codes.append((code, verifier))
        if self.fail:
            raise GoogleAuthError(self.fail)
        return "id-token"

    async def verify_id_token(self, id_token: str, nonce: str) -> GoogleProfile:
        return self.profile


@pytest_asyncio.fixture
async def fake(client: AsyncClient) -> AsyncGenerator[FakeGoogle, None]:
    instance = FakeGoogle()
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    app.dependency_overrides[google.get_google_client] = lambda: instance
    yield instance
    app.dependency_overrides.pop(get_settings, None)
    app.dependency_overrides.pop(google.get_google_client, None)


async def begin(client: AsyncClient, page: str = "login") -> str:
    """Run /start and return the `state` Google would echo back."""
    response = await client.get(START, params={"page": page}, follow_redirects=False)
    assert response.status_code == 302
    return parse_qs(urlsplit(response.headers["location"]).query)["state"][0]


async def finish(client: AsyncClient, state: str, **extra: str):
    params = {"code": "auth-code", "state": state, **extra}
    return await client.get(CALLBACK, params=params, follow_redirects=False)


async def test_providers_reports_configuration(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/providers")).json() == {"google": False}
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    try:
        assert (await client.get("/api/v1/auth/providers")).json() == {"google": True}
    finally:
        app.dependency_overrides.pop(get_settings, None)


async def test_start_when_not_configured_redirects_with_error(client: AsyncClient) -> None:
    response = await client.get(START, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login.html?error=google_unavailable"


async def test_start_builds_pkce_request_and_state_cookie(
    client: AsyncClient, fake: FakeGoogle
) -> None:
    response = await client.get(START, follow_redirects=False)
    url = urlsplit(response.headers["location"])
    query = {k: v[0] for k, v in parse_qs(url.query).items()}
    assert url.netloc == "accounts.google.com"
    assert query["client_id"] == CLIENT_ID
    assert query["redirect_uri"] == SETTINGS.google_redirect_uri
    assert query["response_type"] == "code"
    assert query["code_challenge_method"] == "S256"
    assert {"state", "nonce", "code_challenge"} <= query.keys()
    cookie = response.headers["set-cookie"]
    assert google.STATE_COOKIE in cookie and "HttpOnly" in cookie
    assert "client_secret" not in response.headers["location"]


async def test_new_google_user_is_created_and_signed_in(
    client: AsyncClient, fake: FakeGoogle, db_session: AsyncSession
) -> None:
    state = await begin(client)
    response = await finish(client, state)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard.html"
    assert client.cookies.get(COOKIE)
    # The session is restored through the ordinary refresh mechanism.
    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refreshed.json()['accessToken']}"},
    )
    assert me.json()["email"] == "ada@example.com"
    assert me.json()["displayName"] == "Ada"
    # PKCE verifier from the state cookie is what reaches Google's token endpoint.
    assert fake.codes[0][0] == "auth-code" and len(fake.codes[0][1]) >= 43
    assert await db_session.scalar(select(func.count()).select_from(OAuthIdentity)) == 1


async def test_second_sign_in_reuses_account(
    client: AsyncClient, fake: FakeGoogle, db_session: AsyncSession
) -> None:
    await finish(client, await begin(client))
    await finish(client, await begin(client))
    assert await db_session.scalar(select(func.count()).select_from(User)) == 1
    assert await db_session.scalar(select(func.count()).select_from(OAuthIdentity)) == 1


async def test_changed_email_keeps_same_account_by_subject(
    client: AsyncClient, fake: FakeGoogle, db_session: AsyncSession
) -> None:
    await finish(client, await begin(client))
    fake.profile = GoogleProfile(subject="sub-1", email="new@example.com", name="Ada")
    await finish(client, await begin(client))
    assert await db_session.scalar(select(func.count()).select_from(User)) == 1


async def test_links_existing_password_account_and_neutralizes_old_credentials(
    client: AsyncClient, fake: FakeGoogle, db_session: AsyncSession
) -> None:
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": "ada@example.com", "password": "attacker-known-pass", "displayName": "X"},
    )
    assert registered.status_code == 201
    old_refresh = client.cookies.get(COOKIE)
    client.cookies.clear()

    await finish(client, await begin(client))

    assert await db_session.scalar(select(func.count()).select_from(User)) == 1
    assert await db_session.scalar(select(func.count()).select_from(OAuthIdentity)) == 1
    # The pre-registered password and its sessions no longer work.
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "attacker-known-pass"},
    )
    assert login.status_code == 401
    active = await db_session.scalar(
        select(func.count()).select_from(RefreshToken).where(RefreshToken.revoked_at.is_(None))
    )
    assert active == 1  # only the fresh Google session survives
    client.cookies.clear()
    client.cookies.set(COOKIE, old_refresh or "", path="/api/v1/auth")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_other_google_account_with_same_email_is_not_merged(
    client: AsyncClient, fake: FakeGoogle, db_session: AsyncSession
) -> None:
    await finish(client, await begin(client))
    client.cookies.clear()
    fake.profile = GoogleProfile(subject="sub-2", email="ada@example.com", name="Other")
    response = await finish(client, await begin(client))
    assert response.headers["location"].startswith("/login.html?error=")
    assert await db_session.scalar(select(func.count()).select_from(OAuthIdentity)) == 1


async def test_missing_or_wrong_state_is_rejected(client: AsyncClient, fake: FakeGoogle) -> None:
    no_cookie = await client.get(
        CALLBACK, params={"code": "c", "state": "x"}, follow_redirects=False
    )
    assert no_cookie.headers["location"] == "/login.html?error=google_state"
    await begin(client)
    wrong = await finish(client, "not-the-state")
    assert wrong.headers["location"] == "/login.html?error=google_state"
    assert fake.codes == []
    assert not client.cookies.get(COOKIE)


async def test_state_cookie_cannot_be_forged(client: AsyncClient, fake: FakeGoogle) -> None:
    forged = jwt.encode(
        {
            "type": "google_oauth_state",
            "state": "s",
            "nonce": "n",
            "verifier": "v",
            "exp": time.time() + 60,
        },
        "attacker-secret-attacker-secret-0123",
        algorithm="HS256",
    )
    client.cookies.set(google.STATE_COOKIE, forged, path="/api/v1/auth/google")
    response = await finish(client, "s")
    assert response.headers["location"] == "/login.html?error=google_state"


async def test_state_is_single_use(client: AsyncClient, fake: FakeGoogle) -> None:
    state = await begin(client)
    assert (await finish(client, state)).headers["location"] == "/dashboard.html"
    replay = await finish(client, state)
    assert replay.headers["location"] == "/login.html?error=google_state"


async def test_denied_consent_and_provider_failures_redirect_to_page(
    client: AsyncClient, fake: FakeGoogle
) -> None:
    state = await begin(client, "register")
    denied = await client.get(
        CALLBACK, params={"error": "access_denied", "state": state}, follow_redirects=False
    )
    assert denied.headers["location"] == "/register.html?error=google_denied"
    fake.fail = "google_unavailable"
    failed = await finish(client, await begin(client))
    assert failed.headers["location"] == "/login.html?error=google_unavailable"


# ── ID-token validation ───────────────────────────────────────────────────

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(**overrides: object) -> str:
    now = int(time.time())
    claims: dict[str, object] = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "123",
        "email": "Ada@Example.com",
        "email_verified": True,
        "name": "Ada",
        "nonce": "n1",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, _KEY, algorithm="RS256")


def test_valid_token_yields_normalized_profile() -> None:
    profile = verify_claims(_token(), _KEY.public_key(), SETTINGS, "n1")
    assert profile == GoogleProfile(subject="123", email="ada@example.com", name="Ada")


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"aud": "other-client"}, "google_failed"),
        ({"iss": "https://evil.example"}, "google_failed"),
        ({"exp": int(time.time()) - 10}, "google_failed"),
        ({"nonce": "different"}, "google_failed"),
        ({"nonce": None}, "google_failed"),
        ({"email_verified": False}, "google_unverified"),
        ({"email_verified": "true"}, "google_unverified"),
        ({"email_verified": None}, "google_unverified"),
        ({"email": None}, "google_unverified"),
        ({"sub": None}, "google_failed"),
    ],
)
def test_invalid_claims_are_rejected(overrides: dict, code: str) -> None:
    with pytest.raises(GoogleAuthError) as caught:
        verify_claims(_token(**overrides), _KEY.public_key(), SETTINGS, "n1")
    assert caught.value.code == code


def test_token_signed_by_another_key_is_rejected() -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(GoogleAuthError):
        verify_claims(_token(), other.public_key(), SETTINGS, "n1")


def test_hs256_algorithm_confusion_is_rejected() -> None:
    forged = jwt.encode(
        {
            "iss": "accounts.google.com",
            "aud": CLIENT_ID,
            "sub": "1",
            "iat": 1,
            "exp": int(time.time()) + 60,
            "nonce": "n1",
            "email": "a@b.co",
            "email_verified": True,
        },
        "secret-key-of-at-least-thirty-two-bytes!",
        algorithm="HS256",
    )
    with pytest.raises(GoogleAuthError):
        verify_claims(forged, "secret-key-of-at-least-thirty-two-bytes!", SETTINGS, "n1")
