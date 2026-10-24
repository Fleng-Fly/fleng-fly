# Development

For local presentation preparation, use `npm run demo:prepare` followed by
`npm run dev`. The explicit preparation command applies SQLite migrations,
seeds the catalog and creates three fictional accounts through the existing
registration and grading services. It is allowed only with `APP_ENV=development`
or `APP_ENV=demo` and a SQLite `DATABASE_URL`; credentials are generated in
ignored `backend/data/demo-credentials.json`. See `DEMO.md` for the walkthrough.

> Status: **M2 + catalog read implemented** — static HTML/CSS/JS frontend served
> by the Python/FastAPI backend, local SQLite (optional PostgreSQL) via SQLAlchemy + Alembic,
> email/password authentication with progress storage, and a read-only
> course/lesson catalog, deterministic exercises/progress and backend AI extensions.
> Live PostgreSQL/OpenRouter validation remains pending.

## 1. Technology stack and rationale

| Area            | Choice                                                 | Why                                                            |
| --------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| Frontend        | Plain HTML5 + CSS3 + vanilla JavaScript (ES modules)   | Small, understandable, no build step                           |
| HTTP client     | Browser `fetch`                                        | Native; no dependency                                          |
| Static serving  | FastAPI `StaticFiles` (same origin as the API)         | One deployable; first-party cookies                            |
| Backend         | Python + FastAPI                                       | Async-first, typed via Pydantic, fast to build                 |
| ORM             | SQLAlchemy 2 (async) + aiosqlite / asyncpg             | Shared models and engine configuration                         |
| Migrations      | Alembic                                                | Standard SQLAlchemy migration tool                             |
| Database        | SQLite locally; PostgreSQL via DATABASE_URL            | No server for frontend development; deployment choice retained |
| Passwords       | argon2-cffi (argon2id)                                 | Memory-hard, current recommended hashing                       |
| Tokens          | PyJWT (access) + opaque hashed refresh tokens          | Simple, revocable sessions                                     |
| Backend tests   | pytest + httpx ASGI client (in-memory SQLite)          | Native to the stack; no server required                        |
| Backend quality | Ruff (lint + format), mypy                             | One fast linter/formatter; static type checks                  |
| Tooling         | venv (backend), Docker (database only), Node (scripts) | Reproducible local environment                                 |

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
├── ai/           # AI documentation entry point
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

- Node.js LTS (>= 20), with npm (pnpm scripts also remain available)
- Python (>= 3.11) with `venv`
- PostgreSQL is optional; SQLite is the local default
- Git

## 4. Getting started

```bash
git clone <repo>
cd fleng

npm run dev              # sets up a missing venv, prepares SQLite, starts FastAPI
```

Open http://localhost:3001. The UI is served at `/`; all API routes live under
http://localhost:3001/api/v1.

`npm run dev` runs `scripts/dev.mjs`: set up a missing venv, run `app.db.prepare`,
then start uvicorn. Local SQLite upgrades to Alembic head and gets demo content
only if the course catalog is empty. Failures stop startup. Existing users,
sessions and learning results are preserved. There is no separate frontend server.
Use `npm run db:migrate` or `npm run db:seed` explicitly when needed.

SQLite verification (2026-10-22): 129 pytest tests passed, with the opt-in live
PostgreSQL migration test skipped. Fresh-file preparation, repeated migration and
seeding, foreign keys, unique-email handling, HTTP auth/cookie rotation and lesson
XP/progress were checked. A full backend restart preserved the user, refresh
session, completed lesson, learned word and streak. Headless Firefox also checked
form login, Dashboard layouts at 360/768/1440 px, drawer/Escape/focus, profile menu,
search, navigation and logout. Exact Figma comparison remains unavailable.

## 5. Environment variables

Secrets live in `.env` (git-ignored). `.env.example` documents names with safe
placeholders. The backend loads `.env` from absolute backend/repository paths
(root file wins), then environment variables. Relative SQLite filenames always
resolve against `backend/`, even when Python runs from another directory.

