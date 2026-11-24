"""PWA assets coexist with auth/API routes on the real static mount."""

from httpx import AsyncClient


async def test_install_manifest_and_icons(client: AsyncClient) -> None:
    response = await client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.json() == {}


async def test_install_and_offline_routes(client: AsyncClient) -> None:
    for path in ("/install.html", "/offline.html", "/sw.js", "/js/pwa.js"):
        response = await client.get(path)
        assert response.status_code == 200, path
    worker = await client.get("/sw.js")
    assert "javascript" in worker.headers["content-type"]
    for path in (
        "/",
        "/login.html",
        "/register.html",
        "/dashboard.html",
        "/lesson.html",
        "/courses.html",
        "/course.html",
        "/leaderboard.html",
        "/reading.html",
        "/reading-article.html",
        "/settings.html",
        "/install.html",
    ):
        page = await client.get(path)
        assert 'href="/manifest.webmanifest"' not in page.text, path
        if path != "/install.html":
            assert 'src="/js/pwa.js"' in page.text, path
    api = await client.get("/api/v1/nonexistent")
    assert api.status_code == 404
    assert api.json()["error"]["code"] == "NOT_FOUND"
