from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings


def get_current_user_id(settings: Settings = Depends(get_settings)) -> UUID:
    """DEVELOPMENT-ONLY authentication stub.

    Returns a fixed development user id. It is NOT authentication and refuses to
    run in production. Replace with a JWT dependency when the auth milestone lands.
    """
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not implemented yet",
        )
    return settings.dev_user_id
