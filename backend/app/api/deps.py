from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.models import User
from app.db.session import get_db
from app.modules.auth.security import decode_access_token
from app.modules.users.service import get_user_with_profile

_bearer_scheme = HTTPBearer(auto_error=False)
_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def _unauthorized() -> ApiError:
    return ApiError(
        401, "UNAUTHORIZED", "Authentication required", headers=_UNAUTHORIZED_HEADERS
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolve the authenticated user from a Bearer access token.

    Returns `401` for a missing, malformed or expired token. Never creates a
    user; identity always comes from the token subject.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    user_id = decode_access_token(credentials.credentials, settings)
    if user_id is None:
        raise _unauthorized()
    user = await get_user_with_profile(db, user_id)
    if user is None:
        raise _unauthorized()
    return user
