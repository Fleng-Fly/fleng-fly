# Authentication & Authorization

> Status: **implemented** (M2). Email/password authentication, rotating refresh
> sessions and the `get_current_user` dependency work end to end. Roles/RBAC,
> and email verification are deferred; password reset is implemented (SMTP opt-in).
> Design notes for deferred parts are marked below.

## 1. Model

- Credentials: email + password.
- Passwords hashed with **argon2id** (`argon2-cffi` defaults). Hashes are never
  logged or returned.
- Sessions: a short-lived **access JWT** (kept in frontend memory) plus an opaque
  **rotating refresh token** in an HttpOnly, `SameSite`, path-scoped cookie.
- Refresh tokens are stored **hashed** (SHA-256 hex) in `refresh_tokens`
  (`docs/database.md`), so the database never holds a usable bearer secret.
- Authorization today is simply "authenticated user". Role-based access control
  is deferred. Ownership-scoped learning, vocabulary and AI resources are implemented.

## 2. Endpoints

| Flow | Endpoint | Notes |
| ---- | -------- | ----- |
| Register | `POST /api/v1/auth/register` | `201`; creates User + Profile + Progress; sets the refresh cookie |
| Login | `POST /api/v1/auth/login` | `200`; generic error, no account enumeration |
| Refresh | `POST /api/v1/auth/refresh` | rotates the refresh token; sets a new cookie |
| Logout | `POST /api/v1/auth/logout` | revokes the presented token and clears the cookie |
| Current user | `GET /api/v1/users/me` | Bearer access token; read-only |
| Account details | `PATCH /api/v1/users/me` | Bearer access token; updates own name, email or language preference |
| Change password | `POST /api/v1/users/me/password` | `204`; verifies current password, changes hash and revokes refresh/reset tokens atomically; sign in again |

## 3. Token flow

```
Register/Login
  → verify credentials (argon2id; dummy verify when the email is unknown)
  → issue access token (HS256 JWT, ~15m)
  → generate opaque refresh token; store SHA-256 hash; set raw value as cookie

Authenticated request
  → Authorization: Bearer <access>
  → get_current_user verifies signature + expiry (+ type) and loads the User

Access token expired
  → frontend calls POST /auth/refresh (cookie sent automatically)
  → server resolves identity and takes the shared learner lock
  → conditionally claims an unrevoked, unexpired token with UPDATE RETURNING
  → revocation, new token and replaced_by_id link commit together
  → returns a new access token + rotated cookie

Logout
  → revoke the presented refresh token server-side, clear the cookie
```

### Access token claims

`sub` (user id), `type` ("access"), `jti`, `iat`, `exp`. No PII beyond `sub`.
Signed with `JWT_ACCESS_SECRET` (HS256). The token is rejected if `type` is not
`access`.

### Refresh tokens and reuse detection

Refresh tokens are **opaque** random strings (`secrets.token_urlsafe(48)`), not
JWTs: the server only needs to look up their hash. Each token belongs to a chain
(`replaced_by_id`). On refresh the old token is revoked and a new one issued. If a
**revoked** token is presented (a replay), the entire user session set is revoked
and the client must re-authenticate (`401 REFRESH_TOKEN_REUSED`).

## 4. Cookies and CSRF

- Cookie: `fleng_refresh`, `HttpOnly`, `SameSite=Lax`, `Secure` in production,
  `path=/api/v1/auth`, `max-age` = refresh lifetime (30 days by default).
- `SameSite=Lax` prevents the cookie from being sent on cross-site POSTs.
- Cookie-backed endpoints (`login`, `refresh`, `logout`) additionally reject
  requests whose `Origin` header is not in `CORS_ORIGIN`.
- The frontend never stores the access token in `localStorage`; it lives in
  memory and is re-obtained via `/auth/refresh` on reload.

## 5. Configuration

