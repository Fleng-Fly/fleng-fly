"""Run npm dev/auth/dashboard/lesson checks using only a temporary SQLite database."""

import http.cookiejar
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="fleng-smoke-") as directory:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = dict(
            os.environ,
            DATABASE_URL=f"sqlite+aiosqlite:///{directory}/smoke.db",
            PORT=str(port),
            APP_ENV="development",
            COOKIE_SECURE="false",
            JWT_ACCESS_SECRET="isolated-smoke-test-secret-not-for-deployment",
            RESET_DELIVERY="disabled",
            AI_ENABLED="false",
        )
        cookies = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookies)
        )

        def call(path, payload=None, *, token=None, cookie=None, expected=200):
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if cookie:
                headers["Cookie"] = cookie
            data = None
            if payload is not None:
                data = json.dumps(payload).encode()
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(base + path, data=data, headers=headers)
            try:
                response = opener.open(request, timeout=3)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                assert response.status == expected, (path, response.status)
                body = response.read()
                return (
                    json.loads(body)
                    if body and "json" in response.headers.get("Content-Type", "")
                    else body
                )

        def start(log):
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("npm run dev exited; inspect the smoke log")
                    try:
                        health = call("/api/v1/health")
                        assert health["database"] == "up"
                        return process
                    except (OSError, AssertionError):
                        time.sleep(0.2)
                raise TimeoutError("npm run dev readiness timeout")
            except BaseException:
                stop(process)
                raise

        def stop(process):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)

        login = {"email": "smoke@example.com", "password": "smoke-password-123"}
        with open(Path(directory) / "server.log", "w+") as log:
            process = start(log)
            try:
                registered = call(
                    "/api/v1/auth/register",
                    {**login, "displayName": "Smoke"},
                    expected=201,
                )
                user_id = registered["user"]["id"]
                access = call("/api/v1/auth/login", login)["accessToken"]
                old = next(c for c in cookies if c.name == "fleng_refresh").value
                access = call("/api/v1/auth/refresh", {})["accessToken"]
                new = next(c for c in cookies if c.name == "fleng_refresh").value
                assert new != old
                call(
                    "/api/v1/auth/refresh",
                    {},
                    cookie=f"fleng_refresh={old}",
                    expected=401,
                )
                call(
                    "/api/v1/auth/refresh",
                    {},
                    cookie=f"fleng_refresh={new}",
                    expected=401,
                )
                access = call("/api/v1/auth/login", login)["accessToken"]
                for path in (
                    "/dashboard.html",
                    "/lesson.html",
                    "/api/v1/users/me",
                    "/api/v1/progress/me",
                    "/api/v1/streaks/me",
                    "/api/v1/achievements/me",
                    "/api/v1/vocabulary/stats",
                    "/api/v1/ai/recommendations",
                ):
                    call(path, token=access)
                assert call("/api/v1/courses")
                lesson = call("/api/v1/lessons/greetings-and-introductions")
                call(
                    "/api/v1/lessons/greetings-and-introductions/start",
                    {},
                    token=access,
                )
                question = next(
                    e for e in lesson["exercises"] if e["type"] == "single_choice"
                )
                payload = {"exerciseId": question["id"], "answer": "a"}
                first = call(
                    "/api/v1/lessons/greetings-and-introductions/submit",
                    payload,
                    token=access,
                )
                again = call(
                    "/api/v1/lessons/greetings-and-introductions/submit",
                    payload,
                    token=access,
                )
                assert first["xpAwarded"] > 0 and again["xpAwarded"] == 0
                call(
                    "/api/v1/lessons/greetings-and-introductions/progress", token=access
                )
                xp = call("/api/v1/progress/me", token=access)["xp"]
                call(
                    "/api/v1/users/me/password",
                    {
                        "currentPassword": login["password"],
                        "newPassword": "smoke-new-password-456",
                    },
                    token=access,
                    expected=204,
                )
                call("/api/v1/auth/refresh", {}, expected=401)
                login["password"] = "smoke-new-password-456"
                access = call("/api/v1/auth/login", login)["accessToken"]
                call("/api/v1/auth/logout", {}, expected=204)
                call("/api/v1/auth/refresh", {}, expected=401)
            finally:
                stop(process)
            process = start(log)
            try:
                access = call("/api/v1/auth/login", login)["accessToken"]
                assert call("/api/v1/users/me", token=access)["id"] == user_id
                assert call("/api/v1/progress/me", token=access)["xp"] == xp
            finally:
                stop(process)
        print(
            "VERIFIED: npm dev, migrations, SQLite persistence across restart, auth/reuse/password/logout,"
        )
        print(
            "Dashboard APIs and Lessons start/submit/progress; XP awarded once. Only temporary data used."
        )


if __name__ == "__main__":
    main()
