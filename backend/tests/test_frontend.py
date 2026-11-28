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
        "/leaderboard.html",
        "/settings.html",
        "/courses.html",
        "/course.html",
        "/lesson.html",
        "/vocabulary.html",
        "/reset-password.html",
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
    for tab in ("theory", "practice", "vocabulary"):
        assert f'id="tab-{tab}"' in page.text
    assert 'id="tab-test"' not in page.text
    assert 'id="panel-test"' not in page.text
    assert 'id="panel-vocabulary"' in page.text
    assert "submitAnswer" in script.text
    assert "prefers-reduced-motion" in styles.text


async def test_api_is_reachable_alongside_the_frontend(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_removed_team_page_is_not_served(client: AsyncClient) -> None:
    for path in ("/team.html", "/js/team.js", "/css/team.css"):
        assert (await client.get(path)).status_code == 404, path


async def test_reading_practice_serves_static_files_and_keeps_old_api_retired(
    client: AsyncClient,
) -> None:
    for path in (
        "/reading.html",
        "/js/reading.js",
        "/js/reading-content.js",
        "/js/reading-state.js",
    ):
        assert (await client.get(path)).status_code == 200, path
    for path in (
        "/reading-article.html",
        "/css/reading.css",
        "/api/v1/reading/articles",
        "/api/v1/reading/study-time",
    ):
        assert (await client.get(path)).status_code == 404, path
    workspace = await client.get("/js/workspace.js")
    assert "/reading.html" in workspace.text


async def test_unknown_api_path_keeps_the_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_website_assets_revalidate_conditional_requests(client: AsyncClient) -> None:
    for path in ("/", "/version.json", "/js/workspace.js", "/css/fleng-theme.css", "/sw.js"):
        response = await client.get(path)
        assert response.status_code == 200, path
        assert response.headers["cache-control"] == "no-cache", path
        cached = await client.get(path, headers={"If-None-Match": response.headers["etag"]})
        assert cached.status_code == 304, path
        assert cached.headers["cache-control"] == "no-cache", path
    release = await client.get("/version.json")
    assert release.json()["version"] == "2026.11.16-web"
