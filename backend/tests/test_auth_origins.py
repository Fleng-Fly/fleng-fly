"""Production template must allow both public origins behind TLS termination."""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import Settings, get_settings
from app.db.models import RequestLimit, User
from app.db.session import get_db
from app.main import create_app

RENDER = "https://fleng-fly.onrender.com"
NETLIFY = "https://fleng.netlify.app"
REGISTER = "/api/v1/auth/register"
PAYLOAD = {
    "email": "origin-regression@example.com",
    "password": "origin-regression-password",
    "displayName": "Origin regression",
}


@pytest_asyncio.fixture(params=["explicit-origins", "render-runtime"])
async def production_client(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> AsyncGenerator[AsyncClient, None]:
    monkeypatch.delenv("CORS_ORIGIN", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    if request.param == "render-runtime":
        # Reproduce the deployed allowlist (Netlify only), plus Render's own env.
        monkeypatch.setenv("CORS_ORIGIN", NETLIFY)
        monkeypatch.setenv("RENDER_EXTERNAL_URL", RENDER)
    settings = Settings(
        _env_file=Path(__file__).resolve().parents[2] / ".env.production.example",
        jwt_access_secret="isolated-origin-test-secret-at-least-32-characters",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    assert settings.is_production
    assert set(settings.cors_origins) == {RENDER, NETLIFY}
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    app = create_app()

    async def isolated_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db] = isolated_db
    # Uvicorn without trusted proxy headers sees HTTP even on public HTTPS.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://fleng-fly.onrender.com"
    ) as client:
        yield client


@pytest.mark.parametrize("origin", [RENDER, NETLIFY])
async def test_anonymous_registration_behind_tls_proxy(
    production_client: AsyncClient, origin: str
) -> None:
    assert not production_client.cookies
    response = await production_client.post(REGISTER, json=PAYLOAD, headers={"Origin": origin})
    assert response.status_code == 201, response.text
    assert response.json()["accessToken"]
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    cookie = response.headers["set-cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert (await production_client.get("/api/v1/users/me")).status_code == 401
    login = await production_client.post(
        "/api/v1/auth/login", json=PAYLOAD, headers={"Origin": origin}
    )
    assert login.status_code == 200
    # HTTP test transport cannot automatically send Secure cookies.
    headers = {"Origin": origin, "Cookie": f"fleng_refresh={login.cookies['fleng_refresh']}"}
    assert (
        await production_client.post("/api/v1/auth/refresh", headers=headers)
    ).status_code == 200
    assert (await production_client.post("/api/v1/auth/logout", headers=headers)).status_code == 204


@pytest.mark.parametrize(
    "origin",
    [
        "https://untrusted.example",
        "null",
        RENDER + ".evil.example",
        "http://fleng-fly.onrender.com:99",
    ],
)
async def test_untrusted_registration_rejected_before_throttle_or_writes(
    production_client: AsyncClient,
    db_session: AsyncSession,
    origin: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="fleng"):
        response = await production_client.post(
            REGISTER,
            json=PAYLOAD,
            headers={
                "Origin": origin,
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "untrusted.example",
            },
        )
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Origin not allowed"
    assert "access-control-allow-origin" not in response.headers
    assert "set-cookie" not in response.headers
    assert await db_session.scalar(select(func.count()).select_from(User)) == 0
    assert await db_session.scalar(select(func.count()).select_from(RequestLimit)) == 0
    assert "host='fleng-fly.onrender.com' scheme=http" in caplog.text
    assert PAYLOAD["email"] not in caplog.text
    assert PAYLOAD["password"] not in caplog.text


@pytest.mark.parametrize(
    "origin, expected", [(RENDER, 200), (NETLIFY, 200), ("https://untrusted.example", 400)]
)
async def test_production_preflight(
    production_client: AsyncClient, origin: str, expected: int
) -> None:
    response = await production_client.options(
        REGISTER,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == expected
    assert response.headers.get("access-control-allow-origin") == (
        origin if expected == 200 else None
    )


@pytest.mark.parametrize(
    "peer, proto, forwarded_host, expected_scheme, expected_status",
    [
        ("10.0.0.7", "https", "evil.example", "https", 401),
        ("198.51.100.7", "https", "fleng-fly.onrender.com", "http", 403),
        ("10.0.0.7", "https,http", "fleng-fly.onrender.com", "http", 403),
        ("10.0.0.7", "garbage", "fleng-fly.onrender.com", "http", 403),
        ("10.0.0.7", "http", "fleng-fly.onrender.com", "http", 403),
    ],
)
async def test_uvicorn_only_applies_proto_from_trusted_peer(
    monkeypatch: pytest.MonkeyPatch,
    peer: str,
    proto: str,
    forwarded_host: str,
    expected_scheme: str,
    expected_status: int,
) -> None:
    from starlette.requests import Request

    settings = Settings(_env_file=None, cors_origin=NETLIFY, render_external_url="")
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    observed = {}

    async def record_scope(scope, receive, send):
        request = Request(scope)
        observed.update(scheme=request.url.scheme, host=request.headers["host"])
        await app(scope, receive, send)

    proxy = ProxyHeadersMiddleware(record_scope, trusted_hosts="10.0.0.7")
    async with AsyncClient(
        transport=ASGITransport(app=proxy, client=(peer, 1234)),
        base_url="http://fleng-fly.onrender.com",
    ) as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={
                "Origin": RENDER,
                "X-Forwarded-Proto": proto,
                "X-Forwarded-Host": forwarded_host,
                "Forwarded": 'proto=https;host="fleng-fly.onrender.com"',
            },
        )
    # 401 means the same-origin guard passed, but no session cookie was supplied.
    assert response.status_code == expected_status
    assert observed == {"scheme": expected_scheme, "host": "fleng-fly.onrender.com"}


async def test_trusted_proxy_cannot_rewrite_host_to_allow_attacker_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(_env_file=None, cors_origin=NETLIFY, render_external_url=RENDER)
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    proxy = ProxyHeadersMiddleware(app, trusted_hosts="127.0.0.1")
    async with AsyncClient(
        transport=ASGITransport(app=proxy), base_url="http://fleng-fly.onrender.com"
    ) as client:
        for path in (REGISTER, "/api/v1/auth/login", "/api/v1/auth/refresh"):
            response = await client.post(
                path,
                json=PAYLOAD,
                headers={
                    "Origin": "https://evil.example",
                    "X-Forwarded-Proto": "https",
                    "X-Forwarded-Host": "evil.example",
                    "X-Forwarded-For": "198.51.100.7",
                },
            )
            assert response.status_code == 403
