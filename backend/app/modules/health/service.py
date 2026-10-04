from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.health.schemas import HealthResponse


async def get_health(db: AsyncSession) -> HealthResponse:
    """Health never fails when the API is up: the database is reported as down."""
    database: Literal["up", "down"] = "up"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database = "down"
    return HealthResponse(timestamp=datetime.now(UTC), database=database)
