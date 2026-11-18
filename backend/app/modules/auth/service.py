"""Authentication business logic: registration, login and refresh sessions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import OAuthIdentity, PasswordReset, Profile, Progress, RefreshToken, User
from app.modules.auth.google import GoogleProfile, random_password
from app.modules.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    password_work,
    verify_password,
    verify_password_dummy,
)
from app.modules.gamification.service import lock_learner
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


async def register_user(db: AsyncSession, *, email: str, password: str, display_name: str) -> User:
    normalized_email = _normalize_email(email)
    existing = await db.scalar(select(User.id).where(User.email == normalized_email))
    if existing is not None:
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")

    user = User(email=normalized_email, password_hash=await password_work(hash_password, password))
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
        await password_work(verify_password_dummy, password)
        return None
    if not await password_work(verify_password, user.password_hash, password):
        return None
    return user


async def create_session(db: AsyncSession, *, user: User, settings: Settings) -> tuple[str, str]:
    """Create a refresh-token row and return `(access_token, raw_refresh_token)`."""
    # Serialize issuance with password changes; reject credentials checked before a change.
    verified_hash = user.password_hash
    verified_email = user.email
    await lock_learner(db, user.id)
    await db.refresh(user, attribute_names=["password_hash", "email"])
    if user.password_hash != verified_hash or user.email != verified_email:
        raise ApiError(401, "INVALID_CREDENTIALS", "Incorrect email or password")
    raw_token, token_hash = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.commit()
    return create_access_token(user.id, settings), raw_token


async def rotate_session(
    db: AsyncSession, *, raw_token: str, settings: Settings
) -> tuple[User, str, str]:
    """Validate and rotate a refresh token. Returns `(user, access, new_refresh)`."""
    try:
        token_hash = hash_refresh_token(raw_token)
        user_id = await db.scalar(
            select(RefreshToken.user_id).where(RefreshToken.token_hash == token_hash)
        )
        if user_id is None:
            raise _invalid_refresh()
        # Same identity lock/order as password changes, resets and session issuance.
        # SQLite uses a write lock; PostgreSQL uses a user-row lock.
        await lock_learner(db, user_id)
        now = datetime.now(UTC)
        claimed = await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .values(revoked_at=now)
            .returning(RefreshToken.id)
            .execution_options(synchronize_session=False)
        )
        won = claimed.scalar_one_or_none() is not None
        record = await db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .execution_options(populate_existing=True)
        )
        if record is None:
            raise _invalid_refresh()
        if not won:
            if record.revoked_at is not None:
                await _revoke_all_for_user(db, record.user_id)
                await db.commit()
                raise _refresh_reused()
            raise _invalid_refresh()
        new_raw, new_hash = generate_refresh_token()
        new_record = RefreshToken(
            user_id=record.user_id,
            token_hash=new_hash,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        )
        db.add(new_record)
        await db.flush()
        record.replaced_by_id = new_record.id
        user = await get_user_with_profile(db, record.user_id)
        if user is None:  # pragma: no cover - foreign key protection
            raise _invalid_refresh()
        access_token = create_access_token(user.id, settings)
        await db.commit()
        return user, access_token, new_raw
    except BaseException:
        # A failed insert/flush/commit must not consume the old token alone.
        # Reuse revocation was explicitly committed above and remains durable.
        await db.rollback()
        raise


async def revoke_session(db: AsyncSession, *, raw_token: str) -> None:
    """Revoke this device's token chain, including an already-rotated successor."""
    token_hash = hash_refresh_token(raw_token)
    user_id = await db.scalar(
        select(RefreshToken.user_id).where(RefreshToken.token_hash == token_hash)
    )
    if user_id is not None:
        # Same identity lock as rotation: logout cannot miss a successor committed
        # by a refresh while the browser was still sending the previous cookie.
        await lock_learner(db, user_id)
        chain = (
            select(RefreshToken.id, RefreshToken.replaced_by_id)
            .where(RefreshToken.token_hash == token_hash, RefreshToken.user_id == user_id)
            .cte("logout_chain", recursive=True)
        )
        chain = chain.union(
            select(RefreshToken.id, RefreshToken.replaced_by_id)
            .join(chain, RefreshToken.id == chain.c.replaced_by_id)
            .where(RefreshToken.user_id == user_id)
        )
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id.in_(select(chain.c.id)),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
    await db.commit()


async def _revoke_all_for_user(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def invalidate_password_sessions(db: AsyncSession, user_id: UUID) -> None:
    """Revoke refresh sessions and outstanding reset tokens in the caller's transaction."""
    await _revoke_all_for_user(db, user_id)
    await db.execute(
        update(PasswordReset)
        .where(PasswordReset.user_id == user_id, PasswordReset.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )


async def sign_in_with_google(db: AsyncSession, profile: GoogleProfile) -> User:
    """Return the user for a verified Google identity, linking or creating as needed.

    1. Known Google `sub`  -> that user (the email may have changed; the `sub` is stable).
    2. Else an account with the same verified email -> link it. Fleng does not verify
       emails at sign-up, so someone could have pre-registered this address with a
       password they know ("pre-hijacking"). Linking therefore replaces the password
       with an unknown one and revokes existing sessions; the owner signs in with
       Google or uses password reset to choose a new password.
    3. Else create a new account.
    """
    for attempt in range(2):
        identity = await db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == "google", OAuthIdentity.subject == profile.subject
            )
        )
        if identity is not None:
            user = await get_user_with_profile(db, identity.user_id)
            if user is None:  # pragma: no cover - foreign key protection
                raise ApiError(500, "INTERNAL_ERROR", "Account could not be loaded")
            return user

        email = _normalize_email(profile.email)
        existing = await db.scalar(
            select(User).options(selectinload(User.profile)).where(User.email == email)
        )
        try:
            if existing is not None:
                await lock_learner(db, existing.id)
                has_google = await db.scalar(
                    select(OAuthIdentity.id).where(
                        OAuthIdentity.user_id == existing.id, OAuthIdentity.provider == "google"
                    )
                )
                if has_google is not None:
                    # A different Google account claims this email: never merge it.
                    raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists")
                existing.password_hash = await password_work(hash_password, random_password())
                await _revoke_all_for_user(db, existing.id)
                db.add(
                    OAuthIdentity(
                        user_id=existing.id,
                        provider="google",
                        subject=profile.subject,
                        email=email,
                    )
                )
                await db.commit()
                return existing

            user = User(
                email=email, password_hash=await password_work(hash_password, random_password())
            )
            user.profile = Profile(display_name=(profile.name or email.split("@")[0])[:80])
            user.progress = Progress()
            db.add(user)
            await db.flush()
            db.add(
                OAuthIdentity(
                    user_id=user.id, provider="google", subject=profile.subject, email=email
                )
            )
            await db.commit()
        except IntegrityError:
            # Lost a race (parallel callback or sign-up); look everything up again once.
            await db.rollback()
            if attempt == 1:
                raise ApiError(409, "EMAIL_TAKEN", "Could not complete sign-in") from None
            continue
        loaded = await get_user_with_profile(db, user.id)
        if loaded is None:  # pragma: no cover - defensive
            raise ApiError(500, "INTERNAL_ERROR", "Account could not be loaded")
        return loaded
    raise ApiError(409, "EMAIL_TAKEN", "Could not complete sign-in")  # pragma: no cover
