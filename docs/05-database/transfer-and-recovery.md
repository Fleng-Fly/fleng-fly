# Typed transfer and recovery

`app.db.transfer` is implemented with existing SQLAlchemy/Alembic/sqlite3. It is an
operator command, never called by app startup, CI release or a hosting deploy hook.
Local disposable SQLite copy/rollback tests pass; real asyncpg and PostgreSQL
logical recovery drills are mandatory in CI but were not run in this environment.

## Staging transfer

Use only a disposable SQLite staging snapshot and an explicitly supplied empty
PostgreSQL staging database/schema. Never supply the normal application URL by
implicit default. First migrate the target with this release's Alembic head:

```sh
# Explicit private staging URL; refuse an unset value instead of using .env.
: "${STAGING_DATABASE_URL:?Set an isolated staging URL first}"
cd backend
DATABASE_URL="$STAGING_DATABASE_URL" APP_ENV=development .venv/bin/alembic upgrade head
cd ..
# Supply STAGING_DATABASE_URL privately; do not put credentials in shell history.
npm run db:transfer -- --source /private/staging/source.sqlite3 \
  --backup /private/staging/snapshot-dry.sqlite3 \
  --destination-env STAGING_DATABASE_URL --schema public
# After reviewing a successful dry run, apply only to the same isolated staging target:
npm run db:transfer -- --source /private/staging/source.sqlite3 \
  --backup /private/staging/snapshot-apply.sqlite3 \
  --destination-env STAGING_DATABASE_URL --schema public --apply
```

Each invocation requires a **new** backup filename outside the repository. Backup
uses SQLite's online API, mode 0600, integrity and foreign-key checks; refuses
existing paths. Source stays untouched. The snapshot is then opened read-only.
Source and target must have the exact mapped table inventory plus alembic_version,
the release head and no detectable ORM metadata drift. Extra/missing tables,
columns, indexes or FK differences abort; Alembic autogenerate does not prove
semantic equality of every CHECK/default/trigger. Use the known migration chain and
constraint tests, not a manually stamped schema. No schema is created or migrated
by transfer. No source secrets or row contents appear in CLI output.

The PostgreSQL destination is locked (ACCESS EXCLUSIVE NOWAIT on every mapped table
and alembic_version) before checking emptiness; stop all staging writers. All tables
must be empty except migration-created achievements, allowed only when **all**
primary keys and values equal the source definitions. No delete/upsert/merge is
performed. A repeated applied import refuses occupied data rather than duplicating.

Core typed reads preserve UUIDs, booleans, JSON, dates and timestamps. Naive SQLite
timestamps are interpreted as UTC, matching this application's policy. Explicit
IDs, password hashes, token chains, XP/progress, submissions, vocabulary/cards,
AI records, quota windows, course relationships and publication flags are copied.
Tables insert in FK order; nullable refresh-token self-links are restored in a
second pass. Every FK, primary-key set, count and typed row value is reconciled.
Dry run performs the real inserts and checks then rolls back; --apply commits one
transaction. Errors roll back the transaction; a connection loss during COMMIT can
leave the outcome ambiguous: inspect/reconcile the isolated destination before
retrying, never assume it is empty. Backup failures can leave incomplete files.

Current size limit: full snapshots and reconciliation are held in memory and rows
are inserted individually. This favors auditable MVP data over high-volume import
performance. Measure staging runtime and memory before scheduling downtime. Retain the private JWT secret and cookie settings across cutover to preserve existing
sessions. Source
writers must be stopped for final cutover consistency; an online snapshot alone
does not transfer later writes. Fresh full login/refresh, zero duplicate XP, course
access and card resume must pass on staging before production authorization.

## Backup policy and provider drill

Owner must select and record a real encrypted off-host location, responsible
operator, alert destination and retention before launch. Suggested options (not
configured): daily logical backup with 7 daily / 4 weekly / 3 monthly generations;
pre-release backup; provider continuous PITR where the purchased plan supports it.
Choose frequency from acceptable data-loss window. Keep production archives out of
Git, Actions artifacts and public hosting; require encryption at rest/in transit,
restricted service identities, key separation and restore-audit access. A local
0600 file is access control, **not encryption**. Verify successful backup sizes,
checksums and restore status; alert on missed schedules.

Use PostgreSQL clients matching the server major version. For an owner-approved
staging rehearsal, configure a private pg_service.conf/PGPASSFILE and PGSSLMODE
(require/verify-full as supported by the provider); chmod credential files 0600.
Ensure the restore service targets a **new empty isolated recovery database**.

```sh
# PGSERVICE names point to isolated staging stores, not production.
umask 077
PGSERVICE=fleng_staging pg_dump --format=custom --no-owner --no-acl \
  --file=/private/encrypted-backups/staging.dump
# New empty database; no --clean, no live destination, no seed before restore.
PGSERVICE=fleng_recovery pg_restore --dbname=service=fleng_recovery \
  --exit-on-error --single-transaction --no-owner --no-acl \
  /private/encrypted-backups/staging.dump
```

Pause staging writers or record a consistent snapshot manifest: revision, every
count/primary-key set and typed row values (sensitive manifests stay private).
After restore verify the release head, all counts/relationships and typed values,
login/refresh, progress/XP, vocabulary and card resume. Do not run seed/import before
reconciliation. Existing `test_postgres_recovery.py` automates this on **two newly
created disposable databases** using PostgreSQL clients, with no production URL.
The configured test role must be allowed CREATEDB. Missing client tools fail the
configured PostgreSQL test instead of skipping it. CI installs version 16 clients.
The test's loopback transport disables TLS for its disposable service; remote
test commands require TLS. It is not proof of the provider's restore guarantees.

[Render Recovery](https://render.com/docs/postgresql-backups) is a separate operator
drill: verify the purchased database's Recovery page and available PITR window,
restore staging to a new instance, validate it in isolation, and record restore
time and loss window. No service URL switch or billing action is authorized here.
Free compute does not provide Render recovery; do not assume it does.

## Recovery and rollback

For SQLite follow [online backup/restore](persistence-and-recovery.md). Rehearse
on disposable paths, including WAL. For PostgreSQL, keep damaged storage intact,
stop writers, restore to a new isolated instance, reconcile and validate, then
request explicit authorization for a service switch. Log the selected snapshot,
release SHA and validation results privately. Never restore over production as a
"test". Provider PITR can incur costs and needs owner approval before provisioning.

No fixed downtime is promised: logical recovery time depends on archive size,
network, indexes, validation and DNS/service reconnection; measure the staging
run. A final SQLite transfer needs a maintenance window through snapshot, import,
validation and controlled switch. PITR limits and export retention depend on the
actual provider plan. Before PostgreSQL accepts writes, rollback can restore the
old code/SQLite URL under maintenance. After new writes, stop traffic and reconcile
both stores or recover forward; switching to an old SQLite backup loses new data.
Do not automatically downgrade migrations or change DATABASE_URL.
