"""Independent connections: auth atomicity, bounded hashing and learning writes.

File SQLite is mandatory; PostgreSQL runs the same cases only with TEST_DATABASE_URL.
No application database or existing PostgreSQL schema is used.
"""

import asyncio
import os
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import limits
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.base import Base
from app.db.models import (
    Exercise,
    ExerciseSubmission,
    Lesson,
    PasswordReset,
    Profile,
    Progress,
    RefreshToken,
    RequestLimit,
    User,
)
from app.db.seed import seed_catalog
from app.db.session import get_db
from app.main import create_app
from app.modules.auth import service as auth
from app.modules.auth.security import hash_refresh_token, password_work
from app.modules.exercises.service import submit_answer
from app.modules.users.service import get_user_with_profile

PASSWORD = "original-password-123"
NEW_PASSWORD = "replacement-password-456"


@pytest_asyncio.fixture(params=["sqlite", "postgresql"])
async def connections(request, tmp_path):
    schema = "fleng_stabilization_" + uuid.uuid4().hex
    if request.param == "postgresql":
        if not os.environ.get("TEST_DATABASE_URL"):
            pytest.skip("TEST_DATABASE_URL is not configured; PostgreSQL NOT VERIFIED")
        url = Settings(database_url=os.environ["TEST_DATABASE_URL"]).database_url
        assert url.startswith("postgresql+asyncpg://")
        engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
        async with engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    else:
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{tmp_path / 'isolated.db'}", connect_args={"timeout": 5}
        )

        @event.listens_for(engine.sync_engine, "connect")
        def foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        if request.param == "postgresql":
            async with engine.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()


@pytest_asyncio.fixture
async def isolated_api(connections):
    app = create_app()

    async def independent_session():
        async with connections() as db:
            yield db

    app.dependency_overrides[get_db] = independent_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
    app.dependency_overrides.clear()


async def account(connections):
    async with connections() as db:
        user = await auth.register_user(
            db, email="learner@example.com", password=PASSWORD, display_name="Learner"
        )
        access, refresh = await auth.create_session(db, user=user, settings=get_settings())
        return user.id, access, refresh


async def test_two_refresh_requests_have_only_one_winner(connections, isolated_api):
    user_id, _, raw = await account(connections)
    headers = {"Cookie": f"{get_settings().refresh_cookie_name}={raw}"}
    responses = await asyncio.wait_for(
        asyncio.gather(
            *(isolated_api.post("/api/v1/auth/refresh", headers=headers) for _ in range(2))
        ),
        10,
    )
    assert sorted(r.status_code for r in responses) == [200, 401]
    loser = next(r for r in responses if r.status_code == 401)
    assert loser.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    async with connections() as db:
        rows = (await db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id))).all()
        assert len(rows) == 2  # exactly one successor, never two
        assert all(row.revoked_at is not None for row in rows)  # strict reuse detection
    replay = await isolated_api.post("/api/v1/auth/refresh", headers=headers)
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"


