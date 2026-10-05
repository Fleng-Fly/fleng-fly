# David's Work

> Scope: internal storage for logins and progress, and connecting it to the
> frontend. Legend: `[x]` done · `[~]` in progress · `[ ]` todo · `[!]` blocked.
> "Verified" means exercised by an automated test, not just present in docs.
> Last updated: M2/M3.

## Storage

| Task | Status | Where |
| ---- | ------ | ----- |
| User | `[x]` | `backend/app/db/models.py` (`User`), migration `20261004_1200_init` |
| Profile | `[x]` | `backend/app/db/models.py` (`Profile`), same migration |
| Authentication data | `[x]` | `password_hash` (argon2id) + `RefreshToken` (hashed); migration `20261005_1000_auth_progress` |
| Progress | `[x]` | `backend/app/db/models.py` (`Progress`), migration `20261005_1000_auth_progress` |
| Migrations | `[x]` | `backend/alembic/versions/20261004_1200_init.py`, `.../20261005_1000_auth_progress.py` |
| Migrations applied to a real PostgreSQL | `[!]` | Blocked by environment: no Docker/PostgreSQL here. SQL verified offline with `pnpm db:sql`. See "Remaining". |

`Progress` is a per-user aggregate (`lessonsStarted`, `lessonsCompleted`,
`studyMinutes`, `lastActivityAt`). Per-lesson rows will go in a future
`LessonProgress` table once `lessons` exist — see `docs/database.md`.

## Backend

| Task | Status | Where |
| ---- | ------ | ----- |
| Auth | `[x]` | `backend/app/modules/auth/` (register, login, refresh, logout; argon2id; rotation + reuse detection) |
| Users | `[x]` | `backend/app/modules/users/` — `GET /users/me`, read-only, real `get_current_user` |
| Progress | `[x]` | `backend/app/modules/progress/` — `GET /progress/me` (read-only) |
| API wiring | `[x]` | `backend/app/api/router.py`, `backend/app/api/deps.py` |
| Auth/progress tests | `[x]` | `backend/tests/test_auth.py`, `test_users.py`, `test_progress.py` |
| Rate limiting on auth | `[ ]` | `plans/security-plan.md` Stage 2 |

## Frontend Integration

| Task | Status | Where |
| ---- | ------ | ----- |
| API client | `[x]` | `frontend/src/lib/api/client.ts` (centralised fetch, in-memory access token, 401 refresh-and-retry) |
| Authentication state | `[x]` | `frontend/src/lib/auth/auth-context.tsx` (`AuthProvider`, `useAuth`) |
| Protected requests | `[x]` | `client.ts` retry + `frontend/src/app/learn/page.tsx` redirect to `/login` |
| Profile | `[x]` | `frontend/src/app/learn/page.tsx` shows name/level/XP from `GET /users/me` |
| Progress | `[x]` | `frontend/src/lib/api/progress.ts` + `/learn` shows counters from `GET /progress/me` |
| Login / register pages | `[x]` | `frontend/src/app/login/page.tsx`, `/register/page.tsx` |
| Session-aware nav | `[x]` | `frontend/src/components/user-menu.tsx`, `app-shell.tsx` |

## Definition of Done (this assignment)

- [x] Users, profiles, credentials and progress are stored in PostgreSQL models.
- [x] Real authentication (no stub): register/login/refresh/logout with argon2id.
- [x] Refresh tokens stored hashed, with rotation and reuse detection.
- [x] `GET /users/me` resolves the real user and is read-only.
- [x] `GET /progress/me` returns the user's progress (no fake data).
- [x] Frontend has real `/login` and `/register`, keeps the access token in
      memory and restores the session via the refresh cookie.
- [x] `/learn` shows the signed-in user's name, level, XP and progress from the API.
- [x] Automated tests cover the security-critical auth cases and cross-user isolation.
- [x] `ruff`, `mypy`, `pytest`, `pnpm lint`, `typecheck`, `test`, `build` pass.
- [x] Docs, project-map and plans updated.
- [ ] Migrations applied to a real PostgreSQL instance (environment-blocked here).

## Remaining (not part of the core assignment)

- **CRITICAL:** run migrations + integration tests against real PostgreSQL.
- **NEXT:** rate limiting on auth endpoints; profile editing (`PATCH /users/me`).
- **LATER:** email verification, password reset, role/RBAC, "log out everywhere".
