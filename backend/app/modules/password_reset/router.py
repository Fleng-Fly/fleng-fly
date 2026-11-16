import hashlib

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.limits import consume
from app.db.session import get_db
from app.modules.password_reset import service
from app.modules.password_reset.schemas import ResetConfirm, ResetRequest, ResetResponse

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])


async def throttle(db: AsyncSession, request: Request, settings: Settings, email: str = ""):
    ip = request.client.host if request.client else "unknown"
    for scope, value in (("ip", ip), ("email", email.strip().lower())):
        if value:
            digest = hashlib.sha256(value.encode()).hexdigest()
            await consume(db, f"reset:{scope}:{digest}", settings.reset_rate_per_hour, 3600)
    await db.commit()


@router.post("/request", response_model=ResetResponse)
async def request_reset(
    payload: ResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    await throttle(db, request, settings, str(payload.email))
    await service.request_reset(db, str(payload.email), settings)
    return ResetResponse()


@router.post("/confirm", status_code=204)
async def confirm_reset(
    payload: ResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    await throttle(db, request, settings)
    await service.confirm_reset(db, payload.token, payload.password)
