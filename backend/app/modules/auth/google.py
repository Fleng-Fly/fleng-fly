"""Google sign-in: OAuth 2.0 authorization-code flow with PKCE, run on the server.

The browser never handles Google tokens. `start` redirects to Google with a signed,
short-lived state cookie; `callback` checks that state, exchanges the code, verifies the
ID token (signature, issuer, audience, expiry, nonce) and returns the verified claims.
Account matching lives in `service.sign_in_with_google`.
"""

import base64
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

import anyio
import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ("https://accounts.google.com", "accounts.google.com")
STATE_TTL = timedelta(minutes=10)
STATE_COOKIE = "fleng_oauth"
STATE_COOKIE_PATH = "/api/v1/auth/google"


class GoogleAuthError(Exception):
    """Sign-in must stop. `code` is a stable value shown to the learner via the login page."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class GoogleProfile:
    subject: str
    email: str
    name: str


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_authorization(
    settings: Settings, origin_page: str, link_user_id: str | None = None
) -> tuple[str, str]:
    """Return `(google_url, signed_state_cookie_value)` for a new sign-in attempt.

    `link_user_id` marks a link request: the state cookie is then bound to that account
    (it is only minted after the account's password was re-entered) and the callback
    attaches the Google identity to it instead of signing anyone in.
    """
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    cookie = jwt.encode(
        {
            "type": "google_oauth_state",
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
            "page": origin_page,
            "link": link_user_id,
            "exp": datetime.now(UTC) + STATE_TTL,
        },
        settings.jwt_access_secret,
        algorithm=settings.jwt_algorithm,
    )
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
    )
    return f"{AUTH_URL}?{query}", cookie


def read_state(settings: Settings, cookie: str | None, state: str | None) -> dict[str, Any]:
    """Validate the state cookie against the `state` query value (CSRF / login-CSRF defence)."""
    if not cookie or not state:
        raise GoogleAuthError("google_state")
    try:
        data = jwt.decode(
            cookie,
            settings.jwt_access_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"]},
        )
    except jwt.InvalidTokenError:
        raise GoogleAuthError("google_state") from None
    if data.get("type") != "google_oauth_state" or not hmac.compare_digest(
        str(data.get("state", "")), state
    ):
        raise GoogleAuthError("google_state")
    return data


class GoogleClient:
    """Talks to Google. Replaced by a fake in tests through `get_google_client`."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jwks = PyJWKClient(JWKS_URL, cache_keys=True, timeout=10)

    async def exchange_code(self, code: str, verifier: str) -> str:
        """Trade the authorization code for an ID token (server-to-server, TLS)."""
        s = self._settings
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                response = await http.post(
                    TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": s.google_client_id,
                        "client_secret": s.google_client_secret.get_secret_value(),
                        "redirect_uri": s.google_redirect_uri,
                        "grant_type": "authorization_code",
                        "code_verifier": verifier,
                    },
                )
        except httpx.HTTPError:
            raise GoogleAuthError("google_unavailable") from None
        if response.status_code != 200:
            raise GoogleAuthError("google_failed")
        try:
            id_token = response.json().get("id_token")
        except ValueError:
            id_token = None
        if not isinstance(id_token, str) or not id_token:
            raise GoogleAuthError("google_failed")
        return id_token

    async def verify_id_token(self, id_token: str, nonce: str) -> GoogleProfile:
        try:
            key = await anyio.to_thread.run_sync(self._jwks.get_signing_key_from_jwt, id_token)
        except jwt.PyJWKClientConnectionError:
            raise GoogleAuthError("google_unavailable") from None
        except jwt.InvalidTokenError:
            raise GoogleAuthError("google_failed") from None
        return verify_claims(id_token, key.key, self._settings, nonce)


def verify_claims(id_token: str, key: Any, settings: Settings, nonce: str) -> GoogleProfile:
    """Verify signature, audience, expiry, issuer, nonce and email_verified."""
    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise GoogleAuthError("google_failed") from None
    if claims.get("iss") not in ISSUERS:
        raise GoogleAuthError("google_failed")
    if not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
        raise GoogleAuthError("google_failed")
    email = claims.get("email")
    # Google sends a boolean, but never trust a truthy string such as "false".
    if not isinstance(email, str) or not email or claims.get("email_verified") is not True:
        raise GoogleAuthError("google_unverified")
    subject = str(claims["sub"])
    if not subject or len(subject) > 255:
        raise GoogleAuthError("google_failed")
    name = str(claims.get("name") or "").strip()
    return GoogleProfile(subject=subject, email=email.strip().lower(), name=name)


@lru_cache
def _shared_client() -> GoogleClient:
    # One instance keeps Google's signing keys cached between sign-ins.
    return GoogleClient(get_settings())


def get_google_client() -> GoogleClient:
    return _shared_client()


def random_password() -> str:
    """A password nobody knows: Google-only accounts cannot be logged into by password."""
    return uuid.uuid4().hex + secrets.token_urlsafe(32)
