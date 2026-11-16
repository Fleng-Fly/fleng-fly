"""Preview authorization, real draft rendering payloads and isolation regressions."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import Settings, get_settings
from app.db.curriculum import content_sha, import_curriculum, load_curriculum
from app.db.models import Course, CourseVocabularyItem, Lesson, LessonProgress
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.main import create_app
from app.modules.auth.service import register_user
from app.preview import (
    PREVIEW_DATABASE,
    PREVIEW_KIND,
    load_marker,
    validate_preview_settings,
)


def marker_directory(tmp_path, reviewer_id):
    directory = tmp_path / "preview"
    directory.mkdir(mode=0o700)
    (directory / PREVIEW_DATABASE).touch(mode=0o600)
    marker = dict(
        kind=PREVIEW_KIND,
        database=PREVIEW_DATABASE,
        jwt_secret="isolated-preview-key-" + "x" * 40,
        reviewer_id=str(reviewer_id),
        curriculum_sha=content_sha(load_curriculum()),
    )
    path = directory / "preview.json"
    path.write_text(json.dumps(marker))
    path.chmod(0o600)
    return directory, marker


@pytest_asyncio.fixture
async def preview(db_session, tmp_path, monkeypatch):
    if os.name != "posix":
        pytest.skip("Private preview requires POSIX ownership and permission checks")
    await seed_catalog(db_session)
    await import_curriculum(db_session, load_curriculum(), apply=True)
    user = await register_user(
        db_session,
        email="reviewer@example.com",
        password="review-password",
        display_name="Reviewer",
    )
    await register_user(
        db_session,
        email="other@example.com",
        password="other-password",
        display_name="Other account",
    )
    directory, marker = marker_directory(tmp_path, user.id)
    settings = Settings(
        _env_file=None,
        app_env="development",
        database_url=f"sqlite+aiosqlite:///{directory / PREVIEW_DATABASE}",
        jwt_access_secret=marker["jwt_secret"],
        refresh_cookie_name="fleng_curriculum_preview",
        ai_enabled=False,
        reset_delivery="disabled",
    )
    monkeypatch.setattr("app.preview.get_settings", lambda: settings)
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    from app.preview import create_preview_app

    app = create_preview_app()

    async def database():
        yield db_session

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_settings] = lambda: settings
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 1234)),
        base_url="http://127.0.0.1:3011",
    ) as client:
        yield client, app, user, settings


async def login(client, email="reviewer@example.com", password="review-password"):
    response = await client.post("/api/v1/auth/login", json=dict(email=email, password=password))
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["accessToken"]}


async def test_auth_reviewer_loopback_and_host_guards(preview):
    client, app, _, _ = preview
    assert (await client.get("/api/v1/courses")).status_code == 401
    assert (await client.get("/api/v1/lessons/fleng-a0-classroom")).status_code == 401
    outside = await login(client, "other@example.com", "other-password")
    assert (await client.get("/api/v1/courses", headers=outside)).status_code == 403
    headers = await login(client)
    assert (await client.get("/api/v1/courses", headers=headers)).status_code == 200
    assert (await client.get("/courses.html", headers={"Host": "evil.example"})).status_code == 400
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("198.51.100.9", 1234)),
        base_url="http://127.0.0.1:3011",
    ) as remote:
        assert (await remote.get("/api/v1/courses", headers=headers)).status_code == 403
    assert (
        await client.post("/api/v1/auth/refresh", headers={"Origin": "https://evil.example"})
    ).status_code == 403
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200
    assert "fleng_curriculum_preview" in client.cookies


async def test_all_50_lessons_and_500_words_without_publication(preview, db_session):
    client, _, user, _ = preview
    headers = await login(client)
    catalog = await client.get("/api/v1/courses", headers=headers)
    assert len(catalog.json()) == 7
    assert catalog.headers["cache-control"] == "no-store"
    assert (await client.get("/api/v1/preview/status", headers=headers)).json()[
        "published"
    ] is False
    progress = (await client.get("/api/v1/progress/me", headers=headers)).json()
    assert len(progress["courses"]) == 7
    assert sum(c["lessonsTotal"] for c in progress["courses"]) == 57
    assert progress["xp"] == 0
    for course in load_curriculum().courses:
        detail = (await client.get(f"/api/v1/courses/{course.slug}", headers=headers)).json()
        assert len(detail["lessons"]) == 10
        words = (
            await client.get(
                "/api/v1/vocabulary/course-words",
                headers=headers,
                params={"courseId": detail["id"], "limit": 100},
            )
        ).json()
        assert len(words) == 100
        assert all(w["courseId"] == detail["id"] for w in words)
        assert {(w["word"], w["translation"]) for w in words} == {
            (w.word, w.translation) for lesson in course.lessons for w in lesson.vocabulary
        }
        for lesson in course.lessons:
            response = await client.get(f"/api/v1/lessons/{lesson.slug}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["theory"] == lesson.rendered_theory()
            assert data["courseSlug"] == course.slug
            assert len(data["exercises"]) == 8
            assert "correctOptionId" not in json.dumps(data)
            assert "\ufffd" not in response.text
            assert (
                await client.get(f"/api/v1/lessons/{lesson.slug}/progress", headers=headers)
            ).json()["startedAt"] is None
    assert await db_session.scalar(select(func.count()).select_from(LessonProgress)) == 0
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Course).where(Course.is_published.is_(False))
        )
        == 5
    )
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Lesson).where(Lesson.is_published.is_(False))
        )
        == 50
    )
    assert await db_session.scalar(select(func.count()).select_from(CourseVocabularyItem)) == 500


async def test_exercises_use_existing_grader_and_once_only_xp(preview):
    client, _, _, _ = preview
    headers = await login(client)
    content = load_curriculum().courses[0].lessons[0]
    lesson = (await client.get(f"/api/v1/lessons/{content.slug}", headers=headers)).json()
    url = f"/api/v1/lessons/{content.slug}"
    assert (await client.post(url + "/start", headers=headers)).status_code == 200
    exercise = content.exercises[0]
    payload = dict(
        exerciseId=lesson["exercises"][0]["id"],
        answer=next(o.id for o in exercise.options if o.id != exercise.correct_option_id),
    )
    wrong = (await client.post(url + "/submit", headers=headers, json=payload)).json()
    assert wrong["isCorrect"] is False and wrong["xpAwarded"] == 0
    payload["answer"] = exercise.correct_option_id
    correct = (await client.post(url + "/submit", headers=headers, json=payload)).json()
    assert correct["isCorrect"] is True and correct["xpAwarded"] == 1
    repeated = (await client.post(url + "/submit", headers=headers, json=payload)).json()
    assert repeated["xpAwarded"] == 0
    foreign = await client.post(
        "/api/v1/lessons/fleng-a0-spelling/submit", headers=headers, json=payload
    )
    assert foreign.status_code == 404
    assert (await client.get("/api/v1/progress/me", headers=headers)).json()["xp"] == 1


async def test_normal_app_keeps_drafts_hidden(preview, db_session):
    _, _, _, settings = preview
    app = create_app()

    async def database():
        yield db_session

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_settings] = lambda: settings
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        assert len((await client.get("/api/v1/courses?include_drafts=true")).json()) == 2
        for path in ("/courses/fleng-a0", "/lessons/fleng-a0-classroom", "/preview/status"):
            assert (await client.get("/api/v1" + path)).status_code == 404
        headers = await login(client)
        assert (
            await client.post("/api/v1/lessons/fleng-a0-classroom/start", headers=headers)
        ).status_code == 404
        assert (
            await client.get(
                "/api/v1/vocabulary/course-words", headers=headers, params={"level": "A0"}
            )
        ).json() == []


@pytest.mark.parametrize("change", ["production", "default_db", "key", "cookie", "ai", "sha"])
def test_configuration_fails_closed(tmp_path, change):
    directory, marker = marker_directory(tmp_path, uuid4())
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite+aiosqlite:///{directory / PREVIEW_DATABASE}",
        jwt_access_secret=marker["jwt_secret"],
        refresh_cookie_name="fleng_curriculum_preview",
        ai_enabled=False,
    )
    updates = {
        "production": {"app_env": "production"},
        "default_db": {"database_url": "sqlite+aiosqlite:////tmp/fleng.db"},
        "key": {"jwt_access_secret": "wrong"},
        "cookie": {"refresh_cookie_name": "fleng_refresh"},
        "ai": {"ai_enabled": True},
        "sha": {},
    }
    if change == "sha":
        marker["curriculum_sha"] = "wrong"
        (directory / "preview.json").write_text(json.dumps(marker))
    with pytest.raises(ValueError):
        validate_preview_settings(settings.model_copy(update=updates[change]))


def test_marker_permissions_and_symlinks(tmp_path):
    if os.name != "posix":
        pytest.skip("POSIX ownership and permission checks")
    directory, _ = marker_directory(tmp_path, uuid4())
    marker = directory / "preview.json"
    marker.chmod(0o644)
    with pytest.raises(ValueError, match="private"):
        load_marker(directory)
    marker.chmod(0o600)
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        load_marker(alias)


def test_prepare_refuses_existing_directory_without_writes(tmp_path):
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[2] / "scripts/preview_curriculum.py"
    sentinel = tmp_path / "keep.txt"
    sentinel.write_text("existing user data")
    response = subprocess.run(
        [sys.executable, str(script), "prepare", "--directory", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert response.returncode == 2
    assert sentinel.read_text() == "existing user data"
    assert {p.name for p in tmp_path.iterdir()} == {"keep.txt"}


def test_start_refuses_unprepared_directory_without_creating_database(tmp_path):
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[2] / "scripts/preview_curriculum.py"
    response = subprocess.run(
        [sys.executable, str(script), "start", "--directory", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert response.returncode == 2
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(os.name == "posix", reason="Non-POSIX platform guard")
def test_preview_refuses_platform_without_private_permissions(tmp_path):
    directory, _ = marker_directory(tmp_path, uuid4())
    with pytest.raises(ValueError, match="POSIX"):
        load_marker(directory)
