# Persistence and recovery

## Decision

Keep file-backed SQLite for local development. Use managed PostgreSQL for durable
production hosting after a separate migration rehearsal and release approval.
Existing SQLAlchemy async models, Alembic and asyncpg already support this choice;
no new runtime dependency or automatic URL switch is needed.

| Option | Benefits | Requirements and limits |
| --- | --- | --- |
| SQLite on persistent filesystem | Smallest operational change; same database file | Absolute path under a mounted disk, one instance/launcher, off-host consistent backups, restore drills; disk availability remains a single point of failure |
| Managed PostgreSQL (recommended production target) | Storage independent of app deploys; provider backup/recovery options | Paid durable service, verified backup retention/TLS, explicit schema release and a rehearsed data transfer |

An ephemeral Render filesystem is unsuitable for accounts and learning history.
A relative SQLite URL resolves under `backend/`, independent of the shell working
directory. The launcher probes writes, applies pending migrations, checks mapped
columns and seeds only an empty course catalog. It does not replace the file.
PostgreSQL URL forms `postgres://` and `postgresql://` normalize to
`postgresql+asyncpg://`; PostgreSQL migrations remain explicit.

## Audit (2026-11-14)

Read-only inspection of the existing `backend/data/fleng.db` found: 1 user,
1 profile, 1 aggregate progress row, 1 lesson-progress row, 5 refresh-token rows,
2 published legacy courses, 6 lessons, 18 exercises, 0 course words and 0 flashcard
sessions. There were no foreign-key violations. Revision: `20261110_1400`.
No identities, hashes or token values were exported. This is local evidence,
not a production inventory. The source database was not migrated, seeded or reset.

All five A0–B2 courses exist only in draft JSON here. Normal startup intentionally
neither imports nor publishes them. The normal catalog excludes unpublished
courses/lessons, including their course words. Missing drafts do not mean missing
user data. See [development curriculum](../06-learning/local-draft-workflow.md).

## Local setup

```sh
npm run setup
# Optional: set DATABASE_URL privately in ignored .env; default is backend/data/fleng.db.
npm run db:migrate
npm run db:seed
npm run dev
```

`db:seed` updates seed-owned demo content in place; it is not a curriculum publish
command. Existing accounts, progress, XP and sessions remain in the same database
across process restarts. Never use test URLs or temporary preview storage for
valuable learner data.

## SQLite backups and restore

```sh
npm run db:backup -- /absolute/private/location/fleng-2026-11-14.sqlite3
```

The helper uses SQLite's online backup API, so committed WAL data is included.
It opens an existing source read-only, creates a new mode-0600 destination,
refuses overwrite, checks database and FK integrity and reports table counts.
The CLI refuses destinations inside this repository. Keep backups encrypted,
access restricted and off the application disk; define retention with the owner.
Do not upload production backups to Actions, Git or public report storage.
A failed backup may leave an incomplete destination; it must not be used.

For a restore drill, stop writers and restore into a **new** private path, never
over the live database. Run `PRAGMA integrity_check`, `PRAGMA foreign_key_check`,
compare every table count and Alembic revision to the backup, point an isolated
application at the new path and verify login, refresh, XP, progress and card
resume. Retain the original file and its WAL/SHM while coordinating shutdown;
do not copy only a live main file with `cp`. Changing a production URL or replacing
production storage requires separate approval. The automated test verifies a WAL
backup round trip; a provider/off-host recovery drill remains manual.

## PostgreSQL backup policy

Configure provider backup retention/PITR and verify the purchased plan's guarantees.
Use `pg_dump --format=custom` for an additional encrypted off-host logical backup
with connection credentials supplied privately (for example a protected PGPASSFILE).
Restore with `pg_restore --exit-on-error` into a new empty recovery database, then
verify revision, all counts, relationships and representative API writes. Never use
`--clean` against a live database. Provider recovery must be rehearsed separately.
See [Render recovery documentation](https://render.com/docs/postgresql-backups).

## SQLite to PostgreSQL release procedure (not executed)

1. Provision a dedicated **staging** PostgreSQL database/role, restrict access and
   verify asyncpg connectivity/TLS. Run the full suite with TEST_DATABASE_URL set
   to that disposable database; tests create/drop only unique test schemas.
2. Freeze application writers during the final transfer (all API workers, jobs and
   administrative imports). Take and restore-test an online SQLite snapshot.
   Record release commit, Alembic revision, every table count and FK/integrity checks.
3. Migrate a new empty PostgreSQL target to the same Alembic head using the reviewed
   release. Never point the transfer at an occupied target or reset an existing DB.
4. Prepare/review a one-off typed SQLAlchemy transfer against the **snapshot**.
   Read with ORM column types: SQLite UUID hex must become UUID values, timestamps
   need consistent UTC semantics, booleans and JSON need typed conversion. Copy
   explicit primary keys unchanged, not via registration/seed APIs. Include all
   mapped tables: credentials, profiles, aggregate/lesson progress, submissions,
   refresh chains, reset tokens, vocabulary/reviews, flashcard JSON snapshots,
   activity/awards, quota windows and AI records as well as catalog content.
5. Insert in `Base.metadata.sorted_tables` dependency order in one target transaction.
   For refresh-token self-links, insert with `replaced_by_id=NULL`, then restore
   links after every token exists. Reconcile migration-created achievement definitions
   by exact primary-key/value equality; abort on conflicts. Preserve publication
   flags verbatim. Do not run the curriculum importer or publish command.
6. Before commit compare **every** source/target primary-key set and typed row value,
   table count, profile XP, aggregate totals and learner submission state. Run an
   anti-join for every FK (including token self-links), check all constraints, card
   snapshot JSON and migration head. Any mismatch aborts the target transaction.
7. On staging, test real login/refresh, lesson replay awarding zero duplicate XP,
   vocabulary/review ownership and active/completed flashcard session resume.
   Record transfer duration and repeat successfully before scheduling production.
8. Only after explicit production authorization repeat the frozen snapshot transfer;
   manually change the private DATABASE_URL and release application code. Preserve
   the original SQLite snapshot and URL securely; verify readiness and learner flows.

This is an explicit runbook, **not an implemented or verified cross-engine copy
utility**. Production migration is not ready until the typed transfer and staging
rehearsal above pass. No production migration or URL change was performed.

## Rollback

Before accepting writes on PostgreSQL, rollback can stop the new application and
restore the original release/SQLite URL under maintenance, since the source remains
intact. After PostgreSQL accepts writes, reverting to the old SQLite snapshot would
lose those writes: stop traffic, preserve both stores, reconcile changes through a
reviewed reverse transfer or recover forward. Do not silently switch databases.
Prefer forward fixes to Alembic downgrades; the A0 downgrade intentionally refuses
A0 data and other downgrades can destroy learning records.
