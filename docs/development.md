# Development

> Status: **M2 + catalog read implemented** — static HTML/CSS/JS frontend served
> by the Python/FastAPI backend, PostgreSQL via SQLAlchemy + Alembic,
> email/password authentication with progress storage, and a read-only
> course/lesson catalog. Exercises, progress writes and AI are not implemented
> yet.

## 1. Technology stack and rationale

| Area            | Choice                                                | Why |
| --------------- | ----------------------------------------------------- | --- |
| Frontend        | Plain HTML5 + CSS3 + vanilla JavaScript (ES modules)  | Small, understandable, no build step |
| HTTP client     | Browser `fetch`                                      | Native; no dependency |
| Static serving  | FastAPI `StaticFiles` (same origin as the API)        | One deployable; first-party cookies |
| Backend         | Python + FastAPI                                      | Async-first, typed via Pydantic, fast to build |
| ORM             | SQLAlchemy 2 (async) + asyncpg                        | Mature async SQL toolkit; explicit models |
| Migrations      | Alembic                                               | Standard SQLAlchemy migration tool |
| Database        | PostgreSQL                                            | Relational integrity + JSONB flexibility |
| Passwords       | argon2-cffi (argon2id)                                | Memory-hard, current recommended hashing |
| Tokens          | PyJWT (access) + opaque hashed refresh tokens         | Simple, revocable sessions |
| Backend tests   | pytest + httpx ASGI client (in-memory SQLite)         | Native to the stack; no server required |
| Backend quality | Ruff (lint + format), mypy                            | One fast linter/formatter; static type checks |
| Tooling         | venv (backend), Docker (database only), Node (scripts) | Reproducible local environment |

### Rejected for now (deliberately not added)

- **A frontend framework (Next.js / React / Vue / Angular) or a build system** —
  the UI is plain HTML/CSS/JS served by FastAPI. A framework and a Node build
  step were removed deliberately; do not reintroduce them.
- **Tailwind / UI component libraries** — shared styles live in one hand-written
  stylesheet (`frontend/css/app.css`) with CSS custom-property tokens.
- **A JS state manager / query library** — the API client and page scripts are
  small; no cache layer is needed.
- **Turborepo / Nx** — root Node scripts orchestrate the repo fine.
- **Microservices / message broker** — no proven need; adds operational cost.
- **Redis** — introduce only when caching/multi-instance rate limiting requires it.
- **GraphQL** — REST is sufficient for the resource model.
- **An async task queue (Celery/ARQ)** — not needed until background jobs exist.
- **A Node.js backend framework (NestJS/Express)** — the backend is Python +
  FastAPI and must not depend on Node.

Adding any of these requires a written justification in the relevant plan.

## 2. Repository layout

```
/
├── frontend/     # static HTML/CSS/JS UI (served by FastAPI; no build step)
├── backend/      # FastAPI app (Python, own virtualenv) + static serving
│   ├── app/      # application package
│   ├── alembic/  # migrations
│   ├── tests/    # pytest
│   └── pyproject.toml
├── ai/           # future Python AI layer (docs only)
├── docs/ plans/ design/ project-map/
├── scripts/      # setup.mjs, dev.mjs (root orchestration)
├── package.json          # root scripts (private)
├── docker-compose.yml    # local PostgreSQL
└── .env.example
```

The backend is a Python project managed by pip inside `backend/.venv` and is
started by the root Node scripts (`scripts/`). It also serves the static
frontend, so there is a single server to run.

## 3. Prerequisites

- Node.js LTS (>= 20) and pnpm (>= 9)
- Python (>= 3.11) with `venv`
- PostgreSQL — via `docker compose up -d db`, or your own instance
- Git

## 4. Getting started

```bash
git clone <repo>
cd fleng

pnpm setup                # create backend/.venv + install Python deps

docker compose up -d db   # or set DATABASE_URL to an existing database
cp .env.example .env      # optional in development (defaults exist)
pnpm db:migrate           # apply Alembic migrations
pnpm db:seed              # load the demo courses and lessons (idempotent)

pnpm dev                  # FastAPI on :3001 (serves the API and the frontend)
```

Open http://localhost:3001. The UI is served at `/`; all API routes live under
http://localhost:3001/api/v1.

`pnpm dev` runs `scripts/dev.mjs`, which runs the backend setup automatically if
`.venv` is missing, then starts uvicorn. There is no separate frontend server.

