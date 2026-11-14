# Infrastructure verification — 2026-11-14

## Local evidence

Initial state: main at fc57232, clean working tree. No user edits were present.
Current changes are intentionally uncommitted/unpushed. Local Python 3.14,
Node's native test runner; hosted workflow targets Python 3.11/Node 22/Ubuntu 24.04.

- Final complete backend suite outside sandbox: **395 passed, 17 skipped**,
  144.22 seconds. Includes final self-review fixes, transfer and evidence-gate
  regressions. PostgreSQL skips are explicitly not verification evidence.
- Ruff: passed on app/tests. Mypy: passed on 79 application source files.
- Frontend Node suites: **4 passed**, no failures/skips.
- Alembic: exactly one head, **20261110_1400**; new tests apply the actual migration
  chain to disposable SQLite snapshots and compare metadata before copying.
- Curriculum importer validator: valid; 5 courses/50 lessons. Structural report:
  50 lessons, 500 words, 400 exercises valid. Linguistic review remains incomplete;
  source-unavailable status for all 500 words and 500 missing examples are retained
  as editorial findings, not suppressed as CI errors or approval.
- Documentation checker: **143 Markdown files / 621 local links**, plus 42 API
  operations, 47 named schemas, 21 models, 48 settings fields, 49 examples; zero failures.
- Workflow YAML parsed using PyYAML BaseLoader; expected events, aggregate always()
  and complete dependencies checked. **actionlint 1.7.7 passed locally** on final
  workflow, including expressions/shell analysis. No container job was run here.
- Transfer CLI help works; invalid SQLite target refuses before backup/network.
  New local tests cover UUID/UTC timestamp preservation, publication flags,
  refresh-token self-links, repeated/occupied target refusal, schema/FK/seed
  conflicts, dry-run rollback and reconciliation-trigger rollback. Special-character
  backup path exercises the actual read-only URI path before network connection.
- PostgreSQL evidence gate tests cover empty/missing/skipped/failed/error reports
  and successful complete evidence. Production databases are not test inputs.

An initial in-sandbox full suite stalled at async SQLite, consistent with the
existing documented sandbox behavior; it is not counted as a pass. The same suite
completed outside the sandbox. A new sync test helper initially nested Alembic's
SQLite autocommit migration in an external transaction; it was corrected to give
Alembic transaction ownership. Application migrations were not altered to hide it.

Final targeted results: **16 passed, 2 skipped** (the new PostgreSQL transfer and
logical restore drills have no local database). No claims are made for skipped tests.

## Public hosted observations

Read-only requests to public endpoints (no test account or data writes):

| Endpoint | Observation |
| --- | --- |
| GitHub main branch | SHA fc57232a95741912cf77c3ab90534b81f92c9afe, protected=false |
| GitHub rulesets | HTTP 200, empty list |
| Main check-runs | Required database checks, SQLite and application, PostgreSQL integration all failure |
| Original workflow jobs | db:verify passed both databases; full pytest failed both; later frontend step skipped |
| Hosted workflow log download | HTTP 403; detailed failing tests unavailable without authentication |
| Classic branch-protection detail | HTTP 401; public branch protected=false still available |
| Render /api/v1/health/ready | HTTP 200, database up |
| Netlify homepage | HTTP 200, HTML |
| Netlify /api/v1/health | HTTP 404 |

[Original failed run](https://github.com/Fleng-Fly/fleng-fly/actions/runs/43603490841).
Its public annotations include deprecated action runtime and moving runner-image
warnings plus exit code 1; they do not identify the failing test assertions.
Current action versions/runner pin address warnings only, not an established root
cause of those test failures. Owner must inspect private logs and rerun current code.

## Not verified

No PostgreSQL server/client/container or TEST_DATABASE_URL is available locally.
The new asyncpg transfer and pg_dump/pg_restore drills therefore skip locally.
The CI PostgreSQL job requires a real URL, installs clients, executes them and
rejects skips through the JUnit gate. Historical migration-job success does not
verify these new drills, provider TLS/PITR or production data transfer.

No authenticated hosting management, new hosted CI run, ruleset activation,
Render CI gate, provider backup scheduling/restore, production migration/cutover,
Netlify proxy/browser cookie/mobile integration, live OpenRouter/SMTP, PR/merge or
release was performed. Render DB connectivity does not prove persistent storage.

## Separate self-review

Reviewed transfer as an operator-facing data migration: explicit target; immutable
backup; read-only source; metadata/revision checks; target locks before occupancy
check; exact migration-seed exception; FK ordering/self-links; one transaction;
all typed rows/IDs/counts/FKs reconciled; safe failure output; no production hook.
Corrected the PostgreSQL smoke order to refresh the original restored cookie
before login replaces it; also rejected multiple Alembic heads explicitly.
Corrected snapshot URI construction for spaces/query characters and used parsed
URLs for recovery test database selection instead of string replacement. Reviewed
no-skips evidence behavior with synthetic failure reports. Limits (memory, CHECK
comparison, commit ambiguity, provider settings, unavailable hosted logs) are explicit.
No unnecessary stack, build system or API proxy was introduced.

[Owner setup and release checklist](../09-deployment/final-infrastructure-integration.md)
· [Typed transfer/recovery](../05-database/transfer-and-recovery.md)

## Files and Git state

Main remains at fc57232. No commits or pushes. Initial working tree was clean;
this task adds 9 files and modifies 14 files, all left for owner review:

- CI/tooling: [.github/workflows/database.yml](../../.github/workflows/database.yml),
  [.github/main-ruleset.json](../../.github/main-ruleset.json),
  [package.json](../../package.json),
  [scripts/check-test-report.py](../../scripts/check-test-report.py).
- Implementation/tests: [transfer.py](../../backend/app/db/transfer.py),
  [test_database_transfer.py](../../backend/tests/test_database_transfer.py),
  [test_postgres_recovery.py](../../backend/tests/test_postgres_recovery.py),
  [test_ci_evidence.py](../../backend/tests/test_ci_evidence.py).
- Database docs: [index](../05-database/README.md),
  [persistence/recovery](../05-database/persistence-and-recovery.md),
  [transfer/recovery](../05-database/transfer-and-recovery.md).
- Security/deployment: [secrets](../08-security/secrets-management.md),
  [deployment index](../09-deployment/README.md),
  [CI gate](../09-deployment/database-ci-gate.md),
  [integration report](../09-deployment/final-infrastructure-integration.md).
- Testing/contributing: [testing index](README.md), this verification report,
  [pull requests](../11-contributing/pull-requests.md).
- Plans/maps: [database plan](../../plans/database-plan.md),
  [milestones](../../plans/milestones.md), [roadmap](../../plans/roadmap.md),
  [data flow](../../project-map/data-flow.md), [modules](../../project-map/modules.md).

Netlify configuration, frontend files, production environment templates, curriculum
content and existing migrations were not changed. No credentials or database
snapshots were added to the repository. Off-host backup schedules and storage
retention remain owner configuration, not implemented hosted services.
