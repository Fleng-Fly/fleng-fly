# Development

> Status: **M2 implemented** — pnpm workspace (frontend), Python/FastAPI backend,
> PostgreSQL via SQLAlchemy + Alembic, and email/password authentication with
> progress storage. Catalog and AI are not implemented yet.

## 1. Technology stack and rationale

| Area            | Choice                                                | Why |
| --------------- | ----------------------------------------------------- | --- |
| Frontend        | Next.js (App Router) + TypeScript                     | Routing, SSR/RSC, good DX; matches SEO + app needs |
| Styling         | Tailwind CSS v4 (`@theme` tokens)                     | Token-driven design system matching `design/` |
| Animation       | Framer Motion                                         | Declarative, restrained motion (used sparingly) |
| Server state    | TanStack Query                                        | Caching, retries, request de-duplication |
| Backend         | Python + FastAPI                                      | Async-first, typed via Pydantic, fast to build |
| ORM             | SQLAlchemy 2 (async) + asyncpg                        | Mature async SQL toolkit; explicit models |
| Migrations      | Alembic                                               | Standard SQLAlchemy migration tool |
| Database        | PostgreSQL                                            | Relational integrity + JSONB flexibility |
| Passwords       | argon2-cffi (argon2id)                                | Memory-hard, current recommended hashing |
| Tokens          | PyJWT (access) + opaque hashed refresh tokens         | Simple, revocable sessions |
| Backend tests   | pytest + httpx ASGI client (in-memory SQLite)         | Native to the stack; no server required |
| Backend quality | Ruff (lint + format), mypy                            | One fast linter/formatter; static type checks |
| Frontend tests  | Vitest                                                | Light; no DOM needed for API-client tests |
| Tooling         | pnpm (frontend), venv (backend), Docker (database only) | Reproducible local environment |

### Rejected for now (deliberately not added)

- **Turborepo / Nx** — root Node scripts orchestrate the two packages fine.
- **Microservices / message broker** — no proven need; adds operational cost.
- **Redis** — introduce only when caching/multi-instance rate limiting requires it.
- **GraphQL** — REST is sufficient for the resource model.
- **An async task queue (Celery/ARQ)** — not needed until background jobs exist.
- **A Node.js backend framework (NestJS/Express)** — the backend is Python +
  FastAPI; TypeScript is used only on the frontend and the backend must not
  depend on Node.

Adding any of these requires a written justification in the relevant plan.

## 2. Repository layout

```
/
├── frontend/     # @fleng/frontend — Next.js app (pnpm workspace member)
├── backend/      # FastAPI app (Python, own virtualenv)
│   ├── app/      # application package
│   ├── alembic/  # migrations
│   ├── tests/    # pytest
│   └── pyproject.toml
├── ai/           # future Python AI layer (docs only)
├── docs/ plans/ design/ project-map/
├── scripts/      # setup.mjs, dev.mjs (root orchestration)
├── package.json          # root scripts (private)
├── pnpm-workspace.yaml   # frontend workspace + allowed build scripts
├── docker-compose.yml    # local PostgreSQL
└── .env.example
```

The backend is **not** a pnpm workspace member: it is a Python project managed by
pip inside `backend/.venv`. Root Node scripts (`scripts/`) start both dev servers.

## 3. Prerequisites

- Node.js LTS (>= 20) and pnpm (>= 9)
- Python (>= 3.11) with `venv`
- PostgreSQL — via `docker compose up -d db`, or your own instance
- Git

## 4. Getting started

```bash
git clone <repo>
cd fleng

pnpm install              # frontend dependencies
pnpm setup                # create backend/.venv + install Python deps

docker compose up -d db   # or set DATABASE_URL to an existing database
cp .env.example .env      # optional in development (defaults exist)
pnpm db:migrate           # apply Alembic migrations

pnpm dev                  # frontend :3000, backend :3001
```

Open http://localhost:3000. All API routes live under http://localhost:3001/api/v1.

`pnpm dev` runs `scripts/dev.mjs`, which runs the backend setup automatically if
`.venv` is missing, then starts uvicorn and Next.js together.

If PostgreSQL is not running, the stack still starts: the frontend shows
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
| `CORS_ORIGIN`         | backend  | `http://localhost:3000` | Allowed frontend origin(s), comma-separated |
| `JWT_ACCESS_SECRET`   | backend  | insecure dev value    | Access-token signing secret; **required in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | `15`         | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | backend | `30`         | Refresh-token/session lifetime |
| `COOKIE_SECURE`       | backend  | derived (`production`) | Force the refresh cookie's `Secure` flag |
| `COOKIE_SAMESITE`     | backend  | `lax`                 | Refresh cookie `SameSite` policy |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:3001/api/v1` | API base URL (public) |

`DATABASE_URL` is required in production; in development it falls back to the
docker-compose connection so `pnpm dev` works out of the box. Never expose
secrets to the frontend — only `NEXT_PUBLIC_*` values ship to the browser. Next.js
reads its env from `frontend/.env.local` (git-ignored); the app has a working
default.

## 6. Scripts

| Script             | Effect |
| ------------------ | ------ |
| `pnpm setup`       | Create the backend venv and install dependencies |
| `pnpm dev`         | Run FastAPI + Next.js together (auto-setup if needed) |
| `pnpm build`       | Build the frontend |
| `pnpm lint`        | ESLint (frontend) + Ruff (backend) |
| `pnpm typecheck`   | `tsc` (frontend) + mypy (backend) |
| `pnpm test`        | Vitest (frontend) + pytest (backend) |
| `pnpm format`      | Prettier (frontend) + Ruff format (backend) |
| `pnpm db:migrate`  | `alembic upgrade head` |
| `pnpm db:sql`      | Emit migration SQL offline (no database needed) |

Package-level commands:

```bash
pnpm backend:dev        # uvicorn --reload
pnpm backend:lint       # ruff check
pnpm backend:typecheck  # mypy
pnpm backend:test       # pytest
pnpm --filter @fleng/frontend dev
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

- Frontend: TypeScript `strict`; Prettier + ESLint; no `fetch` outside
  `frontend/src/lib/api`; server components by default.
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