@pytest.mark.parametrize("kind", ["invalid", "expired"])
async def test_invalid_refresh_cannot_create_session(connections, isolated_api, kind):
    _, _, raw = await account(connections)
    if kind == "expired":
        async with connections() as db:
            await db.execute(
                update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(days=1))
            )
            await db.commit()
    else:
        raw = "unknown-token"
    response = await isolated_api.post(
        "/api/v1/auth/refresh", headers={"Cookie": f"{get_settings().refresh_cookie_name}={raw}"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
    async with connections() as db:
        assert await db.scalar(select(func.count()).select_from(RefreshToken)) == 1
        assert (await db.scalar(select(RefreshToken))).revoked_at is None


@pytest.mark.parametrize("failure", ["insert", "commit"])
async def test_failed_rotation_rolls_back_claim(connections, monkeypatch, failure):
    _, _, raw = await account(connections)
    async with connections() as db:
        with monkeypatch.context() as patch:
            if failure == "insert":
                patch.setattr(
                    auth, "generate_refresh_token", lambda: (raw, hash_refresh_token(raw))
                )
                error = IntegrityError
            else:

                async def fail_commit():
                    raise RuntimeError("injected commit failure")

                patch.setattr(db, "commit", fail_commit)
                error = RuntimeError
            with pytest.raises(error):
                await auth.rotate_session(db, raw_token=raw, settings=get_settings())
        # Service must leave a usable session, not a failed transaction.
        record = await db.scalar(select(RefreshToken))
        assert record.revoked_at is None and record.replaced_by_id is None
        assert await db.scalar(select(func.count()).select_from(RefreshToken)) == 1
        await auth.rotate_session(db, raw_token=raw, settings=get_settings())


async def test_parallel_limiter_does_not_overspend(connections):
    async def attempt():
        async with connections() as db:
            try:
                await limits.consume(db, "concurrent", 3, 3600)
                await db.commit()
                return 200
            except ApiError as exc:
                await db.rollback()
                assert exc.status_code == 429
                return 429

    results = await asyncio.wait_for(asyncio.gather(*(attempt() for _ in range(8))), 10)
    assert results.count(200) == 3
    assert results.count(429) == 5
    async with connections() as db:
        assert (await db.scalar(select(RequestLimit))).count == 3


@pytest.mark.parametrize("flow", ["change", "reset"])
async def test_password_mutation_serializes_with_refresh(connections, isolated_api, flow):
    user_id, access, raw = await account(connections)
    async with connections() as db:
        db.add(
            PasswordReset(
                user_id=user_id,
                token_hash=hash_refresh_token("reset-secret-" * 4),
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
            )
        )
        await db.commit()

    async def mutate():
        if flow == "change":
            return await isolated_api.post(
                "/api/v1/users/me/password",
                headers={"Authorization": f"Bearer {access}"},
                json={"currentPassword": PASSWORD, "newPassword": NEW_PASSWORD},
            )
        return await isolated_api.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "reset-secret-" * 4, "password": NEW_PASSWORD},
        )

    changed, refreshed = await asyncio.wait_for(
        asyncio.gather(
            mutate(),
            isolated_api.post(
                "/api/v1/auth/refresh",
                headers={"Cookie": f"{get_settings().refresh_cookie_name}={raw}"},
            ),
        ),
        10,
    )
    assert changed.status_code == 204, changed.text
    assert refreshed.status_code in (200, 401)
    async with connections() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            )
            == 0
        )
        assert await auth.authenticate(db, email="learner@example.com", password=PASSWORD) is None
        assert await auth.authenticate(db, email="learner@example.com", password=NEW_PASSWORD)
        assert (await db.scalar(select(PasswordReset))).used_at is not None
    # Explicit policy: previously issued access JWTs live only until their configured TTL.
    assert (
        await isolated_api.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    ).status_code == 200


async def test_login_checked_before_password_change_cannot_issue_session(connections, isolated_api):
    _, access, _ = await account(connections)
    async with connections() as stale:
        user = await auth.authenticate(stale, email="learner@example.com", password=PASSWORD)
        response = await isolated_api.post(
            "/api/v1/users/me/password",
            headers={"Authorization": f"Bearer {access}"},
            json={"currentPassword": PASSWORD, "newPassword": NEW_PASSWORD},
        )
        assert response.status_code == 204
        with pytest.raises(ApiError) as error:
            await auth.create_session(stale, user=user, settings=get_settings())
        assert error.value.status_code == 401


async def test_concurrent_submissions_preserve_once_only_xp(connections):
    user_id, _, _ = await account(connections)
    async with connections() as db:
        await seed_catalog(db)
        lesson = await db.scalar(select(Lesson).where(Lesson.slug == "greetings-and-introductions"))
        lesson_id = lesson.id
        exercises = list(
            (await db.scalars(select(Exercise).where(Exercise.lesson_id == lesson_id))).all()
        )
        # Leave one objective exercise incomplete so both calls perform the completion transition.
        for exercise in exercises:
            if exercise.type != "single_choice":
                user = await get_user_with_profile(db, user_id)
                await submit_answer(
                    db,
                    user=user,
                    lesson=lesson,
                    exercise=exercise,
                    answer=(exercise.accepted_answers[0] if exercise.type == "text" else "hello"),
                    self_assessment="correct" if exercise.type == "self_check" else None,
                )
        target = next(e for e in exercises if e.type == "single_choice")
        target_id, answer, points = target.id, target.correct_option_id, target.points
        total_points = sum(e.points for e in exercises)

    async def submit():
        async with connections() as db:
            user = await get_user_with_profile(db, user_id)
            lesson = await db.get(Lesson, lesson_id)
            exercise = await db.get(Exercise, target_id)
            return await submit_answer(
                db, user=user, lesson=lesson, exercise=exercise, answer=answer, self_assessment=None
            )

    results = await asyncio.wait_for(asyncio.gather(submit(), submit()), 10)
    assert sum(r.xp_awarded for r in results) == points
    async with connections() as db:
        assert (
            await db.scalar(select(Profile).where(Profile.user_id == user_id))
        ).xp == total_points
        progress = await db.scalar(select(Progress).where(Progress.user_id == user_id))
        assert progress.lessons_started == progress.lessons_completed == 1
        submission = await db.scalar(
            select(ExerciseSubmission).where(
                ExerciseSubmission.user_id == user_id, ExerciseSubmission.exercise_id == target_id
            )
        )
        assert submission.attempts == 2 and submission.xp_awarded


