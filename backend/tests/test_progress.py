"""Progress endpoint tests."""

from httpx import AsyncClient

PROGRESS = "/api/v1/progress/me"
REGISTER = "/api/v1/auth/register"


async def _register(client: AsyncClient, email: str = "progress@example.com") -> str:
    response = await client.post(
        REGISTER,
        json={"email": email, "password": "correct-horse-battery", "displayName": "P"},
    )
    return response.json()["accessToken"]


async def test_progress_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(PROGRESS)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_progress_starts_at_zero(client: AsyncClient) -> None:
    token = await _register(client)
    response = await client.get(PROGRESS, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["lessonsStarted"] == 0
    assert body["lessonsCompleted"] == 0
    assert body["studyMinutes"] == 0
    assert body["lastActivityAt"] is None
    assert body["userId"]
