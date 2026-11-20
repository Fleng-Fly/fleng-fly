"""Daily goals: settings on the profile, progress derived from real activity."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from httpx import AsyncClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.db.base import Base
from app.db.models import LearningActivity, LessonProgress, Profile, VocabularyReview
from app.modules.progress.service import daily_goals, local_day_window
from tests.test_learning_extensions import headers

DAILY = "/api/v1/progress/daily"
WORDS = "/api/v1/vocabulary"


async def _word(client: AsyncClient, auth: dict, word: str) -> str:
    response = await client.post(
        WORDS, headers=auth, json={"word": word, "translation": "t", "example": ""}
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _review(client: AsyncClient, auth: dict, item: str, remembered: bool = True) -> None:
    response = await client.post(
        f"{WORDS}/{item}/review", headers=auth, json={"remembered": remembered}
    )
    assert response.status_code == 200


async def test_requires_session(client: AsyncClient) -> None:
    assert (await client.get(DAILY)).status_code == 401


async def test_defaults_and_zero_progress(client: AsyncClient) -> None:
    auth = await headers(client)
    body = (await client.get(DAILY, headers=auth)).json()
    assert body["lessons"] == {"goal": 1, "done": 0}
    assert body["vocabulary"] == {"goal": 10, "done": 0}
    assert body["timezone"] == "UTC"
    me = (await client.get("/api/v1/users/me", headers=auth)).json()
    assert (me["dailyLessonsGoal"], me["dailyWordsGoal"], me["timezone"]) == (1, 10, None)


async def test_goals_sync_through_profile_and_validate(client: AsyncClient) -> None:
    auth = await headers(client)
    ok = await client.patch(
        "/api/v1/users/me",
        headers=auth,
        json={"dailyLessonsGoal": 3, "dailyWordsGoal": 20, "timezone": "Europe/Kyiv"},
    )
    assert ok.status_code == 200
    body = (await client.get(DAILY, headers=auth)).json()
    assert body["lessons"]["goal"] == 3 and body["vocabulary"]["goal"] == 20
    assert body["timezone"] == "Europe/Kyiv"
    for bad in (
        {"dailyLessonsGoal": 0},
        {"dailyLessonsGoal": 11},
        {"dailyWordsGoal": 101},
        {"dailyWordsGoal": "many"},
        {"timezone": "Mars/Base"},
        {"timezone": "../etc/passwd"},
        {"timezone": ""},
    ):
        assert (await client.patch("/api/v1/users/me", headers=auth, json=bad)).status_code == 422
    after = (await client.get(DAILY, headers=auth)).json()
    assert after["lessons"]["goal"] == 3  # rejected edits changed nothing


async def test_lesson_counts_once_even_if_repeated(client: AsyncClient, db_session) -> None:
    from app.db.seed import seed_catalog
    from tests.test_exercises import _complete_greetings

    auth = await headers(client)
    await seed_catalog(db_session)
    token = auth["Authorization"].removeprefix("Bearer ")
    await _complete_greetings(client, token)
    await _complete_greetings(client, token)
    assert (await client.get(DAILY, headers=auth)).json()["lessons"]["done"] == 1


async def test_words_count_distinct_remembered_reviews_only(client: AsyncClient) -> None:
    auth = await headers(client)
    other = await headers(client, "other@example.com")
    first = await _word(client, auth, "apple")
    second = await _word(client, auth, "pear")
    third = await _word(client, auth, "plum")
    stranger = await _word(client, other, "apple")
    for _ in range(3):
        await _review(client, auth, first)  # repeating one word counts once
    await _review(client, auth, second, remembered=False)  # not remembered: no credit
    await _review(client, other, stranger)
    # A saved but never reviewed word, and a manual "learned" toggle, are not activity.
    await client.patch(f"{WORDS}/{third}", headers=auth, json={"learned": True})
    body = (await client.get(DAILY, headers=auth)).json()
    assert body["vocabulary"]["done"] == 1
    await _review(client, auth, second)
    assert (await client.get(DAILY, headers=auth)).json()["vocabulary"]["done"] == 2


async def test_goal_progress_does_not_touch_streak_or_xp(client: AsyncClient, db_session) -> None:
    auth = await headers(client)
    item = await _word(client, auth, "apple")
    await _review(client, auth, item)
    days = await db_session.scalar(select(func.count()).select_from(LearningActivity))
    xp = (await client.get("/api/v1/users/me", headers=auth)).json()["xp"]
    await client.get(DAILY, headers=auth)
    await client.patch("/api/v1/users/me", headers=auth, json={"dailyWordsGoal": 5})
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == days
    assert (await client.get("/api/v1/users/me", headers=auth)).json()["xp"] == xp


async def test_day_follows_learner_timezone(client: AsyncClient, db_session: AsyncSession) -> None:
    auth = await headers(client)
    item = await _word(client, auth, "apple")
    await _review(client, auth, item)
    profile = await db_session.scalar(select(Profile))
    assert profile is not None
    # Place the review 30 minutes after Kyiv's local midnight, then 30 minutes before it.
    now = datetime.now(UTC)
    today_kyiv, start_kyiv, _ = local_day_window("Europe/Kyiv", now)
    review = await db_session.scalar(select(VocabularyReview))
    assert review is not None
    review.created_at = start_kyiv + timedelta(minutes=30)
    await db_session.commit()
    await client.patch("/api/v1/users/me", headers=auth, json={"timezone": "Europe/Kyiv"})
    await db_session.refresh(profile)
    inside = await daily_goals(db_session, profile.user_id, profile, now)
    assert inside.date == today_kyiv and inside.vocabulary.done == 1
    review.created_at = start_kyiv - timedelta(minutes=30)
    await db_session.commit()
    before = await daily_goals(db_session, profile.user_id, profile, now)
    assert before.vocabulary.done == 0


async def test_lesson_completion_window(db_session: AsyncSession, client: AsyncClient) -> None:
    from app.db.models import Course, Lesson
    from app.modules.progress.service import daily_goals

    await headers(client)
    profile = await db_session.scalar(select(Profile))
    assert profile is not None
    profile.timezone = "Europe/Kyiv"
    course = Course(slug="c", title="C", description="d", level="A1", is_published=True)
    lessons = [
        Lesson(
            course=course,
            slug=f"l{i}",
            title="L",
            summary="s",
            theory="t",
            position=i,
            estimated_minutes=5,
            is_published=True,
        )
        for i in range(3)
    ]
    db_session.add_all([course, *lessons])
    await db_session.flush()
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    _, start, end = local_day_window("Europe/Kyiv", now)
    for lesson, moment in zip(lessons, (start, end - timedelta(seconds=1), end), strict=True):
        db_session.add(
            LessonProgress(
                user_id=profile.user_id,
                lesson_id=lesson.id,
                status="completed",
                completed_at=moment,
            )
        )
    await db_session.commit()
    result = await daily_goals(db_session, profile.user_id, profile, now)
    assert result.lessons.done == 2  # [start, next start): the next-day midnight is excluded


@pytest.mark.parametrize(
    "zone,when,hours",
    [
        ("Europe/Kyiv", datetime(2026, 3, 29, 12, tzinfo=UTC), 23),  # spring forward
        ("Europe/Kyiv", datetime(2026, 10, 25, 12, tzinfo=UTC), 25),  # fall back
        ("Europe/Kyiv", datetime(2026, 6, 15, 12, tzinfo=UTC), 24),
        ("UTC", datetime(2026, 6, 15, 23, 59, tzinfo=UTC), 24),
    ],
)
def test_local_day_window_handles_dst(zone, when, hours) -> None:
    day, start, end = local_day_window(zone, when)
    assert (end - start) == timedelta(hours=hours)
    assert start <= when < end
    assert day == when.astimezone(ZoneInfo(zone)).date()


def test_local_day_window_midnight_boundary() -> None:
    before = datetime(2026, 6, 15, 20, 59, 59, tzinfo=UTC)  # 23:59:59 in Kyiv (UTC+3)
    after = datetime(2026, 6, 15, 21, 0, tzinfo=UTC)  # 00:00 next day in Kyiv
    assert local_day_window("Europe/Kyiv", before)[0].day == 15
    assert local_day_window("Europe/Kyiv", after)[0].day == 16
    assert local_day_window("Europe/Kyiv", before)[2] == after


def test_migration_adds_defaults_and_is_reversible(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(f"sqlite:///{tmp_path / 'goals.db'}")
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "20261118_1400")
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, created_at, updated_at) VALUES "
                "('u1', 'a@example.com', 'x', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO profiles (id, user_id, display_name, created_at, updated_at) VALUES "
                "('p1', 'u1', 'A', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.commit()
        command.upgrade(config, "20261120_1200")
        row = connection.execute(
            text("SELECT daily_lessons_goal, daily_words_goal, timezone FROM profiles")
        ).one()
        assert tuple(row) == (1, 10, None)
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        connection.commit()
        command.downgrade(config, "20261118_1400")
        assert connection.scalar(text("SELECT count(*) FROM profiles")) == 1
        columns = {r[1] for r in connection.execute(text("PRAGMA table_info(profiles)"))}
        assert "daily_words_goal" not in columns and "timezone" not in columns
        connection.commit()
        command.upgrade(config, "head")
    engine.dispose()