async def test_unique_and_foreign_keys_enforced(connections):
    user_id, _, raw = await account(connections)
    async with connections() as db:
        db.add(
            RefreshToken(
                user_id=uuid.uuid4(),
                token_hash="orphan",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()
        db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=hash_refresh_token(raw),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()
        assert await db.scalar(select(func.count()).select_from(RefreshToken)) == 1


async def test_limiter_boundary_retry_after_and_next_window(db_session, monkeypatch):
    class Clock(datetime):
        current = datetime(2026, 10, 28, 12, 0, 40, tzinfo=UTC)

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr(limits, "datetime", Clock)
    for _ in range(2):
        await limits.consume(db_session, "boundary", 2, 60)
        await db_session.commit()
    with pytest.raises(ApiError) as error:
        await limits.consume(db_session, "boundary", 2, 60)
    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "20"
    await db_session.rollback()
    Clock.current += timedelta(seconds=20)
    await limits.consume(db_session, "boundary", 2, 60)
    await db_session.commit()


@pytest.mark.parametrize("endpoint,limit,seconds", [("login", 2, 60), ("register", 2, 3600)])
async def test_auth_ip_limits_ignore_forwarded_headers(client, endpoint, limit, seconds):
    settings = get_settings().model_copy(
        update={
            "auth_login_ip_per_minute": limit,
            "auth_register_ip_per_hour": limit,
            "auth_login_email_per_minute": 100,
        }
    )
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: settings
    for index in range(limit + 1):
        response = await client.post(
            f"/api/v1/auth/{endpoint}",
            json={
                "email": f"nonexistent{index}@example.com",
                "password": PASSWORD,
                **({"displayName": "Learner"} if endpoint == "register" else {}),
            },
            headers={"X-Forwarded-For": f"192.0.2.{index}"},
        )
        assert response.status_code == (
            (401 if endpoint == "login" else 201) if index < limit else 429
        )
    assert response.json()["error"]["message"] == "Request limit reached"
    assert 1 <= int(response.headers["Retry-After"]) <= seconds


async def test_login_email_limit_is_account_independent(client):
    from app.main import app

    settings = get_settings().model_copy(update={"auth_login_email_per_minute": 2})
    app.dependency_overrides[get_settings] = lambda: settings
    for _ in range(2):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "absent@example.com",
                "password": PASSWORD,
            },
        )
        assert response.status_code == 401
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "ABSENT@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 429
    # A different address still has capacity; the IP window was not exhausted.
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": "another@example.com",
                "password": PASSWORD,
            },
        )
    ).status_code == 401


async def test_password_work_is_bounded_and_does_not_block_loop():
    loop_thread = threading.get_ident()
    running = maximum = 0
    lock = threading.Lock()
    release = threading.Event()

    def expensive():
        nonlocal running, maximum
        assert threading.get_ident() != loop_thread
        with lock:
            running += 1
            maximum = max(maximum, running)
        assert release.wait(3)
        time.sleep(0.01)
        with lock:
            running -= 1
        return True

    tasks = [asyncio.create_task(password_work(expensive)) for _ in range(12)]
    try:
        async with asyncio.timeout(3):
            while maximum < 4:
                await asyncio.sleep(0.005)
            await asyncio.sleep(0.03)  # loop continues while password workers are occupied
            assert maximum <= 4
            release.set()
            assert all(await asyncio.gather(*tasks))
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
    assert maximum == 4

    def broken():
        raise ValueError("injected worker error")

    with pytest.raises(ValueError, match="injected worker error"):
        await password_work(broken)
    assert await password_work(lambda: 42) == 42


