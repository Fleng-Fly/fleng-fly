import asyncio

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.health.schemas import HealthResponse
from app.modules.health.service import get_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    return await get_health(db)


@router.get("/ready", response_model=HealthResponse)
async def readiness(response: Response, db: AsyncSession = Depends(get_db)) -> HealthResponse:
    try:
        result = await asyncio.wait_for(get_health(db), timeout=5)
    except TimeoutError:
        from datetime import UTC, datetime

        result = HealthResponse(timestamp=datetime.now(UTC), database="down")
    if result.database == "down":
        response.status_code = 503
    return result
