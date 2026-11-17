"""Password-authorized, one-use email changes; secrets never enter URLs except opaque tokens."""

import asyncio
import hashlib
import hmac
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.limits import consume
from app.db.models import EmailChange, User
from app.db.session import get_db
from app.modules.auth.security import hash_refresh_token, password_work, verify_password
from app.modules.auth.service import invalidate_password_sessions
from app.modules.gamification.service import lock_learner
from app.modules.users.schemas import EmailChangeConfirm, EmailChangeRequest

router = APIRouter(prefix="/users", tags=["users"])


def authorization(user: User, settings: Settings) -> str:
    # Binding to the verified credentials and old address invalidates stale operations.
    return hmac.new(
        settings.jwt_access_secret.encode(),
        f"{user.id}:{user.email}:{user.password_hash}".encode(),
        hashlib.sha256,
    ).hexdigest()


async def deliver(email: str, raw: str, settings: Settings) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = email
    message["Subject"] = "Confirm your Fleng email change"
    message.set_content(
        "Confirm within 30 minutes: " + settings.email_change_url + "#email-change=" + raw
    )

    def send() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)

    await asyncio.to_thread(send)


@router.post("/me/email-change/request", status_code=204)
async def request_change(
    payload: EmailChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    if settings.reset_delivery != "smtp":
        raise ApiError(503, "EMAIL_DELIVERY_DISABLED", "Email delivery is unavailable")
    await consume(db, f"email-change:{user.id}", 5, 3600)
    await db.commit()
    await lock_learner(db, user.id)
    await db.refresh(user, attribute_names=["email", "password_hash"])
    if not await password_work(verify_password, user.password_hash, payload.current_password):
        raise ApiError(400, "INVALID_PASSWORD", "Current password is incorrect")
    email = str(payload.email).strip().lower()
    if email == user.email:
        raise ApiError(422, "VALIDATION_FAILED", "Choose a different email")
    if await db.scalar(select(User.id).where(User.email == email)):
        raise ApiError(409, "EMAIL_TAKEN", "Email is unavailable")
    await db.execute(
        update(EmailChange)
        .where(EmailChange.user_id == user.id, EmailChange.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )
    raw = secrets.token_urlsafe(48)
    record = EmailChange(
        user_id=user.id,
        new_email=email,
        token_hash=hash_refresh_token(raw),
        authorization_hash=authorization(user, settings),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db.add(record)
    await db.commit()
    try:
        await deliver(email, raw, settings)
    except (OSError, smtplib.SMTPException):
        record.used_at = datetime.now(UTC)
        await db.commit()
        raise ApiError(503, "EMAIL_DELIVERY_FAILED", "Email delivery failed") from None
    return Response(status_code=204)


@router.post("/me/email-change/confirm", status_code=204)
async def confirm_change(
    payload: EmailChangeConfirm,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    token_hash = hash_refresh_token(payload.token)
    user_id: UUID | None = await db.scalar(
        select(EmailChange.user_id).where(EmailChange.token_hash == token_hash)
    )
    invalid = ApiError(400, "INVALID_EMAIL_CHANGE_TOKEN", "Invalid or expired email change")
    if user_id is None:
        raise invalid
    await lock_learner(db, user_id)
    user = await db.scalar(
        select(User).where(User.id == user_id).execution_options(populate_existing=True)
    )
    record = await db.scalar(
        select(EmailChange)
        .where(
            EmailChange.token_hash == token_hash,
            EmailChange.used_at.is_(None),
            EmailChange.expires_at > datetime.now(UTC),
        )
        .execution_options(populate_existing=True)
    )
    if (
        user is None
        or record is None
        or not hmac.compare_digest(record.authorization_hash, authorization(user, settings))
    ):
        raise invalid
    user.email = record.new_email
    record.used_at = datetime.now(UTC)
    try:
        await invalidate_password_sessions(db, user_id)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ApiError(409, "EMAIL_TAKEN", "Email is unavailable") from None
    return Response(status_code=204)
