# backend/

API and business logic of Fleng. Built with **Python + FastAPI**.

## Stack

- **FastAPI** + Pydantic for HTTP, validation and OpenAPI.
- **SQLAlchemy 2 (async)** + **asyncpg** for PostgreSQL.
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
pnpm setup            # from the repo root: creates .venv + installs deps
pnpm backend:dev      # uvicorn --reload on :3001
```

Or directly:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
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

> The development auth dependency (`app/api/deps.py`) is a stub, not
> authentication, and refuses to run when `APP_ENV=production`.
