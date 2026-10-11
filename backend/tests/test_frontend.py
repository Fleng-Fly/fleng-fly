"""The static frontend is served by the FastAPI app, alongside /api/v1.

No separate frontend server or build step exists: these tests confirm the pages,
assets and API coexist on one origin.
"""

from httpx import AsyncClient


async def test_index_is_served(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Fleng" in response.text


async def test_login_page_is_served(client: AsyncClient) -> None:
    response = await client.get("/login.html")
    assert response.status_code == 200
    assert "login-form" in response.text


async def test_app_pages_are_served(client: AsyncClient) -> None:
    for path in (
        "/dashboard.html",
        "/settings.html",
        "/courses.html",
        "/course.html",
        "/lesson.html",
    ):
        response = await client.get(path)
        assert response.status_code == 200, path


async def test_static_javascript_is_served(client: AsyncClient) -> None:
    response = await client.get("/js/api.js")
    assert response.status_code == 200
    assert "apiFetch" in response.text


async def test_api_is_reachable_alongside_the_frontend(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_unknown_api_path_keeps_the_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
