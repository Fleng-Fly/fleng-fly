"""Tokens never enter API responses or application logs. SMTP is injectable in tests."""

import asyncio
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import PasswordReset, RefreshToken, User
from app.modules.auth.security import hash_password, hash_refresh_token


async def deliver(email: str, raw: str, settings: Settings) -> None:
    if settings.reset_delivery == "disabled":
        return
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = email
    message["Subject"] = "Reset your Fleng password"
    message.set_content(
        "Reset your password: " + settings.reset_url + "?" + urlencode({"token": raw})
    )

    def send() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)

    await asyncio.to_thread(send)


async def request_reset(db: AsyncSession, email: str, settings: Settings) -> None:
    user = await db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        return
    raw = secrets.token_urlsafe(48)
    record = PasswordReset(
        user_id=user.id,
        token_hash=hash_refresh_token(raw),
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.reset_token_minutes),
    )
    db.add(record)
    await db.commit()
    try:
        await deliver(user.email, raw, settings)
    except (OSError, smtplib.SMTPException):
        # Preserve enumeration-safe responses. Failed delivery invalidates its token.
        record.used_at = datetime.now(UTC)
        await db.commit()


async def confirm_reset(db: AsyncSession, raw: str, password: str) -> None:
    now = datetime.now(UTC)
    # Lock identity first to serialize all reset tokens belonging to an account.
    user_id = await db.scalar(
        select(PasswordReset.user_id).where(PasswordReset.token_hash == hash_refresh_token(raw))
    )
    if user_id is None:
        raise ApiError(400, "INVALID_RESET_TOKEN", "Invalid or expired reset token")
    user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
    claimed = await db.execute(
        update(PasswordReset)
        .where(
            PasswordReset.token_hash == hash_refresh_token(raw),
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > now,
        )
        .values(used_at=now)
        .returning(PasswordReset.id)
        .execution_options(synchronize_session="fetch")
    )
    if claimed.scalar_one_or_none() is None or user is None:
        raise ApiError(400, "INVALID_RESET_TOKEN", "Invalid or expired reset token")
    user.password_hash = await asyncio.to_thread(hash_password, password)
    await db.execute(
        update(PasswordReset)
        .where(PasswordReset.user_id == user_id, PasswordReset.used_at.is_(None))
        .values(used_at=now)
    )
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await db.commit()
