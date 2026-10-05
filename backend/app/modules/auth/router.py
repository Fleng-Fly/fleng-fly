"""Auth HTTP endpoints.

The refresh token lives in an HttpOnly cookie scoped to `/api/v1/auth`; the
access token is returned in the JSON body and kept in memory by the frontend.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.users.service import to_user_response

router = APIRouter(prefix="/auth", tags=["auth"])

_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def _expires_in(settings: Settings) -> int:
    return settings.access_token_expire_minutes * 60


def _set_refresh_cookie(response: Response, raw_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def _delete_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
    )


def _assert_trusted_origin(request: Request, settings: Settings) -> None:
    """CSRF defence for cookie-backed endpoints: reject untrusted origins."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise ApiError(403, "FORBIDDEN", "Origin not allowed")


def _read_refresh_cookie(request: Request, settings: Settings) -> str:
    raw = request.cookies.get(settings.refresh_cookie_name)
    if not raw:
        raise ApiError(
            401,
            "INVALID_REFRESH_TOKEN",
            "Invalid or expired session",
            headers=_UNAUTHORIZED_HEADERS,
        )
    return raw


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    access_token, raw_refresh = await service.create_session(db, user=user, settings=settings)
    _set_refresh_cookie(response, raw_refresh, settings)
    return TokenResponse(
        access_token=access_token,
        expires_in=_expires_in(settings),
        user=to_user_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    _assert_trusted_origin(request, settings)
    user = await service.authenticate(db, email=payload.email, password=payload.password)
    if user is None:
        raise ApiError(
            401, "INVALID_CREDENTIALS", "Incorrect email or password", headers=_UNAUTHORIZED_HEADERS
        )
    access_token, raw_refresh = await service.create_session(db, user=user, settings=settings)
    _set_refresh_cookie(response, raw_refresh, settings)
    return TokenResponse(
        access_token=access_token,
        expires_in=_expires_in(settings),
        user=to_user_response(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AccessTokenResponse:
    _assert_trusted_origin(request, settings)
    raw_refresh = _read_refresh_cookie(request, settings)
    _, access_token, new_refresh = await service.rotate_session(
        db, raw_token=raw_refresh, settings=settings
    )
    _set_refresh_cookie(response, new_refresh, settings)
    return AccessTokenResponse(access_token=access_token, expires_in=_expires_in(settings))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    _assert_trusted_origin(request, settings)
    raw_refresh = request.cookies.get(settings.refresh_cookie_name)
    if raw_refresh:
        await service.revoke_session(db, raw_token=raw_refresh)
    _delete_refresh_cookie(response, settings)
