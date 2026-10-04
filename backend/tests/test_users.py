"""Users endpoint tests. No database required."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_user_id
from app.core.config import Settings
from app.core.config import get_settings as get_settings_dep
from app.db.models import Profile, User
from app.db.session import get_db
from app.main import app


class FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class FakeSession:
    def __init__(self, user: object) -> None:
        self._user = user

    async def execute(self, *_args, **_kwargs) -> FakeResult:
        return FakeResult(self._user)

    def add(self, _obj: object) -> None:
        return None

    async def commit(self) -> None:
        return None


def make_user() -> User:
    user = User(
        id=uuid.uuid4(),
        email="dev@fleng.local",
        password_hash="dev-only-not-a-login-credential",
    )
    user.created_at = datetime.now(UTC)
    user.profile = Profile(display_name="Dev Learner", level=1, xp=0)
    return user


def test_users_me_returns_profile() -> None:
    user = make_user()

    async def override_db() -> AsyncGenerator[object, None]:
        yield FakeSession(user)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    try:
        response = TestClient(app).get("/api/v1/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "dev@fleng.local"
    assert body["displayName"] == "Dev Learner"
    assert body["level"] == 1
    assert body["xp"] == 0
    assert "createdAt" in body


def test_dev_auth_dependency_rejects_production() -> None:
    settings = Settings(app_env="production")
    try:
        get_current_user_id(settings)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:  # pragma: no cover - defensive
        raise AssertionError("production must reject the dev auth stub")


def test_users_me_is_unauthorized_in_production() -> None:
    # Override only the settings dependency; the dev-auth dependency then sees
    # APP_ENV=production and must refuse.
    app.dependency_overrides[get_settings_dep] = lambda: Settings(app_env="production")
    try:
        response = TestClient(app).get("/api/v1/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
