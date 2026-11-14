from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

import pytest

from desktop.runtime import DesktopServer, InstanceLock, StartupCancelled, prepare_user_data

ROOT = Path(__file__).resolve().parents[2]
HTTP = build_opener(ProxyHandler({}))


def request(origin, path, data=None, token=None, method=None):
    headers = {"Content-Type": "application/json", "Origin": origin}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(
        origin + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers=headers,
        method=method,
    )
    with HTTP.open(req, timeout=10) as response:
        return json.load(response)


def test_data_migration_and_secret_survive_updates(tmp_path):
    root, data = tmp_path / "old", tmp_path / "data"
    old = root / "backend/data/fleng.db"
    old.parent.mkdir(parents=True)
    with sqlite3.connect(old) as db:
        db.execute("CREATE TABLE sample (value TEXT)")
        db.execute("INSERT INTO sample VALUES ('saved progress')")
    prepare_user_data(data, root)
    secret = (data / "jwt-secret.txt").read_text()
    assert len(secret) >= 48
    with sqlite3.connect(data / "fleng.db") as db:
        assert db.execute("SELECT value FROM sample").fetchone()[0] == "saved progress"
    with sqlite3.connect(old) as db:
        db.execute("UPDATE sample SET value = 'different old value'")
    prepare_user_data(data, root)
    assert (data / "jwt-secret.txt").read_text() == secret
    with sqlite3.connect(data / "fleng.db") as db:
        assert db.execute("SELECT value FROM sample").fetchone()[0] == "saved progress"


def test_second_process_cannot_take_lock(tmp_path):
    lock = InstanceLock(tmp_path)
    script = (
        "from pathlib import Path; from desktop.runtime import InstanceLock,AlreadyRunning; "
        "import sys\n"
        "try: lock=InstanceLock(Path(sys.argv[1]))\n"
        "except AlreadyRunning: sys.exit(7)\n"
    )
    try:
        result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], cwd=ROOT)
        assert result.returncode == 7
    finally:
        lock.close()
    again = InstanceLock(tmp_path)
    again.close()


def test_cancel_before_start_has_no_process(tmp_path):
    server = DesktopServer(ROOT, tmp_path)
    server.stop()
    with pytest.raises(StartupCancelled):
        server.start()
    assert server.process is None


def test_real_backend_autostarts_and_preserves_account(tmp_path):
    server = DesktopServer(ROOT, tmp_path)
    try:
        origin = server.start(timeout=60)
        assert origin.startswith("http://127.0.0.1:")
        with HTTP.open(origin + "/", timeout=5) as response:
            assert b"Fleng" in response.read()
        auth = request(
            origin,
            "/api/v1/auth/register",
            {
                "email": "desktop-test@example.com",
                "password": "Desktop-password-123!",
                "displayName": "Desktop tester",
            },
        )
        me = request(origin, "/api/v1/users/me", token=auth["accessToken"])
        assert me["displayName"] == "Desktop tester"
        pid = server.process.pid
    finally:
        server.stop()
    assert not list(tmp_path.glob("ready-*.json"))
    with pytest.raises((URLError, OSError)):
        HTTP.open(origin + "/api/v1/health", timeout=1)
    second = DesktopServer(ROOT, tmp_path)
    try:
        restarted = second.start(timeout=60)
        assert second.process.pid != pid
        auth = request(
            restarted,
            "/api/v1/auth/login",
            {
                "email": "desktop-test@example.com",
                "password": "Desktop-password-123!",
            },
        )
        assert auth["user"]["displayName"] == "Desktop tester"
    finally:
        second.stop()


def test_parent_crash_closes_backend_pipe(tmp_path):
    # Simulate the GUI process disappearing without calling server.stop().
    code = (
        "from pathlib import Path; from desktop.runtime import DesktopServer; import os,sys; "
        "s=DesktopServer(Path(sys.argv[1]),Path(sys.argv[2])); "
        "url=s.start(); print(url,flush=True); os._exit(0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT), str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    import time

    deadline = time.monotonic() + 8
    while list(tmp_path.glob("ready-*.json")) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not list(tmp_path.glob("ready-*.json")), (tmp_path / "backend.log").read_text()
    with pytest.raises((URLError, OSError)):
        HTTP.open(result.stdout.strip() + "/api/v1/health", timeout=1)
