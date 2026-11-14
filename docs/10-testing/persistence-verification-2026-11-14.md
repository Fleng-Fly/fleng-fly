# Persistence verification — 2026-11-14

## Executed locally

| Check | Result |
| --- | --- |
| Full pytest suite | 379 passed, 15 skipped, 14 warnings; 182.26 seconds |
| Final focused database checks | 2 passed, 1 PostgreSQL-only skip after backup connection cleanup |
| Ruff | Passed |
| mypy | Passed, 78 source files |
| Frontend Node suites | All 4 passed |
| Fresh SQLite Alembic upgrade, second upgrade, ORM drift | Passed in new migration-based pipeline and existing file tests |
| Database preservation | Passed: existing catalog IDs, user, XP, aggregate progress, refresh and saved vocabulary/card snapshot after reconnect |
| Actual production launcher restart | Existing isolated SQLite production tests passed in full suite |
| Import idempotency/collisions/public visibility | Passed in pipeline and curriculum/preview suites |
| All drafts accessible locally | Preview API suite reads all 50 lessons; actual new preview preparation imported 955 rows |
| Curriculum structural validation | Passed: 5 courses, 50 lessons, 500 words, 400 exercises |
| Curriculum linguistic validator | Exit 0; no critical/high issues, 2 medium possible-multiple-answer findings, source corpus unavailable and human review pending |
| PostgreSQL offline full migration SQL | Compiled successfully; not a live database result |
| Documentation checks | 139 Markdown files, 582 links; 42 operations, 47 named schemas, 21 models, 48 settings, 49 examples; zero failures before this report was added |
| git diff --check | Passed |

The sandboxed aiosqlite run stalled as documented in the repository; it was
interrupted. Database tests and preview preparation completed outside that
restriction with approval. Existing pytest-asyncio/Alembic/httpx deprecation
warnings remain; warnings were not suppressed.

The real local SQLite file was inspected read-only before/after: still 1 user,
2 courses, 6 lessons, no imported drafts and no FK violations. No default database
seed, upgrade, replacement or cleanup was performed. A fresh isolated preview at
`/tmp/fleng-persistence-review-20261114` contains 7 courses and 56 lessons, with
exactly 5 courses/50 lessons unpublished and no FK violations. Its private marker
holds generated reviewer credentials and is not part of the repository.

## Not verified / not performed

No TEST_DATABASE_URL, PostgreSQL server/client or Docker/Podman was available in
this execution environment. Fifteen PostgreSQL-only tests skipped. asyncpg is an
existing installed dependency and URL normalization/offline SQL checks pass,
but live PostgreSQL migrations, transactions and API behavior remain unverified.
The mandatory Actions PostgreSQL 16 service job is prepared; it has not run remotely.

Production migration is **not ready for execution**: the runbook requires a typed
cross-engine transfer implementation and staging rehearsal with full record/ID/FK
comparison, backup/restore and rollback sign-off. No production URL/data, hosting
settings, curriculum publication, commits or pushes were changed.

## Separate self-review

Reviewed the final implementation for database targeting, accidental publication,
credentials/artifacts, existing data preservation, FK checks and failure propagation.
Corrected the test harness to let Alembic own SQLite migration transaction boundaries
and to snapshot learner XP after earning it. Backup connections close explicitly,
source opens read-only and destination creation refuses existing files. The CLI
rejects repository backup destinations; database file patterns are ignored.
The CI aggregator fails for failed/cancelled/skipped dependency jobs. No production
secrets, deploy hooks, automatic draft imports, database resets or schema changes
were added. Remaining external verification gaps are explicit above.
