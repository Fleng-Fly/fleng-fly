# Backend

> Status: **M1 implemented**. Stack: Python 3.11+ / FastAPI / SQLAlchemy 2
> (async) / Alembic / Pydantic. Implemented modules: `health`, `users`
> (development-only auth stub). Auth, catalog, exercises, AI and the rest are
> not built yet.

## 1. Responsibilities

The backend is the only part of the system allowed to make decisions about data:
validation, authorization, business rules, persistence and (later) AI
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
│   │   ├── errors.py           # exception handlers → standard envelope
│   │   └── schemas.py          # CamelModel (snake_case Python → camelCase JSON)
│   ├── db/
│   │   ├── base.py             # DeclarativeBase
│   │   ├── models.py           # User, Profile
│   │   ├── session.py          # async engine, SessionLocal, get_db dependency
│   │   └── __init__.py
│   ├── api/
│   │   ├── deps.py             # get_current_user_id (DEV ONLY)
│   │   └── router.py           # aggregates module routers under /api/v1
│   └── modules/
│       ├── health/
│       │   ├── router.py       # GET /health
│       │   ├── schemas.py
│       │   └── service.py
│       └── users/
│           ├── router.py       # GET /users/me
│           ├── schemas.py
│           └── service.py
├── alembic/
│   ├── env.py                  # async migrations; URL from app settings
│   ├── script.py.mako
│   └── versions/20261004_1200_init.py
├── tests/                      # pytest (health, users)
├── alembic.ini
└── pyproject.toml
```

### Module internal structure

```
modules/<name>/
├── router.py       # HTTP only
├── service.py      # business rules, transaction boundaries
├── schemas.py      # Pydantic request/response models
└── ...
```

## 3. Request lifecycle

```
HTTP request
 → CORS middleware (origins from settings)
 → FastAPI routing (/api/v1)
 → dependency injection (get_db, get_current_user_id)
 → router (thin) → service (business logic)
 → SQLAlchemy async session → asyncpg → PostgreSQL
 → response_model serialization (camelCase)
 → exception handlers on error → standard JSON envelope
```

## 4. Cross-cutting concerns

- **Configuration** — `app/core/config.py` uses `pydantic-settings`; values come
  from the environment / root `.env`. Feature modules receive a `Settings`
  instance via `Depends(get_settings)`; there are no scattered `os.environ` reads.
  `DATABASE_URL` accepts plain `postgresql://` and is normalized to the asyncpg
  driver.
- **Validation** — FastAPI validates request models automatically with Pydantic.
  Invalid requests return `422` in the standard envelope (code
  `VALIDATION_FAILED`).
- **Errors** — `app/core/errors.py` maps exceptions to the envelope in
  `docs/api.md`: `HTTPException` → its status; `RequestValidationError` → `422`;
  `SQLAlchemyError` and connection `OSError`s (asyncpg raises a raw
  `ConnectionRefusedError` when the database is unreachable) → `503
  DATABASE_UNAVAILABLE`; anything else → `500 INTERNAL_ERROR` (traceback logged
  server-side, never returned).
- **Database availability** — the async engine connects lazily, so the process
  starts even when PostgreSQL is down. `/health` reports `database: "down"` and
  data endpoints return `503`.
- **Logging** — Python's `logging` (uvicorn's logger). Structured logging and
  request correlation ids are deferred.
- **Auth** — not implemented. `get_current_user_id` (in `app/api/deps.py`) is a
  development-only dependency that returns a fixed user id from `DEV_USER_ID`
  and raises `401` when `APP_ENV=production`. It is **not** authentication and
  must be replaced by a JWT dependency.
- **Rate limiting** — deferred (arrives with auth/AI).

## 5. HTTP conventions

- Global prefix `/api/v1` applied once when including the aggregate router.
- Routers return Pydantic models, never ORM objects directly.
- JSON uses camelCase via `CamelModel` (alias generator); Python stays snake_case.
- Errors use the envelope in `docs/api.md`.

## 6. Database access

- `app/db/session.py` exposes `get_db()` (an async session dependency) and the
  engine.
- Services take an `AsyncSession` and use SQLAlchemy 2.0 style selects.
- Migrations are managed by Alembic (`alembic/`); the URL comes from settings.

## 7. Testing

| Level | Tool | Scope |
| ----- | ---- | ----- |
| Unit / API | pytest + FastAPI TestClient | routers, services, dependencies |

Current tests (`backend/tests/`):

- `test_health.py` — health reports database up/down and never fails.
- `test_users.py` — `/users/me` returns a camelCase profile; production rejects
  the dev stub with a `401` envelope.

Database access is overridden through FastAPI dependency overrides, so tests run
without PostgreSQL.

## 8. Conventions

- Routers are thin; services own rules.
- One service module per feature; no pass-through wrappers.
- Prefer explicit code over clever abstractions (`AGENTS.md` rules 2/9).
- No cross-module direct DB access that bypasses services.

## 9. Build & run

```bash
pnpm setup                 # create .venv and install dependencies
pnpm backend:dev           # uvicorn --reload on :3001
pnpm backend:lint          # ruff
pnpm backend:typecheck     # mypy
pnpm backend:test          # pytest
pnpm db:migrate            # alembic upgrade head
```

See `plans/backend-plan.md` for what comes next.
