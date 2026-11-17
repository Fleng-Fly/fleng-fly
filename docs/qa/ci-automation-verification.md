# CI automation sprint verification — 2026-11-17

Branch: `feat/ci-automation`. Worktree: `/tmp/fleng-ci-automation`.
Base: `76ef2b6867162969c515d6c4dd076fce2bb0452b`.

The existing `.github/workflows/database.yml` was improved rather than adding a
second competing pipeline. The stable required-check name now aggregates all
SQLite/backend, static/dependency, frontend, E2E, PostgreSQL and workflow jobs.
No push, merge, deploy, stash operation or production migration was performed.
Main, foreign worktrees, frontend source, backend application, migrations,
curriculum JSON and production configuration were not changed.

## Logical commits

| Commit | Purpose |
| --- | --- |
| 286aa7c | Isolated fail-fast check:all, dependency checker and temporary Alembic smoke |
| d93e349 | Split existing verification workflow; require Chromium E2E |
| 2528198 | Explicit browser Web Locks fixture on Node 22 |
| 53a1a5a | Cache npm bootstrap downloads as well as pnpm packages |
| d360491 | Verify package-manager pin and enforce migration checks without assert |
| ae54efd | Make production-origin fixture independent of runner APP_ENV |

Documentation, plan and map changes are recorded in the final documentation
commit. [Operator guide and local commands](../10-testing/ci-automation.md).

## Validation scope

Local runtime: Linux, Python 3.14.10, Node 22.23.5, pnpm 12.9.1,
Playwright 1.56.1, Chromium headless shell build 1194. Python and JS packages
were installed into this worktree's new virtualenv/node_modules; no other
worktree's environment was modified.

- Frozen pnpm install passed and left the lockfile unchanged.
- Constrained Python installation, pip check and all declared applicable pins
  passed. A separate Python 3.11 binary-wheel resolution dry-run passed; this
  is not execution of tests on Python 3.11.
- Actionlint 1.7.7 with ShellCheck 0.10.0 passed. YAML structure and the six-job
  required-gate dependency graph were checked independently. All 29 workflow
  shell blocks passed `bash -n`; npm command references exist. Node syntax and
  Ruff for the new Python verification scripts passed.
- Unknown check:all arguments and private `.env` both returned status 2 with
  actionable messages. An injected installed-version mismatch failed explicitly.
- The final full runner was invoked with artificial inherited production-mode,
  external-database, SMTP and AI settings to check that it discards them. All
  real test connections remain disposable/fixture-owned. No real credentials
  were supplied.
- Temporary migration smoke passed: one head `20261117_1200`, upgrade from empty,
  second idempotent upgrade, `alembic check` with no ORM drift, SQLite integrity
  and foreign-key checks. The updated non-assert checks were also rerun directly.

## Final local results

`npm run check:all` completed with exit status **0**, including the existing
Chromium E2E command, with no skipped stages. Final documentation edits were then
checked again with `npm run docs:check` and `git diff --check`.

| Gate | Result |
| --- | --- |
| Backend pytest | 2373 passed, 24 skipped, 77 warnings; 403.30 seconds |
| Frontend JS | 63 tests passed across the 10 existing files |
| Legacy PWA retirement | Both scripts passed |
| Playwright Chromium E2E | 9 passed, 24.8 seconds, two workers, no retries |
| Ruff | Backend app/tests and new verification scripts passed |
| mypy | Passed: 89 source files, existing untyped-body informational note |
| pip/dependency integrity | Passed; frozen JS install left lock unchanged |
| Migration smoke | Passed at 20261117_1200, including repeat upgrade and ORM drift |
| Documentation | 160 Markdown files, 663 links, all 49 operations/60 schemas/23 models/53 settings and 52 examples checked; zero failures |
| Workflow/shell | actionlint + ShellCheck passed; all 29 bash blocks parse |
| Whitespace | Passed |

The 24 backend skips are recorded rather than represented as PostgreSQL proof.
Existing pytest-asyncio/Alembic deprecation warnings remain. Logs are local under
`/tmp/fleng-ci-check-all.log`, `/tmp/fleng-ci-origin-tests.log`,
`/tmp/fleng-ci-migration.log` and `/tmp/fleng-ci-python311-resolution.log`.

## Failures found and resolved

The first fail-fast run stopped at the existing AI streaming test on Node 22:
that test assumed native browser Web Locks, available in the previous Node 26
validation but absent in Node 22. The test now explicitly supplies/restores the
browser lock mock and verifies exclusive acquisition; the security fallback tests
are retained. No frontend or authorization implementation was changed.

The next full run stopped at backend pytest with 2355 passed, 24 skipped and 18
fixture errors. Global `APP_ENV=development`, already used by the old workflow,
overrode the production example in the origin-test fixture. The fixture now
explicitly selects its intended production mode; no production configuration or
policy was changed. All 24 origin tests passed independently under development
runner settings, then the full runner was repeated. No tests were skipped to
hide either issue; these failures also exercised check:all's stop/nonzero behavior.

The restricted execution sandbox did not reliably capture child Node stderr;
guard checks and the full runner were run unrestricted. The existing aiosqlite
sandbox limitation also requires unrestricted database tests. Browser installation
used Node 22 and the existing Playwright installer, not custom browser/test code.

## Remaining verification

GitHub Actions was not executed locally. Docker/service-backed PostgreSQL is not
available in this local environment; its existing job/evidence gate is retained,
not claimed as passed. Full Python 3.11 execution on Ubuntu 24.04, real hosted
Actions setup/cache behavior, artifact upload, fork PR permissions, cancellation,
merge groups and owner-managed branch protection require hosted runs after a
separately authorized push. No production-code blocker was fixed or bypassed.
