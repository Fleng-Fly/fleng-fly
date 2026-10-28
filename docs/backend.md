# Backend

> Status: **M2 implemented**. Stack: Python 3.11+ / FastAPI / SQLAlchemy 2
> (async) / Alembic / Pydantic. Implemented modules: `health`, `auth`, `users`,
> `progress`, catalog/exercises, vocabulary/gamification, password reset and AI.
> Live PostgreSQL/OpenRouter verification remains pending; see the extension section.

## 1. Responsibilities

The backend is the only part of the system allowed to make decisions about data:
validation, authorization, business rules, persistence and AI
orchestration. The frontend never reaches the database.

## 2. Project structure (current)

Feature modules live under `app/modules/<name>/`. Future modules follow the same
shape; they are added only when the feature exists.

```
backend/
├── app/
│   ├── main.py                 # create_app: CORS, error handlers, /api/v1 router
│   ├── core/
│   │   ├── config.py           # pydantic-settings Settings + get_settings()
│   │   ├── errors.py           # ApiError + exception handlers → standard envelope
│   │   └── schemas.py          # CamelModel (snake_case Python → camelCase JSON)
│   ├── db/
│   │   ├── base.py             # DeclarativeBase
│   │   ├── models.py           # User, Profile, RefreshToken, Progress
│   │   ├── session.py          # async engine, SessionLocal, get_db dependency
│   │   └── __init__.py
│   ├── api/
│   │   ├── deps.py             # get_current_user (Bearer access JWT)
│   │   └── router.py           # aggregates module routers under /api/v1
│   └── modules/
│       ├── health/             # GET /health
│       ├── auth/               # register/login/refresh/logout + security.py
│       ├── users/              # own profile/settings/password
│       ├── progress/           # GET /progress/me
│       ├── catalog/            # courses and lessons
│       ├── exercises/          # grading, XP and completion
│       ├── vocabulary/         # personal words and basic reviews
│       ├── gamification/       # activity, streaks and achievements
│       ├── password_reset/     # reset tokens and SMTP
│       └── ai/                 # OpenRouter, history, recommendations and SSE
├── alembic/
│   ├── env.py                  # async migrations; URL from app settings
│   ├── script.py.mako
│   └── versions/               # 20261004_1200_init, 20261005_1000_auth_progress
├── tests/                      # pytest (health, auth, users, progress)
├── alembic.ini
└── pyproject.toml
```

### Module internal structure

```
modules/<name>/
├── router.py       # HTTP only
├── service.py      # business rules, transaction boundaries
├── schemas.py      # Pydantic request/response models
└── security.py     # (auth only) password hashing, JWT, refresh token helpers
```

## 3. Request lifecycle

```
HTTP request
 → CORS middleware (origins from settings)
 → FastAPI routing (/api/v1)
 → dependency injection (get_db, get_current_user)
 → router (thin) → service (business logic)
 → SQLAlchemy async session → aiosqlite / asyncpg → SQLite / PostgreSQL
 → response_model serialization (camelCase)
 → exception handlers on error → standard JSON envelope
```

## 4. Cross-cutting concerns

- **Configuration** — `app/core/config.py` uses `pydantic-settings`; values come
  from the environment / root `.env`. Feature modules receive a `Settings`
  instance via `Depends(get_settings)`; there are no scattered `os.environ` reads.
  `DATABASE_URL` accepts plain `postgresql://` and is normalized to the asyncpg
  driver. Production refuses to start with the development `JWT_ACCESS_SECRET`.
- **Validation** — FastAPI validates request models automatically with Pydantic.
  Invalid requests return `422` in the standard envelope (code
  `VALIDATION_FAILED`).
- **Errors** — `app/core/errors.py` maps exceptions to the envelope in
  `docs/api.md`. `ApiError` carries an explicit `code` (e.g. `INVALID_CREDENTIALS`,
  `EMAIL_TAKEN`); `HTTPException` maps by status; `RequestValidationError` → `422`;
  `SQLAlchemyError` and connection `OSError`s (asyncpg raises a raw
  `ConnectionRefusedError` when the database is unreachable) → `503
  DATABASE_UNAVAILABLE`; anything else → `500 INTERNAL_ERROR` (traceback logged
  server-side, never returned).
- **Database availability** — the async engine connects lazily, so the process
  starts even when PostgreSQL is down. `/health` reports `database: "down"` and
  data endpoints return `503`.
- **Logging** — Python's `logging` (uvicorn's logger). Structured logging and
  request correlation ids are deferred.
- **Auth** — `get_current_user` (`app/api/deps.py`) verifies a Bearer access JWT
  and loads the `User` with its `Profile`. Invalid/expired tokens return `401
  UNAUTHORIZED`. There is no development auth stub anymore.
- **Rate limiting** — persistent fixed windows for login/register, password reset and AI.
  Configuration and proxy trust: `docs/authentication.md`. Refresh throttling is deferred.

## 5. Authentication module

- `security.py` — argon2id password hashing (`argon2-cffi`), HS256 access JWTs
  (`pyjwt`), opaque refresh-token generation and SHA-256 hashing.
- `service.py` — `register_user`, `authenticate`, `create_session`,
  `rotate_session` (rotation + reuse detection), `revoke_session`.
- `router.py` — `POST /auth/register`, `/login`, `/refresh`, `/logout`. The raw
  refresh token is only ever sent in an HttpOnly, `SameSite`, path-scoped cookie
  (`/api/v1/auth`); it is never returned in the body.
- Refresh tokens are stored **hashed**; a revoked token presented again revokes
  every active token for that user.

