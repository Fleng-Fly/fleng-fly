"""Authentication business logic: registration, login and refresh sessions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import Profile, Progress, RefreshToken, User
from app.modules.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_password_dummy,
)
from app.modules.users.service import get_user_with_profile


def _invalid_refresh() -> ApiError:
    return ApiError(
        401,
        "INVALID_REFRESH_TOKEN",
        "Invalid or expired session",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _refresh_reused() -> ApiError:
    return ApiError(
        401,
        "REFRESH_TOKEN_REUSED",
        "Session reuse detected; please sign in again",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; normalise before comparing."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def register_user(
    db: AsyncSession, *, email: str, password: str, display_name: str
) -> User:
    normalized_email = _normalize_email(email)
    existing = await db.scalar(select(User.id).where(User.email == normalized_email))
    if existing is not None:
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")

    user = User(email=normalized_email, password_hash=hash_password(password))
    user.profile = Profile(display_name=display_name.strip())
    user.progress = Progress()
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # Lost a race on the unique email constraint.
        await db.rollback()
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists") from None

    loaded = await get_user_with_profile(db, user.id)
    if loaded is None:  # pragma: no cover - defensive
        raise ApiError(500, "INTERNAL_ERROR", "Account could not be loaded")
    return loaded


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User | None:
    normalized_email = _normalize_email(email)
    user = await db.scalar(
        select(User).options(selectinload(User.profile)).where(User.email == normalized_email)
    )
    if user is None:
        # Keep timing close to the known-user path to avoid enumeration.
        verify_password_dummy(password)
        return None
    if not verify_password(user.password_hash, password):
        return None
    return user


async def create_session(
    db: AsyncSession, *, user: User, settings: Settings
) -> tuple[str, str]:
    """Create a refresh-token row and return `(access_token, raw_refresh_token)`."""
    raw_token, token_hash = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.commit()
    return create_access_token(user.id, settings), raw_token


async def rotate_session(
    db: AsyncSession, *, raw_token: str, settings: Settings
) -> tuple[User, str, str]:
    """Validate and rotate a refresh token. Returns `(user, access, new_refresh)`."""
    token_hash = hash_refresh_token(raw_token)
    record = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
    if record is None:
        raise _invalid_refresh()

    if record.revoked_at is not None:
        # A revoked token was replayed: assume theft and revoke the whole set.
        await _revoke_all_for_user(db, record.user_id)
        await db.commit()
        raise _refresh_reused()

    if _as_utc(record.expires_at) <= datetime.now(UTC):
        raise _invalid_refresh()

    record.revoked_at = datetime.now(UTC)
    new_raw, new_hash = generate_refresh_token()
    new_record = RefreshToken(
        user_id=record.user_id,
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_record)
    await db.flush()
    record.replaced_by_id = new_record.id
    await db.commit()

    user = await get_user_with_profile(db, record.user_id)
    if user is None:  # pragma: no cover - defensive
        raise _invalid_refresh()
    access_token = create_access_token(user.id, settings)
    return user, access_token, new_raw


async def revoke_session(db: AsyncSession, *, raw_token: str) -> None:
    """Revoke the presented refresh token. Idempotent: unknown tokens are ignored."""
    token_hash = hash_refresh_token(raw_token)
    record = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        await db.commit()


async def _revoke_all_for_user(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
