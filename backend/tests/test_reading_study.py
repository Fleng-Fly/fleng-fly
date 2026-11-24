"""Reading study time: heartbeat crediting, caps, shared cursor, days, streak and statistics."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.errors import ApiError
from app.db.models import (
    LearningActivity,
    Profile,
    ReadingStudyDay,
    ReadingStudyTotal,
)
from app.modules.reading import content, study
from tests.test_reading import make_article, make_category, make_user, xp

T0 = datetime(2026, 11, 22, 10, 0, 0, tzinfo=UTC)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


async def setup(db, *, slug="story", minutes=1):
    user = await make_user(db)
    category = await make_category(db, f"c-{slug}-{uuid.uuid4().hex[:4]}")
    article = await make_article(db, category, slug + uuid.uuid4().hex[:4], reading_minutes=minutes)
    return user, article


async def beat(db, user, article, seconds):
    return await study.heartbeat(db, user.id, article.id, now=at(seconds))


async def test_first_heartbeat_credits_nothing_then_regular_beats_credit_elapsed_time(db_session):
    user, article = await setup(db_session)
    first = await beat(db_session, user, article, 0)
    assert (first.credited_seconds, first.total_seconds, first.capped) == (0, 0, False)
    second = await beat(db_session, user, article, 15)
    assert (second.credited_seconds, second.article_seconds, second.today_seconds) == (15, 15, 15)
    third = await beat(db_session, user, article, 31)
    assert third.credited_seconds == 16 and third.total_seconds == 31


async def test_credit_is_capped_at_20_seconds_per_heartbeat(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    assert (await beat(db_session, user, article, 40)).credited_seconds == 20
    assert (await beat(db_session, user, article, 85)).credited_seconds == 20  # gap 45 = limit


async def test_too_frequent_heartbeats_credit_nothing_and_do_not_move_the_cursor(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    for s in (1, 2, 3, 4):
        assert (await beat(db_session, user, article, s)).credited_seconds == 0
    # the cursor never moved, so the next accepted beat credits the whole gap since 0
    assert (await beat(db_session, user, article, 12)).credited_seconds == 12


async def test_replayed_and_late_requests_cannot_double_count(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    await beat(db_session, user, article, 15)
    replay = await beat(db_session, user, article, 15)  # the same instant again
    late = await beat(db_session, user, article, 10)  # arrives with an older clock
    assert replay.credited_seconds == 0 and late.credited_seconds == 0
    assert replay.total_seconds == 15 and late.total_seconds == 15


async def test_a_long_pause_is_not_credited_and_restarts_the_cursor(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    await beat(db_session, user, article, 15)
    back = await beat(db_session, user, article, 15 + 600)  # tab slept / offline for 10 min
    assert (back.credited_seconds, back.total_seconds) == (0, 15)
    assert (await beat(db_session, user, article, 15 + 615)).credited_seconds == 15


async def test_two_tabs_share_one_cursor_so_time_is_credited_once(db_session):
    user, article = await setup(db_session)
    other_article = (await setup(db_session, slug="other"))[1]
    await beat(db_session, user, article, 0)
    # two tabs alternate every 8 seconds: 6 beats in 48 s
    for s in (8, 16, 24, 32, 40, 48):
        await beat(db_session, user, article if s % 16 else other_article, s)
    total = (await beat(db_session, user, article, 56)).total_seconds
    assert total <= 56  # never more than the wall-clock time
    assert total == 56  # and nothing is lost either: each interval goes to one article


async def test_each_interval_goes_to_the_article_of_the_accepted_heartbeat(db_session):
    user, first = await setup(db_session, slug="one")
    second = (await setup(db_session, slug="two"))[1]
    await beat(db_session, user, first, 0)
    await beat(db_session, user, first, 15)
    await beat(db_session, user, second, 30)
    seconds = await study.seconds_by_article(db_session, user.id, [first.id, second.id])
    assert seconds == {first.id: 15, second.id: 15}


async def test_article_daily_cap_is_max_30_minutes_or_3x_reading_time(db_session):
    assert study.article_daily_cap(1) == 1800
    assert study.article_daily_cap(10) == 1800
    assert study.article_daily_cap(20) == 3600
    user, article = await setup(db_session, minutes=1)  # cap 1800 s
    now = 0
    await beat(db_session, user, article, now)
    last = None
    for _ in range(130):
        now += 15
        last = await beat(db_session, user, article, now)
    assert last.article_seconds == 1800 and last.capped is True and last.credited_seconds == 0
    assert last.total_seconds == 1800


async def test_user_daily_cap_is_four_hours_across_articles(db_session):
    user, a = await setup(db_session, slug="a", minutes=120)
    b = (await setup(db_session, slug="b", minutes=120))[1]
    # Pre-fill 3h59m50s on the learner's local day, then ask for more.
    today = at(0).date()
    db_session.add(ReadingStudyDay(user_id=user.id, article_id=a.id, day=today, seconds=14390))
    await db_session.commit()
    await beat(db_session, user, b, 0)
    result = await beat(db_session, user, b, 15)
    assert result.credited_seconds == 10 and result.capped is True
    assert result.today_seconds == study.DAILY_USER_CAP_SECONDS
    again = await beat(db_session, user, b, 30)
    assert again.credited_seconds == 0 and again.capped is True


async def test_unavailable_article_is_404_and_nothing_is_stored(db_session):
    user, article = await setup(db_session)
    await content.set_status(db_session, article, "archived")
    with pytest.raises(ApiError) as error:
        await beat(db_session, user, article, 0)
    assert error.value.status_code == 404
    with pytest.raises(ApiError):
        await study.heartbeat(db_session, user.id, uuid.uuid4(), now=at(0))
    assert await db_session.scalar(select(func.count()).select_from(ReadingStudyTotal)) == 0


async def test_streak_activity_is_recorded_once_after_60_seconds_and_no_xp(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    for s in (15, 30, 45):
        await beat(db_session, user, article, s)
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 0
    await beat(db_session, user, article, 60)  # 60 seconds credited
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    for s in (75, 90, 105):
        await beat(db_session, user, article, s)
    assert await db_session.scalar(select(func.count()).select_from(LearningActivity)) == 1
    assert await xp(db_session, user) == 0


async def test_seconds_are_filed_under_the_learners_local_day_and_never_rewritten(db_session):
    user, article = await setup(db_session)
    user_id = user.id
    profile = await db_session.scalar(select(Profile).where(Profile.user_id == user_id))
    profile.timezone = "Pacific/Kiritimati"  # UTC+14: 10:00 UTC is already the next day
    await db_session.commit()
    await beat(db_session, user, article, 0)
    await beat(db_session, user, article, 15)
    days = (await db_session.scalars(select(ReadingStudyDay.day))).all()
    assert days == [datetime(2026, 11, 23).date()]

    profile.timezone = "Pacific/Pago_Pago"  # UTC-11: the same instant is the previous day
    await db_session.commit()
    await beat(db_session, user, article, 30)
    rows = (await db_session.scalars(select(ReadingStudyDay).order_by(ReadingStudyDay.day))).all()
    assert [(r.day.isoformat(), r.seconds) for r in rows] == [
        ("2026-11-21", 15),
        ("2026-11-23", 15),
    ]  # the first 15 s stay on the day they were credited


async def test_summary_has_zero_filled_days_totals_and_per_article_time(db_session):
    user, article = await setup(db_session, slug="alpha")
    await beat(db_session, user, article, 0)
    await beat(db_session, user, article, 15)
    await beat(db_session, user, article, 30)
    # a beat on the next day
    await study.heartbeat(db_session, user.id, article.id, now=at(86400))
    await study.heartbeat(db_session, user.id, article.id, now=at(86400 + 15))
    result = await study.summary(db_session, user.id, days=3, now=at(86400 + 15))
    assert [s for _d, s in result.days] == [0, 30, 15]
    assert result.total_seconds == 45 and result.today_seconds == 15
    assert [(a.slug.startswith("alpha"), s) for a, s in result.by_article] == [(True, 45)]
    assert await study.totals_summary(db_session, user.id, now=at(86400 + 15)) == (45, 15)
    for bad in (0, 366):
        with pytest.raises(ApiError):
            await study.summary(db_session, user.id, days=bad)


async def test_stats_are_private_per_learner(db_session):
    a, article = await setup(db_session, slug="shared")
    b = await make_user(db_session, "b")
    await beat(db_session, a, article, 0)
    await beat(db_session, a, article, 15)
    assert await study.totals_summary(db_session, b.id, now=at(15)) == (0, 0)
    assert (await study.summary(db_session, b.id, now=at(15))).by_article == []


async def test_study_time_never_touches_progress_study_minutes_or_xp(db_session):
    from app.db.models import Progress

    user, article = await setup(db_session)
    for s in (0, 15, 30, 45, 60):
        await beat(db_session, user, article, s)
    progress = await db_session.scalar(select(Progress).where(Progress.user_id == user.id))
    assert progress.study_minutes == 0
    assert await xp(db_session, user) == 0


async def _set_zone(db, user, zone):
    profile = await db.scalar(select(Profile).where(Profile.user_id == user.id))
    profile.timezone = zone
    await db.commit()


async def _days(db):
    rows = (await db.scalars(select(ReadingStudyDay).order_by(ReadingStudyDay.day))).all()
    return [(r.day.isoformat(), r.seconds) for r in rows]


async def test_gap_boundaries_are_exact_at_5_and_45_seconds(db_session):
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    assert (await beat(db_session, user, article, 4.9)).credited_seconds == 0
    assert (await beat(db_session, user, article, 5)).credited_seconds == 5  # gap 5 credited
    assert (await beat(db_session, user, article, 50)).credited_seconds == 20  # gap 45 credited
    assert (await beat(db_session, user, article, 95.5)).credited_seconds == 0  # gap > 45: reset
    assert (await beat(db_session, user, article, 110.5)).credited_seconds == 15  # cursor reset


async def test_utc_minus_12_and_utc_plus_14_local_days(db_session):
    user, article = await setup(db_session)
    await _set_zone(db_session, user, "Etc/GMT+12")  # UTC-12: 10:00 UTC is 22:00 the day before
    await beat(db_session, user, article, 0)
    await beat(db_session, user, article, 15)
    await _set_zone(db_session, user, "Pacific/Kiritimati")  # UTC+14
    await beat(db_session, user, article, 30)
    assert await _days(db_session) == [("2026-11-21", 15), ("2026-11-23", 15)]


async def test_local_midnight_splits_credit_by_accepted_heartbeat_time(db_session):
    user, article = await setup(db_session)
    await _set_zone(db_session, user, "Europe/Kyiv")  # UTC+2 in November
    midnight = datetime(2026, 11, 21, 22, 0, tzinfo=UTC)  # 00:00 on the 22nd, local
    await study.heartbeat(db_session, user.id, article.id, now=midnight - timedelta(seconds=30))
    await study.heartbeat(db_session, user.id, article.id, now=midnight - timedelta(seconds=10))
    # the interval ending after midnight belongs to the new local day
    await study.heartbeat(db_session, user.id, article.id, now=midnight + timedelta(seconds=10))
    assert await _days(db_session) == [("2026-11-21", 20), ("2026-11-22", 20)]


async def test_dst_transitions_use_the_local_calendar_day(db_session):
    user, article = await setup(db_session)
    await _set_zone(db_session, user, "America/New_York")
    # spring forward 2026-03-08 02:00 EST -> 03:00 EDT; 04:30 UTC is still 23:30 EST on the 7th
    before = datetime(2026, 3, 8, 4, 59, 50, tzinfo=UTC)
    after = datetime(2026, 3, 8, 5, 0, 10, tzinfo=UTC)  # 00:00:10 EST on the 8th
    await study.heartbeat(db_session, user.id, article.id, now=before - timedelta(seconds=15))
    await study.heartbeat(db_session, user.id, article.id, now=before)
    await study.heartbeat(db_session, user.id, article.id, now=after)
    # fall back 2026-11-01: 04:00 UTC is 00:00 EDT, 05:00 UTC is 00:00 EST (still the 1st)
    t = datetime(2026, 11, 1, 6, 0, 0, tzinfo=UTC)  # 01:00 EST, the 1st
    await study.heartbeat(db_session, user.id, article.id, now=t)
    await study.heartbeat(db_session, user.id, article.id, now=t + timedelta(seconds=15))
    days = await _days(db_session)
    assert days == [("2026-03-07", 15), ("2026-03-08", 20), ("2026-11-01", 15)]


async def test_concurrent_heartbeats_credit_an_interval_once(db_session):
    import asyncio
    import os

    from sqlalchemy.ext.asyncio import async_sessionmaker

    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip(
            "true concurrency needs PostgreSQL (TEST_DATABASE_URL); SQLite shares one connection"
        )
    user, article = await setup(db_session)
    await beat(db_session, user, article, 0)
    factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    async def one():
        async with factory() as session:
            return await study.heartbeat(session, user.id, article.id, now=at(15))

    results = await asyncio.gather(*(one() for _ in range(5)))
    assert sorted(r.credited_seconds for r in results) == [0, 0, 0, 0, 15]
