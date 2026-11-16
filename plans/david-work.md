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
| API client | `[x]` | `frontend/js/api.js` (centralised fetch, in-memory access token, 401 refresh-and-retry) |
| Session state | `[x]` | `frontend/js/session.js` (`loadSession`, `requireSession`) |
| Protected pages | `[x]` | `js/api.js` retry + `requireSession()` redirect to `/login.html` |
| Profile | `[x]` | `frontend/dashboard.html` + `js/dashboard.js` show name/level/XP from `GET /users/me` |
| Progress | `[x]` | `frontend/js/dashboard.js` shows counters from `GET /progress/me` |
| Login / register pages | `[x]` | `frontend/login.html`, `frontend/register.html` (+ their scripts) |
| Session-aware nav | `[x]` | `frontend/js/layout.js` (`mountHeader`) |

## Definition of Done (this assignment)

- [x] Users, profiles, credentials and progress are stored in PostgreSQL models.
- [x] Real authentication (no stub): register/login/refresh/logout with argon2id.
- [x] Refresh tokens stored hashed, with rotation and reuse detection.
- [x] `GET /users/me` resolves the real user and is read-only.
- [x] `GET /progress/me` returns the user's progress (no fake data).
- [x] Frontend has real `login.html` and `register.html`, keeps the access token
      in memory and restores the session via the refresh cookie.
- [x] `dashboard.html` shows the signed-in user's name, level, XP and progress
      from the API; the static UI is served by FastAPI.
- [x] Automated tests cover the security-critical auth cases and cross-user isolation.
- [x] `ruff`, `mypy`, `pytest`, `pnpm lint`, `typecheck`, `test`, `build` pass.
- [x] Docs, project-map and plans updated.
- [ ] Migrations applied to a real PostgreSQL instance (environment-blocked here).

## Remaining (not part of the core assignment)

- **CRITICAL:** run migrations + integration tests against real PostgreSQL.
- **NEXT:** rate limiting on auth endpoints; profile editing (`PATCH /users/me`).
- **LATER:** email verification, password reset, role/RBAC, "log out everywhere".


## Vocabulary flashcards — 2026-11-10

Completed: vocabulary audit, course-word catalog and filters, persistent owned flashcard sessions, completion and Roma handoff contract. Next: frontend category/flip/navigation integration; Roma test engine and XP; curated catalog import. A0 course model extension deferred for shared catalog coordination. Live PostgreSQL NOT VERIFIED.

Validation: full pytest 293 passed / 15 skipped; expanded flashcard tests 7 passed,
SQLite migration preservation 1 passed; Ruff, mypy, Alembic SQLite check/head,
PostgreSQL offline SQL and diff whitespace check passed. Independent self-review
completed. Final verification and one logical commit authorized by the follow-up
request; no push.

Final pre-commit checks: full pytest 297 passed / 15 skipped; Ruff, mypy,
Alembic SQLite checks, PostgreSQL offline SQL and git diff --check passed.


## A0–B2 curriculum — 2026-11-10

Completed: introductory A0 schema/migration, full 5-course/50-lesson draft, 500 vocabulary rows and 400 exercises, validation, immutable/idempotent draft importer and integration tests. Supersedes earlier deferred A0/catalog-content notes. Next: human linguistic/translation review, publication approval and production release procedure; Roma test logic unchanged. No commit/push.

Verification: pytest 325 passed / 15 skipped; final current-content tests 29
passed; Ruff, mypy (68 files), SQLite migration/seed smoke, Alembic check/head,
PostgreSQL offline SQL and diff check passed. DOM catalog checks: 7 passed.
All 50 lessons remain draft; live PostgreSQL NOT VERIFIED.
