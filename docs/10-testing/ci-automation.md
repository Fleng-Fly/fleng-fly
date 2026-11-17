# CI automation and local verification

The existing [database.yml](../../.github/workflows/database.yml) is the single
verification workflow. It runs on every push, pull request, merge group and manual
workflow dispatch, with no path filters. It does not deploy or publish content.

## Independent jobs

| Job/check name | Checks | Browser needed |
| --- | --- | --- |
| SQLite and application | pip check, disposable SQLite migration smoke, full pytest including database pipeline | No |
| Static quality and dependency integrity | frozen JS lock install, installed Python constraints/JS lock versions, Ruff, mypy, docs/contracts, curriculum validators, whitespace | No |
| Frontend JavaScript | existing Node regression suites and legacy PWA retirement tests | No |
| Playwright Chromium E2E | real FastAPI and Chromium against a newly prepared temporary SQLite database | Chromium headless shell only |
| PostgreSQL integration | existing full backend suite in disposable PostgreSQL 16 with isolated schemas and mandatory JUnit evidence | No |
| Workflow validation | pinned actionlint container, including ShellCheck | No |
| Required database checks | always-running aggregate; all six prerequisite jobs must succeed | No |

The full SQLite suite is executed once, rather than repeating `db:verify` before
pytest. The PostgreSQL run repeats behavior deliberately against a different
engine; its evidence gate still rejects missing/skipped required database cases.
`db:smoke` adds a narrow CLI/migration check, not another pytest invocation.

Python 3.11, Node 22, pnpm 12.9.1 and Playwright 1.56.1 follow the existing project
configuration. Python packages install through `backend/constraints.txt`; JS
installs use `pnpm-lock.yaml` with `--frozen-lockfile --ignore-scripts`. No lockfile
or application dependency was upgraded. Pip caches are keyed by constraints and
pyproject. JS jobs cache the npm bootstrap download and pnpm package store by the
lockfile. Virtualenvs, databases and browsers are not cached. The frontend Node
job needs no dependencies beyond Node; only the E2E job installs Chromium/OS libs.
Superseded runs are cancelled and every job has a timeout. Failed E2E traces and
screenshots contain synthetic learners only and expire after seven days; no
SQLite/database files are uploaded.

## Local setup and full check

Use a clean worktree without `.env` or `backend/.env`. This prevents accidental
loading of private configuration through the application's existing Settings.
Do not remove or move a real configuration file just to pass checks; use an
isolated checkout/worktree. Existing local data and credentials are never needed.

```sh
npm run setup
# Install/use the pinned package manager from package.json:
npm install --global pnpm@12.9.1 --ignore-scripts --no-audit --no-fund
pnpm --version
pnpm install --frozen-lockfile --ignore-scripts
npm run test:e2e:install -- --only-shell
# On supported Linux runners, install OS libraries as well if missing:
pnpm exec playwright install-deps chromium
npm run check:all
```

The runner is sequential and stops at the first failed command, returning a
nonzero status. It runs pip check, dependency integrity, Ruff, mypy, frontend and
PWA tests, docs/contracts, curriculum validation, temporary migrations, full
backend pytest, E2E and whitespace. It never installs/downloads dependencies or
browsers itself. `PLAYWRIGHT_BROWSERS_PATH` may select an already installed browser
cache. Unknown options fail with status 2. A missing backend environment or private
`.env` also fails before running tests.

When a browser is deliberately unavailable:

```sh
npm run check:all -- --skip-e2e
```

This explicitly reports the skip and is **not** equivalent to the full gate.
The local command never starts PostgreSQL. Reproduce that opt-in job separately
with a dedicated disposable PostgreSQL server and the existing
[PostgreSQL testing instructions](../05-database/postgresql.md). The hosted
PostgreSQL job retains its full suite plus `scripts/check-test-report.py`.

The runner strips inherited application/hosting/test-database credentials and
uses a fresh temporary SQLite URL, a synthetic JWT secret, disabled AI and disabled
SMTP. No OpenRouter/network provider call or production database is required.
Tests still exercise mocked AI/SMTP behavior through their existing fixtures.
Process PATH and OS/temp/cache variables are retained. The temporary directory is
removed after successful or failed checks; normal project data is not used.

## Dependency and migration diagnostics

```sh
npm run check:dependencies
npm run db:smoke
```

Dependency integrity checks every applicable installed Python constraint and
root JS manifest/lock/installed versions. `pip check` separately checks package
requirements. Frozen pnpm install verifies the resolved dependency graph and
package-store integrity; the version checker is not a cryptographic audit of all
installed files. Windows omits the optional unsupported uvloop extra. Constraints
include verification dependencies such as PyYAML and packaging.

The migration smoke ignores the caller's DATABASE_URL. It always creates a new
SQLite file under an OS temporary directory, verifies exactly one Alembic head,
runs upgrade twice, runs `alembic check` for ORM drift, and checks revision,
SQLite integrity and foreign keys. It performs no seed, publication, downgrade or
production migration. A failure leaves the exit status nonzero and shows the
failed Alembic command. Multiple heads require a reviewed migration fix in the
appropriate application branch; do not choose an arbitrary head to hide drift.

## Troubleshooting and CI limits

- **Install/frozen-lock failure:** compare package.json with pnpm-lock.yaml. Do
  not regenerate a lock automatically in CI. Re-run constrained setup/frozen
  install; a Python version mismatch is shown by `check:dependencies`.
- **Node 22 auth regression:** `test-ai-api.mjs` models browser Web Locks explicitly;
  Node runtime APIs must not stand in for browser fixtures. The no-lock security
  behavior is covered by the separate refresh regression suite.
- **Origin fixture failure under development CI:** the production-origin fixture
  explicitly selects production mode while retaining its synthetic secret and
  isolated database. Do not change production defaults to fix a test fixture.
- **E2E browser/OS failure:** install the browser matching committed Playwright,
  verify OS libraries and availability of the loopback test port (default 3101).
  The existing E2E server creates/migrates/seeds its own temporary SQLite and
  disables external services. Inspect the failed job log and diagnostic artifact.
- **pytest hangs only in the execution sandbox:** the documented aiosqlite
  cross-thread wake-up issue requires an unrestricted local run; do not skip
  application tests to hide it. See [testing](../testing.md).
- **PostgreSQL gate:** inspect JUnit and mandatory-evidence output; a skipped
  required test does not count as verification. Only the existing explicit
  non-POSIX platform exception is allowed.
- **YAML/shell:** run actionlint 1.7.7 with ShellCheck available, or the same
  `rhysd/actionlint:1.7.7` container as CI. `bash -n` checks parsing only.

Local actionlint and shell checks cannot execute GitHub Actions. Hosted runner
setup, cache restoration, fork PR permissions, service provisioning, artifact
upload, cancellation, merge queue and branch-protection enforcement can only be
confirmed by actual hosted runs after a separately authorized push. The existing
`Required database checks` name remains stable for an owner-managed ruleset;
this change does not modify repository settings or production hosting policies.

Official references: [setup-python cache](https://github.com/actions/setup-python),
[setup-node caching](https://github.com/actions/setup-node),
[Playwright CI](https://playwright.dev/docs/ci),
[Chromium installation](https://playwright.dev/docs/browsers).