| Variable | Meaning |
| -------- | ------- |
| `JWT_ACCESS_SECRET` | Access-token signing secret; **required in production** (startup fails with the development default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime (default 15) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token/session lifetime (default 30) |
| `COOKIE_SECURE` / `COOKIE_SAMESITE` | Cookie flags (secure defaults to `APP_ENV == production`) |

## 6. Frontend handling

- Access token in memory only (`frontend/js/api.js`), never in
  `localStorage`/`sessionStorage`.
- `apiFetch` attaches `Authorization: Bearer`; on `401` it attempts **one**
  refresh and retries the request once, de-duplicating concurrent refreshes.
- `js/session.js` resolves the session on load (`loadSession`); protected pages
  call `requireSession()`, which redirects to `/login.html` when unauthenticated.
- The static frontend is served by the backend on the same origin, so the
  refresh cookie is first-party and no CORS is involved.

## 7. Not implemented yet

- Email verification. Password reset is implemented; real SMTP delivery remains unverified.
- Role-based access control (`ADMIN`) and public profiles.
- Rate limiting on refresh (login/register/reset already have persistent limits).
- Multi-device session listing / "log out everywhere" (the schema supports it).
- OAuth providers and MFA.

## Stabilized sessions and password changes

Only one transaction can claim a refresh token. Concurrent reuse returns
`401 REFRESH_TOKEN_REUSED` and durably revokes the whole user refresh-session set,
including the winning request's successor. The winner can therefore receive a
cookie already revoked by the concurrent replay; this intentionally preserves the
existing strict reuse policy. Unknown/expired tokens return `401 INVALID_REFRESH_TOKEN`.
Failures before a successful commit roll back the old claim and successor together.

Rotation, login issuance, password change and reset share the same identity lock.
Login rechecks the verified password hash under that lock, preventing issuance
from credentials verified before a concurrent password change. Normal password
change refreshes the password hash after locking, preventing stale verification.
Both password flows revoke every refresh session and unused reset token within
the password transaction. A failed request session is rolled back on close.
The existing route is **POST**, not PATCH, `/users/me/password`; its `204` contract
is preserved. Settings clears its in-memory access token, explains that another
sign-in is required, then redirects to login. No new token-version field is added.

**Access JWT policy:** logout, password change/reset and reuse detection revoke
refresh tokens. Already issued access JWTs remain valid until their configured
expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 15). Other tabs/devices can retain
this limited access. Immediate access-token revocation would require an additional
revocation/version mechanism and is outside this stabilization.

## Login/register throttling and proxy trust

All limits are fixed UTC windows in the existing `request_limits` table:

| Setting | Default | Scope |
| --- | --- | --- |
| `AUTH_LOGIN_IP_PER_MINUTE` | 20 | Login attempts per peer IP/minute |
| `AUTH_LOGIN_EMAIL_PER_MINUTE` | 10 | Login attempts per normalized email/minute, shared across IPs |
| `AUTH_REGISTER_IP_PER_HOUR` | 10 | Registration attempts per peer IP/hour |

Limits apply before expensive password work, regardless of credential success or
account existence. Keys contain SHA-256 digests, not raw email/IP. A conditional
counter increment prevents concurrent overspending. IP attempts commit before the
email check so an exhausted email window cannot bypass IP accounting. `429
RATE_LIMITED` has the same generic response for all accounts; `Retry-After` is the
positive, rounded-up number of seconds until that window ends. The existing
registration `409 EMAIL_TAKEN` contract remains unchanged (registration can still
reveal duplicates); the limiter adds no account-dependent response.

The app reads only ASGI `request.client.host`, never raw `X-Forwarded-For`.
`npm run dev` and `backend:dev` disable proxy-header processing. In a proxied
production deployment configure Uvicorn `--proxy-headers --forwarded-allow-ips`
with only actual trusted proxy addresses, restrict direct backend access, and
have the proxy overwrite forwarded headers. Never trust `*` on a public backend.
Without a trusted proxy configuration, requests share the proxy's IP quota.
