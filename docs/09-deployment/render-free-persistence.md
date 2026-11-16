# Render Free: retain accounts across sleep

## Diagnosis

Accounts and progress are stored in SQLAlchemy-backed database tables, not Python
process memory. Render Free replaces local filesystem changes on sleep, restart
and redeploy, including backend/data/fleng.db. The startup seed recreates courses,
which can make the app look normal while registered users/progress are gone.
Recreating catalog content is not recovery of runtime user data.
[Render Free storage limits](https://render.com/docs/free).

## Required hosting action

A commit cannot turn Render's ephemeral filesystem into durable storage. Keep the
Free web service and connect it to an external PostgreSQL database. Neon offers a
Free plan with storage/compute/transfer limits; review the current
[provider plan](https://neon.com/docs/introduction/plans) before provisioning.
No account, resource, payment plan or hosted DATABASE_URL was changed here.

1. In your own provider account create a **Free**, isolated PostgreSQL project.
   Choose a suitable region near the Render service. Use a direct connection for
   this single-worker application; pooled-provider endpoints are not verified here.
2. Put its connection string only in Render → Environment → DATABASE_URL.
   This project uses asyncpg. The compatible form is:

   ```text
   postgresql+asyncpg://USER:PASSWORD@HOST/DB?ssl=verify-full
   ```

   Use the provider's real credentials/hostname/database, URL-encode special
   password characters and never paste credentials into Git, frontend or reports.
   Ordinary postgres:// and postgresql:// schemes are normalized automatically;
   sslmode is translated to asyncpg's ssl parameter. Generic libpq strings with
   channel_binding are rejected because asyncpg cannot implement that option;
   use a compatible TLS-verified asyncpg URI instead of claiming that option works.
3. Preserve the existing private JWT_ACCESS_SECRET, cookie and CORS settings.
   Deploy the new commit using `cd backend && python run.py` from repository root.
   Set the URL **before deploying** the storage guard: the old Render SQLite
   configuration intentionally refuses startup instead of accepting disposable
   accounts. No fallback to local SQLite is performed if PostgreSQL is down.
4. A genuinely empty target schema is migrated to head and seeded with all seven
   owner-authorized courses automatically. This happens in one transaction under
   a PostgreSQL advisory lock. Partial initialization rolls back. Existing current
   Fleng schemas are validated and retain user data; unknown/outdated occupied
   schemas fail startup and require a separately reviewed explicit migration.
5. Register an approved test account, earn XP/save a word, restart the service,
   then verify login, refresh, progress and vocabulary/card resume. Check readiness
   at /api/v1/health/ready. Provider sleep/TLS/retention must be validated on the
   chosen hosted service separately from the local PostgreSQL test evidence.

Render Free Postgres has a documented 30-day expiry, so it is not an indefinite
storage solution. An external free plan also has quotas; no unlimited retention,
availability or backup guarantee is claimed. Paid Render SQLite is accepted only
when /var/data is actually mounted and the database resides beneath that mount.
[Render disks](https://render.com/docs/disks).

## Existing data and recovery

Never switch a populated service's DATABASE_URL assuming its accounts will follow.
Take a private consistent backup and use the tested
[SQLite-to-PostgreSQL transfer](../05-database/transfer-and-recovery.md) against an
isolated target before owner-approved cutover. For a full snapshot transfer, migrate
an empty target explicitly and transfer **before the app initializes its catalog**;
the transfer tool refuses an occupied destination rather than overwriting rows.
No production data transfer, restore or cutover was performed in this task.

If the ephemeral database was already discarded and there is no backup, its lost
accounts/progress cannot be reconstructed from the catalog or source code. Any
surviving local backups are separate from the vanished hosted database. Do not
commit account databases, passwords, refresh hashes or private backups to Git.

## Regression checks

`backend/tests/test_storage_durability.py` covers refusal of ephemeral Render SQLite,
actual-mount/path checks, pre-start refusal, TLS URL normalization and secret-safe
configuration errors. `backend/tests/test_postgres_startup.py` uses newly created
disposable databases to verify account/login/refresh, XP, words and cards after
complete ASGI process replacement; it also checks atomic initialization failure
and refusal to modify unknown/outdated occupied schemas. Never set TEST_DATABASE_URL
to production; the test role needs CREATE DATABASE and CREATE SCHEMA.

Local PostgreSQL 16.16 was compiled from the checksum-verified official release
under /tmp solely for these checks. It is not a new project/runtime dependency,
external account or production database. Hosted Neon/Render verification remains
pending owner access/configuration.


## Verification record — 2026-11-15

- Full SQLite suite: 419 passed, 22 skipped (PostgreSQL-only checks and the
  non-applicable non-POSIX guard).
- Full PostgreSQL suite: **440 passed, 1 skipped** (only the non-POSIX guard).
  JUnit evidence gate passed with no missing/skipped mandatory checks. This
  includes asyncpg transfer, logical backup/restore and migration drift checks.
- Actual PostgreSQL startup/replacement/rollback/refusal suite: 4 passed.
- Two pre-existing PostgreSQL test assumptions were corrected: compare UTC
  instants rather than SQLite/PostgreSQL timestamp strings, and give the
  local-only dev factory an explicit SQLite URL instead of inheriting the CI URL.
  Both regressions passed together after correction; no API or stored timestamps
  were changed to satisfy the assertions.
- Ruff, mypy (81 application files), four frontend Node test files, curriculum
  structural validation and Markdown links/contracts pass.
- Independent review checked initialization transaction ownership, concurrent
  startup locking, occupied-schema refusal, credential redaction and the mounted
  disk/path requirement. No SQLite fallback, destructive migration, new runtime
  dependency, cloud resource, hosted cutover or automatic push was introduced.
- These are disposable local test results, not evidence that the hosted Render
  DATABASE_URL has been changed. Provider setup and hosted restart checks remain
  required before declaring the account-loss issue resolved online.