Full design and threat notes: `docs/authentication.md` and `docs/security.md`.

## 6. HTTP conventions

- Global prefix `/api/v1` applied once when including the aggregate router.
- Routers return Pydantic models, never ORM objects directly.
- JSON uses camelCase via `CamelModel` (alias generator); Python stays snake_case.
- Errors use the envelope in `docs/api.md`.

## 7. Database access

- `app/db/session.py` exposes `get_db()` (an async session dependency) and the
  engine.
- Services take an `AsyncSession` and use SQLAlchemy 2.0 style selects.
- Migrations are managed by Alembic (`alembic/`); the URL comes from settings.
- Ownership is enforced by scoping queries to the authenticated `User.id`, never
  by trusting an id from the request body.

## 8. Testing

| Level | Tool | Scope |
| ----- | ---- | ----- |
| Unit / API | pytest + httpx ASGI client | routers, services, dependencies |
| Database-backed API | pytest + in-memory SQLite | auth, users, progress flows |

Current tests (`backend/tests/`):

- `test_health.py` — health reports database up/down and never fails.
- `test_auth.py` — register, duplicate email, hashing, login, wrong password,
  refresh rotation, reuse detection, logout, protected endpoints, cross-user
  isolation.
- `test_users.py` — `/users/me` is authenticated and read-only.
- `test_progress.py` — `/progress/me` requires auth and starts at zero.

Database access is provided through a SQLite fixture (see `tests/conftest.py`);
no PostgreSQL server is required. Integration tests against real PostgreSQL
remain on `plans/testing-plan.md`.

## 9. Conventions

- Routers are thin; services own rules.
- One service module per feature; no pass-through wrappers.
- Prefer explicit code over clever abstractions (`AGENTS.md` rules 2/9).
- No cross-module direct DB access that bypasses services.

## 10. Build & run

```bash
pnpm setup                 # create .venv and install dependencies
pnpm backend:dev           # uvicorn --reload on :3001
pnpm backend:lint          # ruff
pnpm backend:typecheck     # mypy
pnpm backend:test          # pytest
pnpm db:migrate            # alembic upgrade head
```

See `plans/backend-plan.md` for what comes next.

## Implemented learning and AI extensions (2026-10-18)

The modular FastAPI/SQLAlchemy architecture is unchanged. New modules follow
`router.py`, `service.py`, `schemas.py`:

- `vocabulary`: user-owned words, translation/example, optional published lesson,
  learned/review state, due queue and review history. Review scheduling is a
  simple 1-day retry / 7-day remembered policy, not a full SRS algorithm.
- `gamification`: one unique learning activity per learner/calendar day; current
  and longest streak; five deterministic achievements. Submissions and vocabulary
  reviews record activity. Merely opening a lesson does not earn a streak day.
- `password_reset`: hashed expiring one-use tokens, generic responses, persistent
  IP/email fixed-window limits, SMTP delivery and refresh-session revocation.
- `ai`: OpenRouter provider adapter, bounded tutor history, structured explanation
  and practice generation, deterministic learner recommendations, JSON and SSE.
- `users`: authenticated profile PATCH for display name, CEFR English level and
  preferred explanation language. Email editing is also supported. Numeric level, XP and identity stay
  outside this update surface.

Learning writes take a PostgreSQL `users` row lock or SQLite no-op write lock
before reading/updating progress/profile,
so concurrent requests cannot overwrite XP using stale profile objects. The
existing deterministic grading and once-only XP claim remain authoritative.
Activity and achievement writes participate in the same learning transaction.
Achievement definitions are migration-owned, with no client/AI award endpoint.
Thresholds: first lesson, seven-day longest streak, 100 XP, ten completed lessons,
and five saved words. Previously earned metrics are evaluated on the next
learning write; no historical streak days are invented during migration.

`LEARNING_TIMEZONE` is a server-wide IANA zone (default UTC). Dates are derived
from server time and cannot be supplied by clients. A streak remains current if
its last day was today or yesterday; it becomes zero after a missed day. Longest
streak is preserved. Changing this policy after collecting activity changes day
boundaries; plan an explicit data migration if changing timezone in production.

`core/limits.py` stores request windows in SQLite or PostgreSQL. AI quota reservations are
serialized per user and globally, and survive worker restarts. All API request
bodies are bounded before JSON parsing. Validation errors omit input values to
avoid reflecting credentials/reset tokens. Provider errors never expose upstream
bodies. Authenticated object access is scoped by the token's user ID.

Tests, PostgreSQL setup, safe demo seed and SMTP configuration:
[development.md](development.md). Provider protocol, limits and manual AI checks:
[ai.md](ai.md). Live PostgreSQL/AI verification remains blocked in the implementation
environment; offline SQL and mocked/ORM tests are distinct from live integration.

## Backend stabilization — 2026-10-28

Refresh rotation claims one unrevoked, unexpired token through conditional
`UPDATE ... RETURNING`; revocation, successor creation and linking share one
commit. A common learner lock serializes rotation/session issuance with password
changes/reset. SQLite uses a no-op UPDATE (preserving `updated_at`), PostgreSQL
uses `FOR UPDATE`; correctness never depends on SQLite supporting row locks.
The existing SQLite connection timeout remains bounded at 30 seconds, with no
retry loop. Logout also uses a conditional UPDATE.

Hash/verify/dummy-verify calls in async auth/password paths use the shared
four-worker AnyIO limiter. Hash parameters and credential semantics are unchanged;
there was no existing automatic rehash path to migrate.
The existing schema and Alembic chain are unchanged. See
[stabilization report](backend-stabilization-report.md) for runtime evidence.
