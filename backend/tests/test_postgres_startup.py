"""Real database survives complete app replacement; never point TEST_DATABASE_URL at production."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import BACKEND_ROOT, Settings
from tests.test_production_sqlite import production_env, server


@pytest_asyncio.fixture
async def isolated_pg_database():
    configured = os.environ.get("TEST_DATABASE_URL")
    if not configured:
        pytest.skip("TEST_DATABASE_URL is not configured")
    url = Settings(database_url=configured).database_url
    name = "fleng_durability_" + uuid4().hex
    admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
    target = make_url(url).set(database=name).render_as_string(hide_password=False)
    created = False
    try:
        async with admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        yield target
    finally:
        if created:
            async with admin.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{name}"'))
        await admin.dispose()


def hosted_env(url, tmp_path):
    return {
        **production_env(tmp_path / "must-not-be-used.db"),
        "DATABASE_URL": url,
        "RENDER_EXTERNAL_URL": "https://fleng.example",
    }


async def test_postgres_startup_account_progress_and_cards_survive_new_app_process(
    isolated_pg_database, tmp_path
):
    url = isolated_pg_database
    env = hosted_env(url, tmp_path)
    origin = {"Origin": "https://fleng.example"}
    login = {"email": "durable@example.com", "password": "durable-test-password-123"}
    with server(env, tmp_path) as client:
        courses = client.get("/api/v1/courses").json()
        assert len(courses) == 7
        registered = client.post(
            "/api/v1/auth/register",
            headers=origin,
            json={**login, "displayName": "Durable learner"},
        )
        assert registered.status_code == 201
        auth = {"Authorization": "Bearer " + registered.json()["accessToken"]}
        refresh = client.cookies.get("fleng_refresh")
        lesson = client.get("/api/v1/lessons/the-verb-to-be").json()
        submission = {"exerciseId": lesson["exercises"][0]["id"], "answer": "b"}
        route = "/api/v1/lessons/the-verb-to-be/submit"
        assert client.post(route, headers=auth, json=submission).json()["xpAwarded"] > 0
        assert (
            client.post(
                "/api/v1/vocabulary",
                headers=auth,
                json={"word": "durable", "translation": "постійний"},
            ).status_code
            == 201
        )
        cards = client.post(
            "/api/v1/vocabulary/flashcards/sessions", headers=auth, json={"source": "my_words"}
        ).json()
        user = client.get("/api/v1/users/me", headers=auth).json()
        progress = client.get("/api/v1/progress/me", headers=auth).json()
    # The original ASGI worker/pool no longer exist. A fresh process uses the same external DB.
    with server(env, tmp_path) as client:
        assert client.get("/api/v1/courses").json() == courses
        assert client.get("/api/v1/users/me", headers=auth).json() == user
        assert client.get("/api/v1/progress/me", headers=auth).json() == progress
        assert (
            client.post(
                "/api/v1/auth/refresh", headers={**origin, "Cookie": "fleng_refresh=" + refresh}
            ).status_code
            == 200
        )
        assert client.post("/api/v1/auth/login", headers=origin, json=login).status_code == 200
        assert client.post(route, headers=auth, json=submission).json()["xpAwarded"] == 0
        card_route = "/api/v1/vocabulary/flashcards/sessions/" + cards["sessionId"]
        assert client.get(card_route, headers=auth).json() == cards
    assert not (tmp_path / "must-not-be-used.db").exists()


@pytest.mark.parametrize("versioned", [False, True])
async def test_existing_postgres_data_is_never_auto_migrated_or_reset(
    isolated_pg_database, tmp_path, versioned
):
    url = isolated_pg_database
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("CREATE TABLE keep_me (value TEXT)"))
            await connection.execute(text("INSERT INTO keep_me VALUES ('saved learner data')"))
            if versioned:
                await connection.execute(
                    text("CREATE TABLE alembic_version (version_num VARCHAR(32))")
                )
                await connection.execute(text("INSERT INTO alembic_version VALUES ('old_release')"))
        result = subprocess.run(
            [sys.executable, str(BACKEND_ROOT / "run.py")],
            cwd=tmp_path,
            env=hosted_env(url, tmp_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1 and "Startup" in result.stderr
        async with engine.connect() as connection:
            assert (
                await connection.scalar(text("SELECT value FROM keep_me")) == "saved learner data"
            )
            tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            assert "users" not in tables
            if versioned:
                assert (
                    await connection.scalar(text("SELECT version_num FROM alembic_version"))
                    == "old_release"
                )
    finally:
        await engine.dispose()


async def test_failed_fresh_postgres_bootstrap_rolls_back_all_schema_and_seed(
    isolated_pg_database, monkeypatch
):
    from app.db import prepare

    engine = create_async_engine(isolated_pg_database)
    monkeypatch.setattr(prepare, "engine", engine)
    monkeypatch.setattr(prepare, "OWNER_AUTHORIZED_CURRICULUM_SHA", "not-approved")
    with pytest.raises(ValueError, match="SHA"):
        await prepare.prepare_postgres()
    try:
        async with engine.connect() as connection:
            assert await connection.run_sync(lambda sync: inspect(sync).get_table_names()) == []
    finally:
        await engine.dispose()
