from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.config import Settings, get_settings
from app.db.models import Achievement, LearningActivity, PasswordReset, User, UserAchievement
from app.main import app
from app.modules.auth.security import hash_refresh_token
from app.modules.gamification import service as gamification
from app.modules.password_reset import service as reset
from tests.test_auth import register


async def test_vocabulary_can_filter_own_words_by_lesson(client, db_session):
    from app.db.seed import seed_catalog

    await seed_catalog(db_session)
    learner = await headers(client)
    other = await headers(client, "another@example.com")
    first = (await client.get("/api/v1/lessons/greetings-and-introductions")).json()["id"]
    second = (await client.get("/api/v1/lessons/the-verb-to-be")).json()["id"]
    for auth, lesson_id, word in [
        (learner, first, "hello"), (learner, second, "be"), (other, first, "hi")
    ]:
        response = await client.post(
            "/api/v1/vocabulary", headers=auth,
            json={"word": word, "translation": word, "lessonId": lesson_id},
        )
        assert response.status_code == 201
    result = await client.get(f"/api/v1/vocabulary?lessonId={first}", headers=learner)
    assert result.status_code == 200
    assert [item["word"] for item in result.json()] == ["hello"]
    second_words = await client.get(f"/api/v1/vocabulary?lessonId={second}", headers=learner)
    assert second_words.json()[0]["word"] == "be"


async def headers(client, email="learner@example.com"):
    r = await register(client, email=email)
    assert r.status_code == 201
    return {"Authorization": "Bearer " + r.json()["accessToken"]}


async def definitions(db):
    for code, title, metric, threshold in gamification.DEFINITIONS:
        db.add(Achievement(code=code, title=title, metric=metric, threshold=threshold))
    await db.commit()


@pytest.mark.parametrize(
    "days,today,expected",
    [
        ([], date(2026, 10, 1), (0, 0)),
        ([date(2026, 9, 30)], date(2026, 10, 1), (1, 1)),
        ([date(2026, 9, 29)], date(2026, 10, 1), (0, 1)),
        (
            [date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 1)],
            date(2026, 10, 1),
            (3, 3),
        ),
        ([date(2026, 9, 27), date(2026, 9, 28), date(2026, 10, 1)], date(2026, 10, 1), (1, 2)),
        ([date(2026, 10, 2)], date(2026, 10, 1), (0, 0)),
    ],
)
def test_streak_calendar(days, today, expected):
    assert gamification.calculate_streak(days, today) == expected


def test_timezone_config():
    assert Settings(learning_timezone="Europe/Kyiv").learning_timezone == "Europe/Kyiv"
    with pytest.raises(ValueError):
        Settings(learning_timezone="Not/AZone")


async def test_vocabulary_ownership_and_review(client, db_session):
    auth = await headers(client)
    other = await headers(client, "other@example.com")
    created = await client.post(
        "/api/v1/vocabulary",
        headers=auth,
        json={"word": " Hello ", "translation": "Привіт", "example": "Hello, Sam!"},
    )
    assert created.status_code == 201
    item = created.json()
    assert item["word"] == "hello"
    assert (
        await client.post(
            "/api/v1/vocabulary", headers=auth, json={"word": "HELLO", "translation": "Hi"}
        )
    ).status_code == 409
    for method, suffix, payload in [
        ("patch", "", {"learned": True}),
        ("post", "/review", {"remembered": True}),
    ]:
        response = await getattr(client, method)(
            f"/api/v1/vocabulary/{item['id']}{suffix}", headers=other, json=payload
        )
        assert response.status_code == 404
    assert (await client.get("/api/v1/vocabulary", headers=other)).json() == []
    assert (
        await client.get(f"/api/v1/vocabulary/{item['id']}/reviews", headers=other)
    ).status_code == 404
    for remembered in [False, True]:
        response = await client.post(
            f"/api/v1/vocabulary/{item['id']}/review", headers=auth, json={"remembered": remembered}
        )
        assert response.status_code == 200
        assert response.json()["learned"] == remembered
    history = await client.get(f"/api/v1/vocabulary/{item['id']}/reviews", headers=auth)
    assert len(history.json()) == 2
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    streak = (await client.get("/api/v1/streaks/me", headers=auth)).json()
    assert streak["current"] == streak["longest"] == 1
    assert (
        await client.delete(f"/api/v1/vocabulary/{item['id']}", headers=other)
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/vocabulary/{item['id']}", headers=auth)
    ).status_code == 204


async def test_vocabulary_validation(client):
    auth = await headers(client)
    for payload in [{"word": " ", "translation": "hi"}, {"word": "hi", "translation": " "}]:
        assert (
            await client.post("/api/v1/vocabulary", headers=auth, json=payload)
        ).status_code == 422


async def test_vocabulary_stats_count_only_owned_learned_words(client):
    auth = await headers(client)
    other = await headers(client, "stats-other@example.com")
    assert (await client.get("/api/v1/vocabulary/stats")).status_code == 401
    assert (await client.get("/api/v1/vocabulary/stats", headers=auth)).json() == {
        "wordsLearned": 0
    }
    learned = await client.post(
        "/api/v1/vocabulary", headers=auth, json={"word": "hello", "translation": "привіт"}
    )
    assert learned.status_code == 201
    assert (
        await client.post(
            "/api/v1/vocabulary",
            headers=other,
            json={"word": "world", "translation": "світ"},
        )
    ).status_code == 201
    assert (
        await client.patch(
            f"/api/v1/vocabulary/{learned.json()['id']}",
            headers=auth,
            json={"learned": True},
        )
    ).status_code == 200
    assert (await client.get("/api/v1/vocabulary/stats", headers=auth)).json() == {
        "wordsLearned": 1
    }
    assert (await client.get("/api/v1/vocabulary/stats", headers=other)).json() == {
        "wordsLearned": 0
    }


