# Render registration 503: follow-up diagnosis — 2026-11-04

## Established facts and limits

The starting commit for this investigation is `2850e6c`. It already calls SQLite
preparation before Uvicorn, runs Alembic online through `app.db.session.engine`,
checks every mapped table/column and probes real writes using rolled-back DDL.
Settings resolve relative SQLite paths against `backend/`, independently of cwd.
The API and Alembic both use the cached Settings and the same engine. No second
migration URL, missing migration or registration defect was found in that path.

A fresh local production launch successfully registers a user (201), rotates a
session and preserves accounts/progress on process restart. The schema has 19
mapped tables, including `request_limits`, `users`, `profiles`, `refresh_tokens`.
Both post-migration and real FastAPI connections report the same database file,
Alembic head `20261101_1200`, foreign_keys=1 and no missing tables/columns.

**The exact cause of the reported live Render OperationalError is not established.**
The supplied generic error cannot distinguish missing schema, readonly storage,
locks, inability to open the file, missing SQLite functions or unsupported SQL.
The Render URL, deployment configuration and detailed runtime diagnostics were
not available. The previous report's missing-migration reproduction applies to a
launcher bypass, not proof of the current live failure.

Two diagnostic defects are established and fixed: the API handler logged only
`OperationalError`; Alembic's `fileConfig` default disables existing non-Alembic
loggers (including `fleng` when created before migrations). Application loggers
now survive migrations, and Fleng INFO diagnostics remain visible after Alembic
sets the root level to WARNING.

## Changes and safety

- `app.db.diagnostics` classifies SQLite failures into fixed categories and logs
  numeric/code names. Table names are included only if present in model metadata.
  It never emits raw exception messages, SQL, parameters, row values, request
  bodies, tokens, passwords, emails or the database URL/query string.
- Startup snapshots inspect `PRAGMA database_list`, schema columns, known Alembic
  revisions, SQLite version/RETURNING support, foreign_keys, journal_mode and
  busy_timeout. They report the actual file path, configuration/engine equality
  and advisory file/directory write flags. Only expected schema names are shown;
  unknown revision contents and unexpected table/column names are not printed.
- Preparation still tests actual writes and all mapped tables/columns. It also
  explicitly checks foreign keys, the existing now() connection function and
  SQLite >=3.35, required by authentication's UPDATE ... RETURNING statements.
  os.access flags alone cannot prove journal write access or available disk space.
- FastAPI emits a second snapshot from its own engine connection in production.
  No migration/seed hook was added to lifespan. PostgreSQL behavior is unchanged.
- `python -m app.db.diagnostics` inspects an existing file with SELECT/PRAGMA only;
  it refuses an absent file and never migrates, seeds, repairs or resets schema.
  A missing schema is reported, not silently repaired or treated as healthy.
- API errors remain HTTP 503 with the same generic DATABASE_UNAVAILABLE envelope.
  No frontend changes, database deletion, schema-check bypass or fake auth success.

## Safe Render diagnostic procedure

1. In Render Dashboard, record the **Live deploy commit SHA**, Root Directory,
   Start Command and Health Check Path. Do not copy secret environment values.
   This patch must be present in the live revision before expecting its logs.
   Expected root is the repository root; Start Command is
   `cd backend && python run.py`; readiness is `/api/v1/health/ready`.
   Direct `uvicorn app.main:app` bypasses launcher preparation.
2. Collect the startup lines, including:

   ```text
   Preparing SQLite: <resolved file path>
   SQLite connection version=<version> foreign_keys=1
   SQLite write check passed; upgrading Alembic to head.
   SQLite diagnostics stage=after_migrations {...}
   SQLite diagnostics stage=fastapi_startup {...}
   ```

   In both JSON snapshots expect engine_path_matches/settings_match_engine=true,
   the same database_path, foreign_keys=1, returning_supported=true, at_head=true,
   unknown_revision=false, missing_tables=[] and missing_columns={}.
   Database preparation failure must occur before Uvicorn starts listening.
