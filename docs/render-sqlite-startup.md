# Render SQLite startup verification — 2026-11-04

## Diagnosis and evidence

The production launcher previously called Uvicorn directly. FastAPI lifespan did
not prepare the database, while `app.db.prepare.main` explicitly skipped all
production environments. SQLite creates a new empty file when first connected;
no Alembic tables were created by production startup. Both auth endpoints first
write to `request_limits`, so an empty disk produces
`sqlite3.OperationalError: no such table: request_limits`, mapped by the existing
handler to HTTP 503. `SELECT 1` readiness can still succeed on that empty file.

Reproduced using APP_ENV=production, an isolated writable SQLite file and the
unchanged ASGI entry point without preparation: register and login both returned
503, with the underlying missing-table exception inspected directly. The path
was correct and writable. Configuration already resolves relative paths against
backend/, session setup creates parents and registers foreign keys/now(), and
Alembic already shares that engine and has head `20261101_1200`. Those parts
needed no change, nor did any existing migration.

This establishes the repository startup defect and an exact local reproduction.
Only the generic OperationalError and reported production SQLite use were
provided for the live service; its actual tables, revision, filesystem permissions
and resolved path could not be inspected. No Render connector or browser session
was available. Live causation remains to be confirmed against detailed logs;
unable-to-open/read-only/locked-database errors are different possible causes.
No secret values or existing application DB rows were printed.

## Fix

`backend/run.py` calls the existing preparation entry point once, before
`uvicorn.run(..., workers=1)`. It never migrates in worker imports or lifespan.
Preparation now permits production file-backed SQLite, probes actual directory
and file write access using transactional DDL followed by rollback, applies
`alembic upgrade head`, checks every mapped table/column, and calls the existing
`seed_catalog` only if the catalog is empty. The probe leaves no table behind.
The seed creates learning content only, with no demo users; existing catalog
edits, accounts, sessions and progress survive repeated preparation.

Errors terminate startup with exit code 1; the HTTP error handler is unchanged.
Launcher diagnostics show phase, exception class and SQLite error code, without
printing SQL parameters or connection credentials. Missing schema despite an
incorrect head stamp fails explicitly rather than dropping/stamping/resetting it.
There is no `drop_all`, database deletion, fallback or fake successful auth.
PostgreSQL URLs/asyncpg and explicit release migrations remain supported.
Run one launcher/instance for a SQLite file; shared-file multi-instance migration
coordination is outside this supported deployment topology.

## Verification

Targeted regression suite: **13 passed**. It includes real launcher subprocesses
from a different working directory, a fresh production file migrated to head,
nonempty catalog, register 201, login/refresh 200, Secure refresh cookie, Dashboard
HTML and profile/progress/streak/vocabulary APIs, XP earned via an exercise, then
process termination and a second launch with the same file. Account ID, rotated
refresh session, progress/XP, catalog counts and custom catalog title persisted.
Invalid path, read-only file/directory, memory DB and a falsely stamped empty DB
all stop before serving HTTP. PostgreSQL launcher regression confirms it does not
migrate or seed automatically and passes workers=1 to Uvicorn.

The existing stabilization smoke also passed: development preparation, auth
rotation/reuse/password/logout, Dashboard and Lessons, once-only XP, persistence
on restart, production launcher/readiness/static pages/Secure cookie/origin guard.
Secure cookies were supplied explicitly over local HTTP in tests; actual browser
HTTPS/proxy behavior is not established by that transport.

Full backend suite: **236 passed, 15 skipped**, with the existing
Starlette/httpx deprecation warning. PostgreSQL integration tests skip without
TEST_DATABASE_URL. Ruff passed for app/tests/launcher; mypy passed for 65 source
files including the launcher; `git diff --check` passed. Alembic has one head
(`20261101_1200`), and the entire PostgreSQL upgrade chain compiles offline. SQLite preparation tests
also run `alembic check` with no schema drift. SQLite execution hangs in this
restricted sandbox (previously documented in docs/testing.md), so DB tests and
smoke ran outside it against temporary databases.

Separate self-review checked startup ordering, engine disposal across event
loops, rollback/no probe artifacts, migration/seed idempotence, existing data
preservation, no worker migration hooks, error redaction, PostgreSQL branching,
API compatibility, test isolation and deployment/doc consistency.

## Deployment and remaining limits

Use repository root as Render Root Directory, Build Command
`python -m pip install ./backend`, Start Command `cd backend && python run.py` and
Health Check Path `/api/v1/health/ready`. Production env reference and exact
settings are in [deployment.md](deployment.md#free-render-sqlite-configuration).
Do not launch Uvicorn directly or depend only on build-time SQLite preparation.
No push, live environment mutation or deployment was performed.

Render's [free service documentation](https://render.com/docs/free) specifies
that SQLite files are lost on service restart, redeploy or spin-down. A process
restart retaining the same file is distinct from a Render service restart.
This fix prepares a replacement disk; it cannot recover deleted accounts or
progress. Persistent data requires durable storage, preferably external
PostgreSQL. Live PostgreSQL, Render filesystem/configuration and public HTTPS
registration/login/refresh/Dashboard remain unverified without external access.
