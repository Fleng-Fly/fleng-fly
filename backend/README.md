# backend/

API and business logic of Fleng. Built with **Python + FastAPI**.

## Stack

- **FastAPI** + Pydantic for HTTP, validation and OpenAPI.
- **SQLAlchemy 2 (async)** + **aiosqlite** locally; **asyncpg** for PostgreSQL.
- **Alembic** for migrations.
- **pydantic-settings** for configuration.
- **pytest** for tests; **Ruff** + **mypy** for quality.

## Layout

```
app/
├── main.py          # create_app: CORS, error handlers, /api/v1 router
├── core/            # config, error handlers, shared schemas
├── db/              # SQLAlchemy base, models, async session
├── api/             # aggregate router + dependencies (dev auth stub)
└── modules/         # health/, users/
alembic/             # migrations
tests/               # pytest
pyproject.toml
```

## Setup

```bash
npm run dev          # from repo root: prepares SQLite and starts the site on :3001
```

Or directly:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m app.db.prepare
.venv/bin/uvicorn app.main:app --reload --port 3001
```

## Quality gates

```bash
pnpm backend:lint       # ruff check
pnpm backend:typecheck  # mypy app
pnpm backend:test       # pytest
```

## Where to look

- Docs: `docs/backend.md`, `docs/database.md`, `docs/api.md`, `docs/security.md`
- Plan: `plans/backend-plan.md`

SQLite defaults to `backend/data/fleng.db` and persists across restarts. Explicit
PostgreSQL DATABASE_URL configurations require their own server and migrations.
Authentication uses access JWTs and rotating HttpOnly refresh cookies in both modes.