3. Make one registration attempt using a dedicated test account through the
   existing UI. Collect only the matching server line, for example:

   ```text
   Database error on POST /api/v1/auth/register {"exception": "OperationalError", "sqlite_code": 1, "sqlite_name": "SQLITE_ERROR", "reason": "missing_table", "table": "request_limits"}
   ```

   This is an **example of the fault-injection test**, not an observed Render log.
   Do not export request bodies, cookies, authorization headers or access tokens.
4. If Render Shell is available, run from the live checkout:

   ```sh
   cd backend
   python -m app.db.diagnostics
   ```

   Supply its JSON with the two startup snapshots and error line. This command
   does not change schema/data. Do not run db.prepare, migrations, chmod, a schema
   stamp or a database replacement as a diagnostic action against the live file.
   Do not print env, DATABASE_URL, sqlite dumps or user rows.

| Evidence | Interpretation / next action |
| --- | --- |
| No preparation log, only FastAPI snapshot | Check live SHA and actual Start Command; launcher bypass/stale deployment is possible. |
| Different paths or settings_match_engine=false | Compare configuration between migration/web processes; use one explicit SQLite file path. Never delete either file. |
| missing_table / missing_column | Compare missing_* fields and migration head. at_head=true alone does not establish a valid schema. Back up before planning any repair. |
| SQLITE_READONLY / cannot_open | Check configured file/directory and mounted disk location; journal requires writable parent. Do not apply broad chmod. |
| SQLITE_BUSY / SQLITE_LOCKED | Check overlapping processes/instances and active writers; preserve single-instance SQLite topology. Busy timeout is 30000ms. |
| sql_syntax and returning_supported=false | SQLite runtime predates required RETURNING support; update Python/SQLite runtime while retaining SQLite. |
| missing_function | Check startup now() probe and deployed session.py; the application engine must install now() on every SQLite connection. |
| SQLITE_FULL / SQLITE_IOERR | Inspect Render disk capacity/storage events; preserve the database and plan storage correction. |

Render's [deploy history](https://render.com/docs/deploys) identifies the live
revision. A persistent disk is available only at runtime, not to the build or
pre-deploy command, and only paths under its mount persist:
[Render disks](https://render.com/docs/disks). Free service SQLite files disappear
on redeploy/restart/spin-down: [free service limits](https://render.com/docs/free).
These are hosting constraints, not proof of this OperationalError. SQLite remains
the selected database; this change does not migrate to PostgreSQL.

## Verification and review

- Final full pytest: **251 passed, 15 skipped**, 91.59s. PostgreSQL tests skip
  without TEST_DATABASE_URL; the existing Starlette/httpx deprecation remains.
- Targeted production/diagnostics/SQLite suite: **28 passed**, 37.11s. Includes
  fresh production startup/registration/restart, all four missing-table failures,
  a readiness 200 alongside registration 503, safe error redaction, false-head
  rejection, unwritable files/directories and absent-file CLI refusal.
- Ruff passed for app/tests/launcher/Alembic env; mypy passed for **66 source
  files** including launcher. Changed Python formatting and git diff --check pass.
- `python3 scripts/backend-stabilization-smoke.py` passed: production launcher,
  readiness/static frontend, Secure/HttpOnly cookie/origin guard/refresh, dev
  migrations, authentication, Dashboard/Lessons, once-only XP and restart
  persistence. Secure cookies on local HTTP are explicitly supplied by the test;
  public Render HTTPS/proxy behavior remains unverified.

The sandbox denied local socket creation; pytest/localhost smoke ran with approved
unrestricted execution. All database tests used isolated temporary files; the
existing application database was not opened for diagnosis or changed. No live
Render mutation, push or deployment was performed.

Separate self-review covers log redaction/allowlists, logger survival across
Alembic, identical connection identity, schema checks retained, rollback of the
write probe, SQLite runtime requirements, no data reset, diagnostic CLI absence
handling, test isolation and unchanged API/frontend contracts.
