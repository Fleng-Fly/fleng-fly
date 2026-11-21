"""Measured reading time (heartbeat crediting) and its statistics.

This is *measured* active reading time, kept apart from `progress.study_minutes` (a lesson
estimate) and from XP (reading time never awards XP).

Crediting uses the server clock only. Each learner has one cursor, `credited_until`, shared by
all tabs, devices and articles; a heartbeat credits the time between the cursor and now, so one
stretch of time is credited at most once, to the article of the heartbeat that is accepted:

    gap = now - cursor
    gap < MIN_GAP_SECONDS            -> nothing, cursor stays (too frequent / replayed)
    no cursor or gap > RESET_GAP     -> nothing, cursor = now (first beat after a pause)
    otherwise                        -> min(gap, CREDIT_CAP_SECONDS), cursor = now

Credit is then limited by a per-learner daily cap and a per-article daily cap. Seconds are
stored per local calendar day (the learner's time zone when credited) and are never
recomputed, so a later time-zone change does not rewrite history. Reaching
`ACTIVE_DAY_SECONDS` of reading in a day records learning activity (streak) once, through the
existing gamification service.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.models import (
    Profile,
    ReadingArticle,
    ReadingStudyDay,
    ReadingStudyTotal,
)
from app.modules.gamification.service import lock_learner, record_activity
from app.modules.progress.service import local_day_window
from app.modules.reading.content import available_clauses

MIN_GAP_SECONDS = 5
CREDIT_CAP_SECONDS = 20
RESET_GAP_SECONDS = 45
BEAT_INTERVAL_SECONDS = 15  # what clients are told to use
DAILY_USER_CAP_SECONDS = 4 * 3600
ACTIVE_DAY_SECONDS = 60


def article_daily_cap(reading_minutes: int) -> int:
    """Most seconds one article may earn per learner and local day."""
    return max(30 * 60, 3 * reading_minutes * 60)


@dataclass(frozen=True)
class HeartbeatResult:
    credited_seconds: int
    article_seconds: int  # all days
    today_seconds: int  # this learner, all articles, local day
    total_seconds: int
    capped: bool


@dataclass(frozen=True)
class StudySummary:
    total_seconds: int
    today_seconds: int
    days: list[tuple[date, int]]  # oldest first, zero days included
    by_article: list[tuple[ReadingArticle, int]]  # most time first


def _now() -> datetime:
    """The server clock (a single seam so tests can move time)."""
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes; they are always UTC here.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _zone(profile: Profile | None) -> str:
    return (profile.timezone if profile else None) or get_settings().learning_timezone


async def _profile(db: AsyncSession, user_id: UUID) -> Profile | None:
    return await db.scalar(select(Profile).where(Profile.user_id == user_id))


async def heartbeat(
    db: AsyncSession, user_id: UUID, article_id: UUID, *, now: datetime | None = None
) -> HeartbeatResult:
    """Accept one client heartbeat for an available article and credit reading time."""
    now = now or _now()
    minutes = await db.scalar(
        select(ReadingArticle.reading_minutes).where(
            ReadingArticle.id == article_id, *available_clauses()
        )
    )
    if minutes is None:
        raise ApiError(404, "NOT_FOUND", "Article not found")

    await lock_learner(db, user_id)
    totals = await db.get(ReadingStudyTotal, user_id)
    if totals is None:
        totals = ReadingStudyTotal(user_id=user_id, total_seconds=0)
        db.add(totals)
        await db.flush()
    today, _start, _end = local_day_window(_zone(await _profile(db, user_id)), now)

    cursor = _aware(totals.credited_until)
    credit = 0
    move_cursor = True
    if cursor is not None:
        gap = (now - cursor).total_seconds()
        if gap < MIN_GAP_SECONDS:
            move_cursor = False
        elif gap <= RESET_GAP_SECONDS:
            credit = min(int(gap), CREDIT_CAP_SECONDS)
    if move_cursor:
        totals.credited_until = now

    user_today = int(
        await db.scalar(
            select(func.coalesce(func.sum(ReadingStudyDay.seconds), 0)).where(
                ReadingStudyDay.user_id == user_id, ReadingStudyDay.day == today
            )
        )
        or 0
    )
    day_row = await db.scalar(
        select(ReadingStudyDay).where(
            ReadingStudyDay.user_id == user_id,
            ReadingStudyDay.article_id == article_id,
            ReadingStudyDay.day == today,
        )
    )
    article_today = day_row.seconds if day_row else 0
    room = min(DAILY_USER_CAP_SECONDS - user_today, article_daily_cap(minutes) - article_today)
    credited = max(0, min(credit, room))
    capped = room <= 0 or credited < credit

    if credited:
        if day_row is None:
            day_row = ReadingStudyDay(user_id=user_id, article_id=article_id, day=today, seconds=0)
            db.add(day_row)
        day_row.seconds += credited
        totals.total_seconds += credited
        await db.flush()
        if user_today < ACTIVE_DAY_SECONDS <= user_today + credited:
            await record_activity(db, user_id)

    article_total = int(
        await db.scalar(
            select(func.coalesce(func.sum(ReadingStudyDay.seconds), 0)).where(
                ReadingStudyDay.user_id == user_id, ReadingStudyDay.article_id == article_id
            )
        )
        or 0
    )
    result = HeartbeatResult(
        credited_seconds=credited,
        article_seconds=article_total,
        today_seconds=user_today + credited,
        total_seconds=totals.total_seconds,
        capped=capped,
    )
    await db.commit()
    return result


async def seconds_by_article(
    db: AsyncSession, user_id: UUID, article_ids: list[UUID]
) -> dict[UUID, int]:
    """Measured seconds per article (all days) for the given articles."""
    if not article_ids:
        return {}
    rows = await db.execute(
        select(ReadingStudyDay.article_id, func.sum(ReadingStudyDay.seconds))
        .where(ReadingStudyDay.user_id == user_id, ReadingStudyDay.article_id.in_(article_ids))
        .group_by(ReadingStudyDay.article_id)
    )
    return {article_id: int(total) for article_id, total in rows.all()}


async def totals_summary(
    db: AsyncSession, user_id: UUID, *, now: datetime | None = None
) -> tuple[int, int]:
    """`(total_seconds, today_seconds)` for the learner's local day."""
    now = now or _now()
    today, _start, _end = local_day_window(_zone(await _profile(db, user_id)), now)
    total = await db.scalar(
        select(ReadingStudyTotal.total_seconds).where(ReadingStudyTotal.user_id == user_id)
    )
    today_seconds = await db.scalar(
        select(func.coalesce(func.sum(ReadingStudyDay.seconds), 0)).where(
            ReadingStudyDay.user_id == user_id, ReadingStudyDay.day == today
        )
    )
    return int(total or 0), int(today_seconds or 0)


