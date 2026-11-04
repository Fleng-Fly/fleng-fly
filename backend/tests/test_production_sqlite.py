"""Production starts on an empty disk and preserves data on process-only restart."""

import os
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest

from app.core.config import BACKEND_ROOT


def production_env(path: Path) -> dict[str, str]:
    return {
        **os.environ,
        "APP_ENV": "production",
        "DATABASE_URL": f"sqlite+aiosqlite:///{path}",
        "JWT_ACCESS_SECRET": "isolated-production-test-secret-never-deploy",
        "CORS_ORIGIN": "https://fleng.example",
        "COOKIE_SECURE": "true",
        "COOKIE_SAMESITE": "lax",
        "TRUSTED_PROXY_IPS": "",
        "AI_ENABLED": "false",
        "PYTHONPATH": str(BACKEND_ROOT),
    }


@contextmanager
def server(env, tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        env = {**env, "PORT": str(sock.getsockname()[1])}
    with (tmp_path / "production.log").open("a+") as log:
        process = subprocess.Popen(
            [sys.executable, str(BACKEND_ROOT / "run.py")],
            cwd=tmp_path,
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{env['PORT']}", timeout=3) as client:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    assert process.poll() is None, "Production launcher exited before readiness"
                    try:
                        if client.get("/api/v1/health/ready").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.1)
                else:
                    pytest.fail("Production launcher readiness timed out")
                yield client
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_fresh_production_sqlite_auth_dashboard_and_restart(tmp_path):
    path = tmp_path / "data" / "render.db"
    env = production_env(path)
    login = {"email": "render-test@example.com", "password": "regression-password-123"}
    origin = {"Origin": "https://fleng.example"}
    with server(env, tmp_path) as client:
        response = client.post(
            "/api/v1/auth/register", json={**login, "displayName": "Render"}, headers=origin
        )
        assert response.status_code == 201
        user_id = response.json()["user"]["id"]
        response = client.post("/api/v1/auth/login", json=login, headers=origin)
        assert response.status_code == 200
        refresh = client.cookies.get("fleng_refresh")
        assert "Secure" in response.headers["set-cookie"]
        # HTTP transport cannot send Secure cookies automatically; model HTTPS explicitly.
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
            headers={**origin, "Cookie": f"fleng_refresh={refresh}"},
        )
        assert response.status_code == 200
        saved_refresh = client.cookies.get("fleng_refresh")
        assert saved_refresh != refresh
        auth = {"Authorization": f"Bearer {response.json()['accessToken']}"}
        assert client.get("/dashboard.html").status_code == 200
        for route in ("users/me", "progress/me", "streaks/me", "vocabulary/stats"):
            assert client.get(f"/api/v1/{route}", headers=auth).status_code == 200
        lesson = client.get("/api/v1/lessons/greetings-and-introductions").json()
        assert (
            client.post(
                "/api/v1/lessons/greetings-and-introductions/start", json={}, headers=auth
            ).status_code
            == 200
        )
        question = next(e for e in lesson["exercises"] if e["type"] == "single_choice")
        result = client.post(
            "/api/v1/lessons/greetings-and-introductions/submit",
            json={"exerciseId": question["id"], "answer": "a"},
            headers=auth,
        )
        assert result.status_code == 200
        assert result.json()["xpAwarded"] > 0
        progress = client.get("/api/v1/progress/me", headers=auth).json()
        assert progress["xp"] > 0
    with sqlite3.connect(path) as db:
        catalog = db.execute("SELECT count(*) FROM courses").fetchone()
        assert db.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "20261101_1200",
        )
        assert not db.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE '_fleng_write_probe_%'"
        ).fetchall()
        db.execute(
            "UPDATE courses SET title = 'Preserved custom title' WHERE slug = ?",
            ("english-foundations",),
        )
    for course in progress["courses"]:
        if course["slug"] == "english-foundations":
            course["title"] = "Preserved custom title"
    with server(env, tmp_path) as client:
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
            headers={**origin, "Cookie": f"fleng_refresh={saved_refresh}"},
        )
        assert response.status_code == 200
        auth = {"Authorization": f"Bearer {response.json()['accessToken']}"}
        assert client.get("/api/v1/users/me", headers=auth).json()["id"] == user_id
        assert client.get("/api/v1/progress/me", headers=auth).json() == progress
        assert client.post("/api/v1/auth/login", json=login, headers=origin).status_code == 200
        assert client.get("/api/v1/courses/english-foundations").json()["title"] == (
            "Preserved custom title"
        )
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM courses").fetchone() == catalog


@pytest.mark.parametrize(
    "broken",
    ["directory", "memory", "stamped_without_tables", "readonly_file", "readonly_directory"],
)
def test_production_does_not_serve_when_preparation_fails(tmp_path, broken):
    path = tmp_path / "broken.db"
    if broken == "directory":
        path.mkdir()
    if broken == "stamped_without_tables":
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
            db.execute("INSERT INTO alembic_version VALUES ('20261101_1200')")
    if broken.startswith("readonly"):
        if os.geteuid() == 0:
            pytest.skip("Root bypasses filesystem mode bits")
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE existing_data (id INT)")
        if broken == "readonly_file":
            path.chmod(0o444)
        else:
            tmp_path.chmod(0o555)
    env = production_env(path)
    if broken == "memory":
        env["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    try:
        response = subprocess.run(
            [sys.executable, str(BACKEND_ROOT / "run.py")],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
    finally:
        if broken.startswith("readonly"):
            tmp_path.chmod(0o700)
            path.chmod(0o600)
    assert response.returncode == 1
    assert "Database preparation failed" in response.stderr
    assert "Uvicorn running" not in response.stderr
    assert env["JWT_ACCESS_SECRET"] not in response.stderr


def test_postgres_launcher_leaves_migrations_to_release_step(tmp_path):
    env = production_env(tmp_path / "unused.db")
    env["DATABASE_URL"] = "postgresql://test:test@127.0.0.1:1/unreachable"
    response = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import runpy
from unittest.mock import patch
from alembic import command
from app.db import prepare
with patch.object(command, 'upgrade', side_effect=AssertionError('automatic PG migration')), \
     patch.object(prepare, 'ensure_catalog', side_effect=AssertionError('automatic PG seed')), \
     patch('uvicorn.run') as serve:
    runpy.run_path('BACKEND_RUN_PATH', run_name='__main__')
    serve.assert_called_once()
    assert serve.call_args.kwargs['workers'] == 1
""".replace("BACKEND_RUN_PATH", str(BACKEND_ROOT / "run.py")),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert response.returncode == 0, response.stderr
