# Database tests

Default fixtures create ORM tables in isolated SQLite, not necessarily through Alembic. File tests cover migrations, independent-connection locks, startup diagnostics and restart persistence. These evidence types are distinct.

TEST_DATABASE_URL selects a dedicated PostgreSQL DB; fixtures create/drop unique fleng_test_* schemas, migration tests unique migration schemas. Never use production. Without a URL PostgreSQL-specific checks skip; SQLite is not PostgreSQL proof.

```sh
cd backend
.venv/bin/pytest -q tests/test_sqlite_local.py tests/test_production_sqlite.py tests/test_stabilization.py
.venv/bin/pytest -q tests/test_postgres_migrations.py
```

The latter can explicitly skip. Live TLS/restore and provider integrations need separate evidence.

[Section index](README.md) · [Documentation home](../README.md)

## Mandatory database pipeline

`npm run db:verify` runs `test_database_pipeline.py` plus PostgreSQL migration checks.
The new pipeline migrates a new SQLite file or a unique disposable PostgreSQL schema,
upgrades twice, compares ORM metadata and checks seed/import idempotency. It creates
an authenticated learner, earns XP, saves a vocabulary word/card session, imports
all drafts twice, closes the engine pool and verifies identity, refresh, progress,
XP and flashcard resume through fresh connections. It checks all declared FKs and
exact curriculum counts while normal APIs still hide all 50 draft lessons.
The SQLite backup test checks committed WAL data, private permissions, restore and
refusal to overwrite an existing file. Existing production-launcher tests separately
verify process restart persistence; reconnect evidence is not process-restart proof.

`npm run frontend:test` runs all four existing Node regression suites.
`npm run curriculum:validate` runs DB-independent structural checks; for linguistic
QA also run `backend/.venv/bin/python scripts/validate_curriculum.py --report json`.
Source-corpus evidence and human content approval remain separate.

CI requires both SQLite and PostgreSQL jobs via an always-running aggregator. The
PostgreSQL job always sets TEST_DATABASE_URL to its disposable service; locally the
PG-only migration test skips without it. Never supply a production URL to tests.
See [hosting gate](../09-deployment/database-ci-gate.md).

## Windows integration ? 2026-11-14

`npm.cmd run db:verify` uses the cross-platform backend runner. After merging
the letter-tile sample, expected totals are 57 lessons and 421 exercises.
SQLite persistence and backup round-trip: 2 passed; PostgreSQL: 1 skipped
(no TEST_DATABASE_URL). The POSIX mode-bit assertion runs only on POSIX;
Windows inherits directory ACLs and this test does not verify those ACLs.
Ruff, mypy, 27 frontend tests and both PWA checks also passed.