async def test_password_change_revokes_all_devices_and_failed_change_preserves_them(
    client, db_session
):
    from tests.test_auth import COOKIE, LOGIN, ME, REFRESH, register

    registered = await register(client)
    access = registered.json()["accessToken"]
    first_cookie = client.cookies.get(COOKIE)
    await client.post(
        LOGIN, json={"email": "learner@example.com", "password": "correct-horse-battery"}
    )
    second_cookie = client.cookies.get(COOKIE)
    headers = {"Authorization": f"Bearer {access}"}
    failed = await client.post(
        f"{ME}/password",
        headers=headers,
        json={"currentPassword": "incorrect", "newPassword": NEW_PASSWORD},
    )
    assert failed.status_code == 400
    rows = (await db_session.scalars(select(RefreshToken))).all()
    assert len(rows) == 2 and all(row.revoked_at is None for row in rows)
    changed = await client.post(
        f"{ME}/password",
        headers=headers,
        json={
            "currentPassword": "correct-horse-battery",
            "newPassword": NEW_PASSWORD,
        },
    )
    assert changed.status_code == 204
    for raw in (first_cookie, second_cookie):
        assert (
            await client.post(REFRESH, headers={"Cookie": f"{COOKIE}={raw}"})
        ).status_code == 401
    assert (await client.get(ME, headers=headers)).status_code == 200  # documented TTL policy


@pytest.mark.parametrize("flow", ["change", "reset"])
async def test_password_transaction_failure_does_not_partially_invalidate(
    connections, isolated_api, monkeypatch, flow
):
    from app.modules.password_reset.service import confirm_reset
    from app.modules.users.router import change_password
    from app.modules.users.schemas import PasswordChange

    user_id, _, raw = await account(connections)
    secret = "reset-secret-" * 4
    async with connections() as db:
        db.add(
            PasswordReset(
                user_id=user_id,
                token_hash=hash_refresh_token(secret),
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
            )
        )
        await db.commit()
    # Simulate a failed HTTP dependency: closing the request session rolls back all writes.
    async with connections() as db:
        user = await get_user_with_profile(db, user_id)

        async def fail_commit():
            raise RuntimeError("injected password commit failure")

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="injected password commit failure"):
            if flow == "change":
                await change_password(
                    PasswordChange(current_password=PASSWORD, new_password=NEW_PASSWORD),
                    current_user=user,
                    db=db,
                )
            else:
                await confirm_reset(db, secret, NEW_PASSWORD)
    async with connections() as db:
        assert await auth.authenticate(db, email="learner@example.com", password=PASSWORD)
        assert (await db.scalar(select(RefreshToken))).revoked_at is None
        assert (await db.scalar(select(PasswordReset))).used_at is None
        await auth.rotate_session(db, raw_token=raw, settings=get_settings())


async def test_hashing_failure_cannot_create_an_account(db_session, monkeypatch):
    def fail_hash(_password):
        raise RuntimeError("injected hashing error")

    monkeypatch.setattr(auth, "hash_password", fail_hash)
    with pytest.raises(RuntimeError, match="injected hashing error"):
        await auth.register_user(
            db_session, email="failure@example.com", password=PASSWORD, display_name="Learner"
        )
    assert await db_session.scalar(select(func.count()).select_from(User)) == 0
    assert await db_session.scalar(select(func.count()).select_from(RefreshToken)) == 0


async def test_email_limit_survives_different_peers(connections):
    app = create_app()
    settings = get_settings().model_copy(update={"auth_login_email_per_minute": 1})
    app.dependency_overrides[get_settings] = lambda: settings

    async def independent_session():
        async with connections() as db:
            yield db

    app.dependency_overrides[get_db] = independent_session
    for index, expected in enumerate((401, 429)):
        async with AsyncClient(
            transport=ASGITransport(app=app, client=(f"192.0.2.{index}", 1234)),
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "target@example.com",
                    "password": PASSWORD,
                },
            )
            assert response.status_code == expected
