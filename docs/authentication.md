# Authentication & Authorization

> Status: **design** (pre-implementation). Implementation: NestJS + Passport +
> Prisma.

## 1. Model

- Credentials: email + password.
- Passwords hashed with **argon2id** (memory-hard). Never log or return hashes.
- Sessions: short-lived **JWT access token** (memory on the client) + **rotating
  refresh token** in an httpOnly, `Secure`, `SameSite` cookie.
- Refresh tokens are stored **hashed** (SHA-256) in `RefreshToken`
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
  → JwtAuthGuard verifies signature + expiry + user status

Access token expired
  → frontend calls POST /auth/refresh (cookie sent automatically)
  → server validates hash, not revoked, not expired
  → rotates: revokes old, issues new refresh token (reuse detection)
  → returns new access token + rotates cookie

Logout
  → revoke refresh token server-side, clear cookie
```

### Refresh token rotation and reuse detection

Each refresh token belongs to a chain (`replacedById`). On refresh, the old token
is revoked and a new one issued. If a **revoked** token is presented (replay),
the entire chain is revoked and the user is forced to re-authenticate.

### Token claims

Access JWT: `sub` (userId), `role`, `iat`, `exp`, `jti`. No PII beyond `sub`/`role`.
Secrets (`JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`) are distinct and env-provided.

## 3. Account lifecycle

| Flow | Endpoint | Notes |
| ---- | -------- | ----- |
| Register | `POST /auth/register` | Rate limited; sends verification email (provider deferred) |
| Verify email | `POST /auth/verify-email` | Token is single-use, time-limited |
| Login | `POST /auth/login` | Generic error; no account enumeration |
| Refresh | `POST /auth/refresh` | Rotation + reuse detection |
| Logout | `POST /auth/logout` | Revokes the presented refresh token |
| Forgot password | `POST /auth/forgot-password` | Always `202`; no enumeration |
| Reset password | `POST /auth/reset-password` | Revokes all refresh tokens on success |
| Delete account | `DELETE /users/me` | Revokes all sessions; deletion policy TBD |

## 4. Authorization

- `JwtAuthGuard` authenticates; `RolesGuard` + `@Roles()` enforces coarse roles.
- Fine-grained ownership is enforced in services/repositories via `userId`
  predicates. A guard alone is insufficient.
- Admins can manage catalog/content but not read user AI conversations or
  private data without an explicit, logged reason.

## 5. Security controls tied to auth

- Rate limiting on login/register/refresh/forgot-password.
- Constant-time-ish behaviour: always run a hash comparison on login failure to
  avoid timing/user enumeration.
- Cookies: `httpOnly`, `Secure` in production, `SameSite=Lax` (or `Strict` where
  CSRF risk requires), scoped path for the refresh endpoint.
- CSRF: refresh relies on a cookie; the endpoint is POST-only, checks `Origin`,
  and returns only an access token — no state-changing action without a bearer
  token.
- Password policy: minimum length + breach guidance; never silently truncate.

See `docs/security.md` for the full security model.

## 6. Frontend handling

- Access token in memory only (never `localStorage`).
- Refresh via the httpOnly cookie; the API client retries a single request after
  a successful refresh.
- On refresh failure, redirect to login and clear client state.

## 7. Open questions

- Multi-device session listing / "log out everywhere" (schema already supports it).
- OAuth providers (Google/Apple) — deferred; the `User` model can add an
  `OAuthAccount` table without changing existing flows.
- MFA — deferred.
