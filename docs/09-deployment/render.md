# Render

Repository-compatible settings: Python runtime, repository root, build `python -m pip install ./backend`, start `cd backend && python run.py`, readiness /api/v1/health/ready. Retain frontend/backend/migrations. Host supplies PORT; set production secrets/settings privately.

run.py prepares file-backed SQLite before binding one worker. PostgreSQL needs explicit Alembic release migrations from backend/. Direct Uvicorn bypasses preparation. Configure exact CORS_ORIGIN; validated platform RENDER_EXTERNAL_URL joins it. TRUSTED_PROXY_IPS must reflect actual ingress knowledge, not wildcard guesses.

Ephemeral SQLite is a demo choice and can lose all accounts/progress on storage replacement. Same-file process restart proves no host durability. Durable SQLite requires an explicit persistent volume/single instance; external PostgreSQL still requires backup/restore/TLS validation.

No deployment/host configuration changed here. [Troubleshooting](troubleshooting.md) links historical diagnoses without asserting today's cause.

[Section index](README.md) · [Documentation home](../README.md)

## SQLite catalog bootstrap — 2026-11-14

For `DATABASE_URL=sqlite+aiosqlite:///./data/fleng.db`, start with
`cd backend && python run.py` (or `python run.py` when the Render root directory
is backend). The launcher creates the database, applies Alembic, initializes an
empty legacy catalog and idempotently imports the five packaged A0–B2 drafts.
A fresh database contains seven courses, 50 draft lessons and 500 course words.
Existing users, XP/progress, sessions and legacy content are preserved. No private
local database, password hashes, account data or credentials are bundled in Git.
No SSH/file upload is needed to recreate the curriculum catalog.

This is catalog initialization, not a transfer of local accounts/history. Five
A0–B2 courses stay unpublished; the normal public API still exposes only published
content. Publishing them requires separate editorial/release authorization.
PostgreSQL startup remains unchanged and does not migrate/import automatically.

Render's default filesystem is ephemeral: this bootstraps content after storage
replacement but cannot recover accounts/progress lost with that filesystem. A
persistent disk or managed database and backups are still required for durable
user data. With a disk mounted at /var/data, use the separately configured absolute
SQLite path; changing an occupied service's path does not transfer existing data.

Local verification for this change: backend pytest **406 passed / 18 skipped**;
fresh production-mode SQLite startup, hidden draft routes, registration/XP and
restart persistence pass. Local dev preparation was also run twice on an isolated
file: seven courses, 50 draft lessons, 500 words, zero bundled accounts and no new
rows on rerun. Ruff, mypy, frontend Node tests and Markdown links pass. Live Render
deployment and PostgreSQL integration are not claimed by these local checks.
