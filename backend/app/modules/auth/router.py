"""Auth HTTP endpoints.

The refresh token lives in an HttpOnly cookie scoped to `/api/v1/auth`; the
access token is returned in the JSON body and kept in memory by the frontend.
"""

import hashlib
import logging

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.limits import consume
from app.db.session import get_db
from app.modules.auth import google, service
from app.modules.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.users.service import to_user_response

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("fleng")

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
    """CSRF defence for cookie-backed endpoints: reject untrusted origins.

    The static frontend is served by this same app, so same-origin requests are
    trusted in addition to the explicitly configured CORS origins. Browsers send
    an `Origin` header on same-origin POSTs, so rejecting it would break login,
    refresh and logout. Cross-site origins remain rejected.
    """
    origin = request.headers.get("origin")
    if origin is None:
        return
    same_origin = f"{request.url.scheme}://{request.url.netloc}"
    if origin == same_origin or origin in settings.cors_origins:
        return
    # Bound and escape untrusted headers. Never log bodies, cookies or tokens.
    logger.warning(
        "Auth origin rejected method=%s path=%s origin=%r host=%r scheme=%s",
        request.method,
        request.url.path,
        origin[:256],
        request.headers.get("host", "")[:256],
        request.url.scheme,
    )
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


async def throttle(
    db: AsyncSession,
    request: Request,
    settings: Settings,
    email: str,
    *,
    registration: bool = False,
) -> None:
    # Only the ASGI peer is trusted. Deployment must constrain uvicorn proxy trust.
    ip = request.client.host if request.client else "unknown"
    digest = hashlib.sha256(ip.encode()).hexdigest()
    scope = "register" if registration else "login"
    await consume(
        db,
        f"auth:{scope}:ip:{digest}",
        settings.auth_register_ip_per_hour if registration else settings.auth_login_ip_per_minute,
        3600 if registration else 60,
    )
    # Persist IP attempts even if the email limit or credential check rejects the request.
    await db.commit()
    if not registration:
        digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        await consume(db, f"auth:login:email:{digest}", settings.auth_login_email_per_minute, 60)
        await db.commit()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    _assert_trusted_origin(request, settings)
    await throttle(db, request, settings, str(payload.email), registration=True)
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
    await throttle(db, request, settings, str(payload.email))
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


@router.get("/providers")
async def providers(settings: Settings = Depends(get_settings)) -> dict[str, bool]:
    """Which optional sign-in methods are configured (lets the UI hide dead buttons)."""
    return {"google": settings.google_enabled}


def _login_redirect(page: str, error: str) -> RedirectResponse:
    target = "/register.html" if page == "register" else "/login.html"
    return RedirectResponse(f"{target}?error={error}", status_code=status.HTTP_302_FOUND)


def _clear_oauth_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=google.STATE_COOKIE,
        path=google.STATE_COOKIE_PATH,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )


@router.get("/google/start")
async def google_start(
    page: str = Query(default="login", pattern="^(login|register)$"),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if not settings.google_enabled:
        return _login_redirect(page, "google_unavailable")
    url, cookie = google.build_authorization(settings, page)
    response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=google.STATE_COOKIE,
        value=cookie,
        max_age=int(google.STATE_TTL.total_seconds()),
        httponly=True,
        secure=settings.secure_cookies,
        # Lax: Google returns to the callback with a top-level GET navigation.
        samesite="lax",
        path=google.STATE_COOKIE_PATH,
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = Query(default=None, max_length=2048),
    state: str | None = Query(default=None, max_length=256),
    error: str | None = Query(default=None, max_length=100),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    client: google.GoogleClient = Depends(google.get_google_client),
) -> RedirectResponse:
    page = "login"
    try:
        if not settings.google_enabled:
            raise google.GoogleAuthError("google_unavailable")
        saved = google.read_state(settings, request.cookies.get(google.STATE_COOKIE), state)
        page = "register" if saved.get("page") == "register" else "login"
        if error:
            raise google.GoogleAuthError("google_denied")
        if not code:
            raise google.GoogleAuthError("google_failed")
        ip = request.client.host if request.client else "unknown"
        digest = hashlib.sha256(ip.encode()).hexdigest()
        try:
            await consume(db, f"auth:google:ip:{digest}", settings.auth_login_ip_per_minute, 60)
            await db.commit()
        except ApiError:
            raise google.GoogleAuthError("google_rate_limited") from None
        id_token = await client.exchange_code(code, saved["verifier"])
        profile = await client.verify_id_token(id_token, saved["nonce"])
        user = await service.sign_in_with_google(db, profile)
        _, raw_refresh = await service.create_session(db, user=user, settings=settings)
    except google.GoogleAuthError as exc:
        response = _login_redirect(page, exc.code)
        _clear_oauth_cookie(response, settings)
        return response
    except ApiError:
        response = _login_redirect(page, "google_failed")
        _clear_oauth_cookie(response, settings)
        return response
    response = RedirectResponse("/dashboard.html", status_code=status.HTTP_302_FOUND)
    _set_refresh_cookie(response, raw_refresh, settings)
    _clear_oauth_cookie(response, settings)
    return response
