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


async def test_dashboard_shell_assets_are_served(client: AsyncClient) -> None:
    page = await client.get("/dashboard.html")
    styles = await client.get("/css/dashboard.css")
    script = await client.get("/js/dashboard.js")
    workspace = await client.get("/js/workspace.js")
    assert all(response.status_code == 200 for response in (page, styles, script, workspace))
    assert 'id="dashboard-sidebar"' in workspace.text
    assert 'id="your-progress"' in page.text
    assert "prefers-reduced-motion" in styles.text
    assert "getVocabularyStats" in script.text


async def test_lesson_player_assets_are_served(client: AsyncClient) -> None:
    page = await client.get("/lesson.html")
    styles = await client.get("/css/lesson.css")
    script = await client.get("/js/lesson.js")
    assert page.status_code == styles.status_code == script.status_code == 200
    assert 'id="tab-test"' in page.text
    assert 'id="panel-vocabulary"' in page.text
    assert "submitAnswer" in script.text
    assert "prefers-reduced-motion" in styles.text


async def test_api_is_reachable_alongside_the_frontend(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_unknown_api_path_keeps_the_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
