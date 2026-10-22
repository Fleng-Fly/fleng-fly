"""Database-backed windows shared by workers; no raw identifiers in keys."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import RequestLimit


async def consume(db: AsyncSession, key: str, limit: int, seconds: int) -> None:
    now = datetime.now(UTC)
    window = datetime.fromtimestamp(int(now.timestamp()) // seconds * seconds, UTC)
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    await db.execute(
        insert(RequestLimit).values(key=key, window=window, count=0).on_conflict_do_nothing()
    )
    result = await db.execute(
        update(RequestLimit)
        .where(RequestLimit.key == key, RequestLimit.window == window, RequestLimit.count < limit)
        .values(count=RequestLimit.count + 1)
        .returning(RequestLimit.count)
    )
    if result.scalar_one_or_none() is None:
        raise ApiError(
            429, "RATE_LIMITED", "Request limit reached", headers={"Retry-After": str(seconds)}
        )
    await db.execute(
        delete(RequestLimit)
        .where(
            (RequestLimit.window < now - timedelta(days=2)) & (RequestLimit.key != "ai:capacity")
        )
        .execution_options(synchronize_session="fetch")
    )


async def lock_ai_capacity(db: AsyncSession) -> None:
    """One lightweight row serializes global reservation checks across workers."""
    window = datetime(1970, 1, 1, tzinfo=UTC)
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    await db.execute(
        insert(RequestLimit)
        .values(key="ai:capacity", window=window, count=0)
        .on_conflict_do_nothing()
    )
    await db.execute(
        select(RequestLimit)
        .where(RequestLimit.key == "ai:capacity", RequestLimit.window == window)
        .with_for_update()
    )
