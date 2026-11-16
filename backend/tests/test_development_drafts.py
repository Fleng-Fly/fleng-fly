"""npm dev defaults to all local courses; normal and hosted apps still hide drafts."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.db.curriculum import import_curriculum, load_curriculum
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.development import create_development_app, validate_development_settings
from app.main import create_app
from tests.test_learning_extensions import headers


@pytest.mark.parametrize(
    "changes",
    [
        {"app_env": "production"},
        {"render_external_url": "https://fleng-fly.onrender.com"},
        {"database_url": "sqlite+aiosqlite:///:memory:"},
        {"database_url": "postgresql+asyncpg://test:test@localhost/test"},
    ],
)
def test_local_draft_factory_refuses_hosted_or_nonpersistent_settings(changes):
    settings = Settings(_env_file=None).model_copy(update=changes)
    with pytest.raises(ValueError):
        validate_development_settings(settings)


async def test_existing_accounts_can_learn_all_drafts_only_on_loopback(db_session, monkeypatch):
    await seed_catalog(db_session)
    await import_curriculum(db_session, load_curriculum(), apply=True)
    assert (await import_curriculum(db_session, load_curriculum(), apply=True))["new_rows"] == 0
    settings = Settings(_env_file=None, app_env="development", render_external_url="")
    monkeypatch.setattr("app.development.get_settings", lambda: settings)
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    app = create_development_app()

    async def database():
        yield db_session

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_settings] = lambda: settings
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 1234)),
        base_url="http://127.0.0.1:3001",
    ) as c:
        assert (await c.get("/api/v1/courses")).status_code == 401
        for email in ("first@example.com", "second@example.com"):
            auth = await headers(c, email)
            response = await c.get("/api/v1/courses", headers=auth)
            assert response.headers["x-fleng-mode"] == "local-development-drafts"
            assert len(response.json()) == 7
            assert {row["level"] for row in response.json()} >= {"A0", "A1", "A2", "B1", "B2"}
            lesson = (await c.get("/api/v1/lessons/fleng-a0-classroom", headers=auth)).json()
            word_list = await c.get(
                "/api/v1/vocabulary/course-words?level=A0&limit=100", headers=auth
            )
            assert len(word_list.json()) == 100
            exercise = load_curriculum().courses[0].lessons[0].exercises[0]
            answer = next(
                option.id for option in exercise.options if option.id == exercise.correct_option_id
            )
            submission = {"exerciseId": lesson["exercises"][0]["id"], "answer": answer}
            route = "/api/v1/lessons/fleng-a0-classroom/submit"
            assert (await c.post(route, headers=auth, json=submission)).json()["xpAwarded"] == 1
            assert (await c.post(route, headers=auth, json=submission)).json()["xpAwarded"] == 0
        assert (await c.get("/api/v1/courses", headers={"Host": "evil.example"})).status_code == 400
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("203.0.113.1", 1234)),
        base_url="http://127.0.0.1:3001",
    ) as remote:
        assert (await remote.get("/api/v1/courses")).status_code == 403
    normal = create_app()
    normal.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=normal), base_url="http://testserver") as c:
        assert len((await c.get("/api/v1/courses")).json()) == 2
        assert (await c.get("/api/v1/lessons/fleng-a0-classroom")).status_code == 404