| Variable                      | Used by | Default (development)                 | Purpose                                                                           |
| ----------------------------- | ------- | ------------------------------------- | --------------------------------------------------------------------------------- |
| `APP_ENV`                     | backend | `development`                         | Runtime mode; `production` requires real secrets and secure cookies               |
| `PORT`                        | backend | `3001`                                | API port (used by docs; uvicorn is started with `--port`)                         |
| `DATABASE_URL`                | backend | `sqlite+aiosqlite:///./data/fleng.db` | Local file, or PostgreSQL URL (normalized to asyncpg)                             |
| `CORS_ORIGIN`                 | backend | `http://localhost:3000`               | Extra allowed origin(s), comma-separated (the app's own origin is always trusted) |
| `FRONTEND_DIR`                | backend | repository `frontend/`                | Override the served static frontend directory                                     |
| `JWT_ACCESS_SECRET`           | backend | insecure dev value                    | Access-token signing secret; **required in production**                           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | `15`                                  | Access-token lifetime                                                             |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | backend | `30`                                  | Refresh-token/session lifetime                                                    |
| `COOKIE_SECURE`               | backend | derived (`production`)                | Force the refresh cookie's `Secure` flag                                          |
| `COOKIE_SAMESITE`             | backend | `lax`                                 | Refresh cookie `SameSite` policy                                                  |

`DATABASE_URL` is required in production; in development it falls back to the
docker-compose connection so `pnpm dev` works out of the box. The frontend has no
environment configuration of its own: it is served from the same origin as the
API and calls the relative `/api/v1`. No secrets are exposed to the browser.

## 6. Scripts

| Script            | Effect                                                  |
| ----------------- | ------------------------------------------------------- |
| `pnpm setup`      | Create the backend venv and install dependencies        |
| `pnpm dev`        | Run FastAPI (serves the API and the static frontend)    |
| `pnpm lint`       | Ruff (backend)                                          |
| `pnpm typecheck`  | mypy (backend)                                          |
| `pnpm test`       | pytest (backend)                                        |
| `pnpm format`     | Prettier (HTML/CSS/JS/Markdown) + Ruff format (backend) |
| `pnpm db:migrate` | `alembic upgrade head`                                  |
| `pnpm db:seed`    | Insert/update the demo catalog (idempotent)             |
| `pnpm db:sql`     | Emit migration SQL offline (no database needed)         |

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
- `npm run db:migrate` applies migrations using the configured SQLite or PostgreSQL database.
- `npm run db:prepare` prepares local SQLite; dev calls it before serving HTTP.
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
- **Auth/register returns 503, `/health` says `db down`** — check DATABASE_URL,
  file permissions and migrations. For an explicit PostgreSQL URL, start that
  server and apply migrations; local SQLite requires no database service.
- **`/users/me` returns 401** — no/invalid Bearer access token; sign in at
  `/login` first.
- **pnpm blocks build scripts** — `pnpm-workspace.yaml` lists `allowBuilds`; keep
  it minimal.
- **Port already in use** — stop the previous Fleng server or set PORT before dev.

## Backend completion: reproducible PostgreSQL setup

PostgreSQL is an optional explicit DATABASE_URL configuration; the local default
is SQLite. There is no automatic fallback between databases. Existing
databases/volumes must be kept; never use `compose down -v`
or downgrade migrations as a setup fix.

From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e './backend[dev]'
# Create .env from .env.example only if you do not already have one.
docker compose up -d --wait db
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python ../scripts/check-db.py
.venv/bin/python -m app.db.seed
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload
```

Compose binds PostgreSQL 16 to loopback. `POSTGRES_PORT` changes the host port
(default 5432); also update `DATABASE_URL` to match. The named volume is retained.
Changing POSTGRES_USER/PASSWORD does not change credentials in an already
initialized volume; use its existing credentials or an explicit administrator-led
credential change. Do not delete the volume to fix credentials.

### Native alternative (no Docker)

Install PostgreSQL 16+ with your operating system package manager and start its
local service. For Debian/Ubuntu this is typically:

```bash
sudo apt install postgresql postgresql-client
sudo systemctl enable --now postgresql
sudo -u postgres createuser --pwprompt fleng
sudo -u postgres createdb --owner=fleng fleng
pg_isready -h 127.0.0.1 -p 5432
```

Use these creation commands only for a new role/database. For an existing setup,
use the existing role/database and credentials. `--pwprompt` avoids putting the
password in shell history. Set root `.env`:

```dotenv
DATABASE_URL=postgresql+asyncpg://fleng:<URL-encoded-password>@127.0.0.1:5432/fleng
```

Then run the same Alembic, check, seed and uvicorn commands above. On other
systems use their PostgreSQL service tooling. TCP authentication must allow the
application role; do not weaken authentication to `trust` as a workaround.

The seed is idempotent and updates only the small demo catalog matched by slugs
(courses, lessons, exercises). It never changes accounts/progress; it can update
seed-owned content in place, so use a development database. CLI seeding refuses
`APP_ENV=production`. It does not run automatically on startup.

### Database and migration checks

```bash
cd backend
.venv/bin/alembic heads
.venv/bin/alembic history
.venv/bin/alembic upgrade head --sql > /tmp/fleng-migrations.sql
.venv/bin/python ../scripts/check-db.py
```

There is one head, `20261018_1200`, extending `20261011_1400`. Do not stamp a
revision without applying its migration. Offline SQL validates compilation only;
it does not prove live database integration.

The suite uses SQLite in-memory ORM fixtures by default. To exercise registration,
authentication, catalog, XP, progress and new modules against real PostgreSQL,
point `TEST_DATABASE_URL` to a PostgreSQL test database and run:

```bash
cd backend
TEST_DATABASE_URL='postgresql+asyncpg://fleng:<password>@127.0.0.1:5432/fleng_test' .venv/bin/pytest -q
```

Create `fleng_test` beforehand, owned by the test role. Tests create unique
`fleng_test_*` / `fleng_migration_*` schemas and remove only those schemas.
The migration test applies the entire chain in its isolated schema and checks
ORM drift. The role needs CREATE schema privilege. Do not use production for tests.
Without TEST_DATABASE_URL the PostgreSQL migration test is explicitly skipped.

Execution-environment result (2026-10-18): Docker/psql/pg_isready were absent;
local IPv4/IPv6 port 5432 refused connections. `alembic upgrade head` failed
before applying migrations. No PostgreSQL data was changed. Offline migration SQL
and mocked/database-independent tests were run; a successful live integration is
still required once PostgreSQL is available.

### Password reset email

`RESET_DELIVERY=smtp` enables SMTP; configure SMTP_HOST/PORT/USERNAME/PASSWORD/FROM,
SMTP_STARTTLS and RESET_URL for a real password-reset UI. Production requires a
trusted HTTPS RESET_URL and authenticated encrypted SMTP. No reset UI is added
by this backend task; the API is callable via Swagger or your own UI.

For safe development use a local-only SMTP capture inbox, with its host/port and
`SMTP_STARTTLS=false` if required. Tokens appear only in that mailbox, never in
HTTP responses or logs. Automated tests inject the delivery function and inspect
captured tokens in memory. `disabled` sends no email and never exposes a debug
reset token. Delivery failures retain the generic response and invalidate that
token. Monitor SMTP health externally. Old access JWTs last until their existing
short expiry; reset revokes refresh sessions and all other unused reset tokens.

OpenRouter configuration and manual testing: [ai.md](ai.md).

### Existing native PostgreSQL on Arch Linux

For an already installed/running local server, do not reinstall, run initdb, remove
its data directory, recreate databases, or enable autostart. Fleng's native target
for this setup is role `fleng`, database `fleng_db`, TCP `127.0.0.1:5432`, using
SQLAlchemy's `postgresql+asyncpg` driver.

Run this from your own terminal so sudo and database password prompts remain
interactive with echo disabled:

```bash
cd /home/kr1m12/Desktop/fleng
backend/.venv/bin/python scripts/setup-local-postgres.py
```

The helper uses `scripts/setup-local-postgres.sql` to create only missing Fleng
resources, refuses an unexpectedly privileged existing application role or a
database owned by another role, and uses psql's `\password` with SCRAM encryption.
It verifies both successful TCP login and rejection of a wrong password before
saving only DATABASE_URL in the ignored root `.env` with permissions 0600. Other
environment keys are preserved. Existing exported DATABASE_URL or a different
configured database cause a stop for review. Never share passwords in chat.

No system-wide PostgreSQL configuration is changed. If the wrong-password check
succeeds (for example an existing `trust` rule), stop and review a scoped
`pg_hba.conf` change before applying it; modifying that file requires explicit
permission. The helper also prints authentication-rule metadata without password
hashes. After successful setup use the existing migrate/check/seed commands above.

The PostgreSQL tests create unique temporary schemas. Their cleanup drops only
those schemas; get explicit approval before running that cleanup when required.
The existing public application schema is never used as test-fixture scratch data.
