"""Auth HTTP endpoints.

The refresh token lives in an HttpOnly cookie scoped to `/api/v1/auth`; the
access token is returned in the JSON body and kept in memory by the frontend.
"""

import hashlib
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.limits import consume
from app.db.models import User
from app.db.session import get_db
from app.modules.auth import google, service
from app.modules.auth.schemas import (
    AccessTokenResponse,
    GoogleLinkRequest,
    GoogleLinkResponse,
    IdentitiesResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.security import password_work, verify_password
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


def _set_oauth_cookie(response: Response, value: str, settings: Settings) -> None:
    response.set_cookie(
        key=google.STATE_COOKIE,
        value=value,
        max_age=int(google.STATE_TTL.total_seconds()),
        httponly=True,
        secure=settings.secure_cookies,
        # Lax: Google returns to the callback with a top-level GET navigation.
        samesite="lax",
        path=google.STATE_COOKIE_PATH,
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
    _set_oauth_cookie(response, cookie, settings)
    return response


@router.get("/identities", response_model=IdentitiesResponse)
async def identities(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> IdentitiesResponse:
    return IdentitiesResponse(google_linked=await service.has_google_identity(db, current_user.id))


@router.post("/google/link", response_model=GoogleLinkResponse)
async def google_link(
    payload: GoogleLinkRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GoogleLinkResponse:
    """Start connecting Google to the signed-in account after re-entering its password.

    The password proves ownership right now (a stolen access token or an old session is not
    enough). The returned Google URL belongs to a state cookie bound to this account.
    """
    if not settings.google_enabled:
        raise ApiError(503, "GOOGLE_UNAVAILABLE", "Google sign-in is not configured")
    # Same budget as password logins: this endpoint is a password oracle for a stolen token.
    await consume(
        db, f"auth:google-link:{current_user.id}", settings.auth_login_email_per_minute, 60
    )
    await db.commit()
    if await service.has_google_identity(db, current_user.id):
        raise ApiError(409, "GOOGLE_ALREADY_LINKED", "A Google account is already connected")
    if not await password_work(verify_password, current_user.password_hash, payload.password):
        raise ApiError(400, "INVALID_PASSWORD", "Password is incorrect")
    url, cookie = google.build_authorization(settings, "login", str(current_user.id))
    _set_oauth_cookie(response, cookie, settings)
    response.headers["Cache-Control"] = "no-store"
    return GoogleLinkResponse(url=url)


_LINK_ERRORS = {
    "GOOGLE_EMAIL_MISMATCH": "google_email_mismatch",
    "GOOGLE_ALREADY_LINKED": "google_already_linked",
}


def _failed(page: str, linking: bool, code: str, settings: Settings) -> RedirectResponse:
    if linking:
        response = RedirectResponse(f"/settings.html?googleError={code}", status.HTTP_302_FOUND)
    else:
        response = _login_redirect(page, code)
    _clear_oauth_cookie(response, settings)
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
    linking = False
    try:
        if not settings.google_enabled:
            raise google.GoogleAuthError("google_unavailable")
        saved = google.read_state(settings, request.cookies.get(google.STATE_COOKIE), state)
        page = "register" if saved.get("page") == "register" else "login"
        linking = bool(saved.get("link"))
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
        if linking:
            await service.link_google(db, user_id=UUID(saved["link"]), profile=profile)
            response = RedirectResponse("/settings.html?google=linked", status.HTTP_302_FOUND)
            _clear_oauth_cookie(response, settings)
            return response
        user = await service.sign_in_with_google(db, profile)
        _, raw_refresh = await service.create_session(db, user=user, settings=settings)
    except google.GoogleAuthError as exc:
        return _failed(page, linking, exc.code, settings)
    except service.GoogleLinkRequired:
        return _failed(page, linking, "google_link_required", settings)
    except ApiError as exc:
        return _failed(page, linking, _LINK_ERRORS.get(exc.code, "google_failed"), settings)
    except ValueError:  # a state cookie without a usable account id
        return _failed(page, linking, "google_state", settings)
    response = RedirectResponse("/dashboard.html", status_code=status.HTTP_302_FOUND)
    _set_refresh_cookie(response, raw_refresh, settings)
    _clear_oauth_cookie(response, settings)
    return response
