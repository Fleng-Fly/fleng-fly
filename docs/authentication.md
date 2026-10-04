# Authentication & Authorization

> Status: **not implemented**. This is the design for the auth milestone. Today
> the only identity mechanism is the development-only `get_current_user_id`
> dependency described in `docs/backend.md`, which refuses to run when
> `APP_ENV=production`. Do not treat any of the flows below as existing.

## 1. Model

- Credentials: email + password.
- Passwords hashed with **argon2id** (memory-hard). Never log or return hashes.
- Sessions: short-lived **JWT access token** (memory on the client) + **rotating
  refresh token** in an httpOnly, `Secure`, `SameSite` cookie.
- Refresh tokens are stored **hashed** (SHA-256) in `refresh_tokens`
  (`docs/database.md`), enabling revocation without storing bearer secrets.
- Authorization: role-based (`USER`, `ADMIN`) plus **ownership scoping** in
  queries.

## 2. Token flow

```
Register/Login
  → verify credentials
  → issue access token (JWT, ~15m) + refresh token (~30d)
  → refresh token hashed + persisted; raw value set as httpOnly cookie

Authenticated request
  → Authorization: Bearer <access>
  → get_current_user dependency verifies signature + expiry + user status

Access token expired
  → frontend calls POST /auth/refresh (cookie sent automatically)
  → server validates hash, not revoked, not expired
  → rotates: revokes old, issues new refresh token (reuse detection)
  → returns new access token + rotated cookie

Logout
  → revoke refresh token server-side, clear cookie
```

### Refresh token rotation and reuse detection

Each refresh token belongs to a chain (`replaced_by_id`). On refresh, the old
token is revoked and a new one issued. If a **revoked** token is presented
(replay), the entire chain is revoked and the user must re-authenticate.

### Token claims

Access JWT: `sub` (user id), `role`, `iat`, `exp`, `jti`. No PII beyond
`sub`/`role`. Secrets (`JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`) are distinct and
env-provided; add them to `Settings` when the milestone starts.

## 3. Account lifecycle

| Flow | Endpoint | Notes |
| ---- | -------- | ----- |
| Register | `POST /auth/register` | Rate limited; sends verification email (provider deferred) |
| Verify email | `POST /auth/verify-email` | Token single-use, time-limited |
| Login | `POST /auth/login` | Generic error; no account enumeration |
| Refresh | `POST /auth/refresh` | Rotation + reuse detection |
| Logout | `POST /auth/logout` | Revokes the presented refresh token |
| Forgot password | `POST /auth/forgot-password` | Always `202`; no enumeration |
| Reset password | `POST /auth/reset-password` | Revokes all refresh tokens on success |
| Delete account | `DELETE /users/me` | Revokes all sessions; deletion policy TBD |

## 4. Authorization

- A `get_current_user` FastAPI dependency authenticates via JWT and returns the
  `User`; a `require_role("ADMIN")` dependency enforces coarse roles.
- Fine-grained ownership is enforced in services/queries via `user_id`
  predicates. A dependency alone is insufficient.
- Admins can manage catalog/content but not read user AI conversations or
  private data without an explicit, logged reason.

## 5. Security controls tied to auth

- Rate limiting on login/register/refresh/forgot-password.
- Timing-consistent login (always run a hash comparison) to avoid enumeration.
- Cookies: `httpOnly`, `Secure` in production, `SameSite=Lax` (or `Strict` where
  CSRF risk requires), scoped path for the refresh endpoint.
- CSRF: refresh relies on a cookie; the endpoint is POST-only, checks `Origin`,
  and returns only an access token.
- Password policy: minimum length + breach guidance.

See `docs/security.md` for the full security model.

## 6. Frontend handling

- Access token in memory only (never `localStorage`).
- Refresh via the httpOnly cookie; the API client retries a single request after
  a successful refresh.
- On refresh failure, redirect to login and clear client state.

## 7. Open questions

- Multi-device session listing / "log out everywhere" (schema already supports it).
- OAuth providers (Google/Apple) — deferred.
- MFA — deferred.