async def summary(
    db: AsyncSession, user_id: UUID, *, days: int = 30, now: datetime | None = None
) -> StudySummary:
    """Totals, one entry per local day for the last `days` days, and time per article."""
    if not 1 <= days <= 365:
        raise ApiError(422, "VALIDATION_FAILED", "days must be between 1 and 365")
    now = now or _now()
    today, _start, _end = local_day_window(_zone(await _profile(db, user_id)), now)
    first = today - timedelta(days=days - 1)
    per_day = dict(
        (
            await db.execute(
                select(ReadingStudyDay.day, func.sum(ReadingStudyDay.seconds))
                .where(
                    ReadingStudyDay.user_id == user_id,
                    ReadingStudyDay.day >= first,
                    ReadingStudyDay.day <= today,
                )
                .group_by(ReadingStudyDay.day)
            )
        ).all()
    )
    series = [
        (first + timedelta(days=offset), int(per_day.get(first + timedelta(days=offset), 0)))
        for offset in range(days)
    ]
    by_article_rows = (
        await db.execute(
            select(ReadingArticle, func.sum(ReadingStudyDay.seconds).label("seconds"))
            .join(ReadingStudyDay, ReadingStudyDay.article_id == ReadingArticle.id)
            .where(ReadingStudyDay.user_id == user_id, ReadingStudyDay.day >= first)
            .group_by(ReadingArticle.id)
            .order_by(func.sum(ReadingStudyDay.seconds).desc(), ReadingArticle.slug)
            .limit(20)
        )
    ).all()
    total, today_seconds = await totals_summary(db, user_id, now=now)
    return StudySummary(
        total_seconds=total,
        today_seconds=today_seconds,
        days=series,
        by_article=[(article, int(seconds)) for article, seconds in by_article_rows],
    )
