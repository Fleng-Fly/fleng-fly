# Authentication & Authorization

> Status: **implemented** (M2). Email/password authentication, rotating refresh
> sessions and the `get_current_user` dependency work end to end. Roles/RBAC,
> email verification and password reset are not implemented yet. Design notes for
> the deferred parts are marked below.

## 1. Model

- Credentials: email + password.
- Passwords hashed with **argon2id** (`argon2-cffi` defaults). Hashes are never
  logged or returned.
- Sessions: a short-lived **access JWT** (kept in frontend memory) plus an opaque
  **rotating refresh token** in an HttpOnly, `SameSite`, path-scoped cookie.
- Refresh tokens are stored **hashed** (SHA-256 hex) in `refresh_tokens`
  (`docs/database.md`), so the database never holds a usable bearer secret.
- Authorization today is simply "authenticated user". Role-based access control
  and ownership-scoped resources arrive with the learning catalog.

## 2. Endpoints

| Flow | Endpoint | Notes |
| ---- | -------- | ----- |
| Register | `POST /api/v1/auth/register` | `201`; creates User + Profile + Progress; sets the refresh cookie |
| Login | `POST /api/v1/auth/login` | `200`; generic error, no account enumeration |
| Refresh | `POST /api/v1/auth/refresh` | rotates the refresh token; sets a new cookie |
| Logout | `POST /api/v1/auth/logout` | revokes the presented token and clears the cookie |
| Current user | `GET /api/v1/users/me` | Bearer access token; read-only |

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
  → server looks up the hash, checks expiry and revocation
  → rotates: revokes the old token, issues a new one (linked via replaced_by_id)
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

- Access token in memory only (`src/lib/api/client.ts`).
- `apiFetch` attaches `Authorization: Bearer`; on `401` it attempts **one**
  refresh and retries the request once, de-duplicating concurrent refreshes.
- `AuthProvider` (`src/lib/auth/auth-context.tsx`) resolves the session on load
  and exposes `login`/`register`/`logout`; `/learn` redirects to `/login` when
  unauthenticated.

## 7. Not implemented yet

- Email verification and password reset (email provider deferred).
- Role-based access control (`ADMIN`) and public profiles.
- Rate limiting on auth endpoints (`plans/security-plan.md` Stage 2).
- Multi-device session listing / "log out everywhere" (the schema supports it).
- OAuth providers and MFA.
