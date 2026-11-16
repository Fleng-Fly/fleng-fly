"""Password hashing and token primitives.

Passwords use **argon2id** (argon2-cffi defaults). Access tokens are short-lived
HS256 JWTs. Refresh tokens are opaque random strings; only their SHA-256 hash is
stored (see `docs/authentication.md`).
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import anyio
import jwt
from anyio.lowlevel import RunVar
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings

_hasher = PasswordHasher()

# A fixed hash used to keep login timing consistent when the email is unknown.
_DUMMY_HASH = _hasher.hash("timing-equalisation-placeholder")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_password_dummy(password: str) -> None:
    """Run a verification against a dummy hash to equalise login timing."""
    verify_password(_DUMMY_HASH, password)


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_access_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> uuid.UUID | None:
    """Return the subject user id, or `None` if the token is invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_access_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        return None


def generate_refresh_token() -> tuple[str, str]:
    """Return `(raw_token, token_hash)`."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def password_work(function, *args):
    """Run Argon2 off the event loop with a dedicated bounded worker budget."""
    try:
        limiter = _password_limiter.get()
    except LookupError:
        limiter = anyio.CapacityLimiter(4)
        _password_limiter.set(limiter)
    return await anyio.to_thread.run_sync(function, *args, limiter=limiter)


_password_limiter: RunVar[anyio.CapacityLimiter] = RunVar("fleng_password_limiter")