If PostgreSQL is not running, the app still starts: the landing page shows
`Backend ● Online` with `db down`, unauthenticated requests return `401`, and
auth/registration requests return `503`.

## 5. Environment variables

Secrets live in `.env` (git-ignored). `.env.example` documents names with safe
placeholders. The backend loads `.env` from `backend/` or the repository root.

| Variable              | Used by  | Default (development) | Purpose |
| --------------------- | -------- | --------------------- | ------- |
| `APP_ENV`             | backend  | `development`         | Runtime mode; `production` requires real secrets and secure cookies |
| `PORT`                | backend  | `3001`                | API port (used by docs; uvicorn is started with `--port`) |
| `DATABASE_URL`        | backend  | local compose URL     | PostgreSQL connection (plain `postgresql://` is normalized to asyncpg) |
| `CORS_ORIGIN`         | backend  | `http://localhost:3000` | Extra allowed origin(s), comma-separated (the app's own origin is always trusted) |
| `FRONTEND_DIR`        | backend  | repository `frontend/` | Override the served static frontend directory |
| `JWT_ACCESS_SECRET`   | backend  | insecure dev value    | Access-token signing secret; **required in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | `15`         | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | backend | `30`         | Refresh-token/session lifetime |
| `COOKIE_SECURE`       | backend  | derived (`production`) | Force the refresh cookie's `Secure` flag |
| `COOKIE_SAMESITE`     | backend  | `lax`                 | Refresh cookie `SameSite` policy |

`DATABASE_URL` is required in production; in development it falls back to the
docker-compose connection so `pnpm dev` works out of the box. The frontend has no
environment configuration of its own: it is served from the same origin as the
API and calls the relative `/api/v1`. No secrets are exposed to the browser.

## 6. Scripts

| Script             | Effect |
| ------------------ | ------ |
| `pnpm setup`       | Create the backend venv and install dependencies |
| `pnpm dev`         | Run FastAPI (serves the API and the static frontend) |
| `pnpm lint`        | Ruff (backend) |
| `pnpm typecheck`   | mypy (backend) |
| `pnpm test`        | pytest (backend) |
| `pnpm format`      | Prettier (HTML/CSS/JS/Markdown) + Ruff format (backend) |
| `pnpm db:migrate`  | `alembic upgrade head` |
| `pnpm db:seed`     | Insert/update the demo catalog (idempotent) |
| `pnpm db:sql`      | Emit migration SQL offline (no database needed) |

Package-level commands:

```bash
pnpm backend:dev        # uvicorn --reload (API + static frontend on :3001)
pnpm backend:lint       # ruff check
pnpm backend:typecheck  # mypy
pnpm backend:test       # pytest
```

## 7. Database workflow

- Models: `backend/app/db/models.py`.
- Migrations: `backend/alembic/versions/` (committed).
- `pnpm db:migrate` applies migrations; requires a running PostgreSQL.
- After changing models, create a migration:
  `cd backend && .venv/bin/alembic revision --autogenerate -m "message"`
  (autogenerate needs a database to compare against).
- `pnpm db:sql` prints the SQL for all migrations without connecting.

## 8. Code conventions

- Frontend: plain ES-module JavaScript; no `fetch` outside `frontend/js/api.js`;
  render untrusted text with `textContent` (never `innerHTML`); no tokens in
  `localStorage`/`sessionStorage`.
- Backend: Python type hints everywhere; Ruff enforces import order and common
  bugs; mypy checks types. Pydantic models at every boundary; services own rules;
  routers stay thin. JSON is camelCase via `CamelModel`.
- Commit messages: `type: summary` (`chore`, `docs`, `feat`, `fix`, `refactor`,
  `test`). One logical change per commit.
- Never commit `.env`, secrets, `node_modules`, `.venv`, generated clients or
  build output.

## 9. Troubleshooting

- **Backend import errors** — run `pnpm setup` (or ensure `backend/.venv`
  exists) and run commands from `backend/`.
- **Auth/register returns 503, `/health` says `db down`** — PostgreSQL is not
  running or `DATABASE_URL` is wrong; run `docker compose up -d db` and
  `pnpm db:migrate`.
- **`/users/me` returns 401** — no/invalid Bearer access token; sign in at
  `/login` first.
- **pnpm blocks build scripts** — `pnpm-workspace.yaml` lists `allowBuilds`; keep
  it minimal.
- **Port already in use** — uvicorn uses `3001`, Next uses `3000`; change the
  ports in the scripts.