async def test_achievement_rules_idempotent(client, db_session):
    auth = await headers(client)
    await definitions(db_session)
    user = await db_session.scalar(select(User))
    user.profile.xp = 100
    progress = user.progress if "progress" in user.__dict__ else None
    from app.modules.progress.service import get_or_create_progress

    progress = await get_or_create_progress(db_session, user.id)
    progress.lessons_completed = 10
    today = datetime.now(UTC).date()
    for i in range(7):
        db_session.add(LearningActivity(user_id=user.id, day=today - timedelta(days=i)))
    await gamification.award(db_session, user.id)
    await gamification.award(db_session, user.id)
    await db_session.commit()
    codes = set((await db_session.scalars(select(UserAchievement.achievement_code))).all())
    assert codes == {"first_lesson", "hundred_xp", "ten_lessons", "seven_day_streak"}
    for i in range(5):
        assert (
            await client.post(
                "/api/v1/vocabulary",
                headers=auth,
                json={"word": f"word{i}", "translation": "слово"},
            )
        ).status_code == 201
    assert await db_session.scalar(select(func.count()).select_from(UserAchievement)) == 5
    assert (await client.get("/api/v1/achievements/me", headers=auth)).status_code == 200


async def test_profile_update(client):
    auth = await headers(client)
    r = await client.patch(
        "/api/v1/users/me",
        headers=auth,
        json={
            "displayName": "New name",
            "englishLevel": "B2",
            "preferredLanguage": "Ukrainian",
            "xp": 999,
        },
    )
    assert r.status_code == 200
    assert r.json()["displayName"] == "New name"
    assert r.json()["englishLevel"] == "B2"
    assert r.json()["xp"] == 0
    for body in [{"displayName": " "}, {"englishLevel": "D1"}, {"preferredLanguage": None}]:
        assert (await client.patch("/api/v1/users/me", headers=auth, json=body)).status_code == 422
    assert (await client.patch("/api/v1/users/me", json={"displayName": "X"})).status_code == 401


async def test_password_reset_hash_single_use_and_sessions(client, db_session, monkeypatch):
    await headers(client)
    delivered = []

    async def capture(email, raw, settings):
        delivered.append((email, raw))

    monkeypatch.setattr(reset, "deliver", capture)
    known = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "learner@example.com"}
    )
    unknown = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "missing@example.com"}
    )
    assert known.json() == unknown.json()
    assert "token" not in known.text.lower()
    record = await db_session.scalar(select(PasswordReset))
    raw = delivered[0][1]
    assert record.token_hash == hash_refresh_token(raw) != raw
    payload = {"token": raw, "password": "new-strong-password"}
    assert (
        await client.post("/api/v1/auth/password-reset/confirm", json=payload)
    ).status_code == 204
    assert (
        await client.post("/api/v1/auth/password-reset/confirm", json=payload)
    ).status_code == 400
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "learner@example.com", "password": payload["password"]},
        )
    ).status_code == 200


async def test_password_reset_expiry_and_rate(client, db_session, monkeypatch):
    await headers(client)
    delivered = []

    async def capture(email, raw, settings):
        delivered.append(raw)

    monkeypatch.setattr(reset, "deliver", capture)
    settings = Settings(reset_rate_per_hour=2)
    app.dependency_overrides[get_settings] = lambda: settings
    for _ in range(2):
        assert (
            await client.post(
                "/api/v1/auth/password-reset/request", json={"email": "learner@example.com"}
            )
        ).status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/password-reset/request", json={"email": "learner@example.com"}
        )
    ).status_code == 429
    record = await db_session.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == hash_refresh_token(delivered[0]))
    )
    record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    with pytest.raises(Exception) as exc:
        await reset.confirm_reset(db_session, delivered[0], "another-password")
    assert exc.value.code == "INVALID_RESET_TOKEN"


async def test_validation_redacts_secrets_and_large_bodies(client):
    secret = "private-reset-token"
    response = await client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": secret, "password": "short"}
    )
    assert response.status_code == 422
    assert secret not in response.text
    assert '"input"' not in response.text
    response = await client.post("/api/v1/ai/chat", content=b"x" * 140000)
    assert response.status_code == 413


async def test_grading_records_streak_and_first_lesson(client, db_session):
    from app.db.seed import seed_catalog
    from tests.test_exercises import _complete_greetings

    auth = await headers(client)
    await seed_catalog(db_session)
    await definitions(db_session)
    token = auth["Authorization"].removeprefix("Bearer ")
    await _complete_greetings(client, token)
    await _complete_greetings(client, token)
    awards = (await client.get("/api/v1/achievements/me", headers=auth)).json()
    first = next(row for row in awards if row["code"] == "first_lesson")
    assert first["awardedAt"] is not None
    assert await db_session.scalar(select(func.count()).select_from(UserAchievement)) == 1
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    assert (await client.get("/api/v1/users/me", headers=auth)).json()["xp"] == 3
