"""Health endpoint tests. No database required."""

from collections.abc import AsyncGenerator

from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient


class OkSession:
    async def execute(self, *_args, **_kwargs) -> None:
        return None


class BrokenSession:
    async def execute(self, *_args, **_kwargs) -> None:
        raise RuntimeError("database down")


def override_db(session: object):
    async def _override() -> AsyncGenerator[object, None]:
        yield session

    return _override


def test_health_reports_database_up() -> None:
    app.dependency_overrides[get_db] = override_db(OkSession())
    try:
        response = TestClient(app).get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend"
    assert body["database"] == "up"
    assert body["timestamp"]


def test_health_reports_database_down_without_failing() -> None:
    app.dependency_overrides[get_db] = override_db(BrokenSession())
    try:
        response = TestClient(app).get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["database"] == "down"
