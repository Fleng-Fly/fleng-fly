# Database CI and hosting gate

The existing `.github/workflows/database.yml` verifies every push/PR/merge group
without production secrets. Independent jobs cover SQLite/backend, static quality
and dependency integrity, Node frontend tests, Chromium E2E, disposable PostgreSQL
16 and workflow validation. The always-running `Required database checks` gate
requires every job to succeed, including browser and documentation checks.
No deployment or content publication is triggered.

See [CI automation and local commands](../10-testing/ci-automation.md) for the job
matrix, caching, `npm run check:all`, temporary migration smoke and diagnostics.
PostgreSQL transfer/logical recovery evidence remains mandatory: skipped/missing
required cases fail `scripts/check-test-report.py`. The old duplicate `db:verify`
before full pytest was removed; database tests still run inside each engine's
full suite. Historical hosted failures are documented in the
[earlier integration audit](final-infrastructure-integration.md); local checks of
the revised workflow do not establish hosted CI success or branch protection.

## Manual Render configuration

**Not enabled or verified by this change.** No hosting account/settings were altered.

1. Link the existing backend service to the protected release branch through the
   GitHub integration. Preserve Python build `python -m pip install ./backend`,
   start `cd backend && python run.py` and `/api/v1/health/ready` health path.
2. In Settings → Auto-Deploy select **After CI Checks Pass**, or turn auto-deploy
   **Off** until CI/branch protection is configured. The default On Commit can
   deploy before checks finish. Disable other deploy hooks/workflows that bypass CI.
3. Require `Required database checks` on the protected branch. Render treats
   neutral/skipped GitHub checks as passing, so the always-running aggregator is
   needed. Verify a deliberately failing PR/check prevents a deploy before relying
   on the gate. Manual deploys remain an operator-controlled bypass.
4. Preserve existing data before changing production DATABASE_URL. Choose durable
   PostgreSQL with TLS and a tested backup/restore procedure; Render Free needs
   an external provider ([setup](render-free-persistence.md)). Switching the URL and moving
   data require [separate release approval](../05-database/persistence-and-recovery.md).
5. On a paid Render instance, if SQLite is retained, attach a persistent disk and use an absolute
   path within its mount (e.g. `/var/data/fleng.db`), one instance and off-host online
   backups. Move existing data only in a separately approved maintenance procedure.
   Do not change the URL to a new empty file and assume the users were transferred.
6. Existing PostgreSQL schema upgrades are a reviewed explicit release operation.
   The launcher initializes a completely empty schema and its approved catalog
   atomically; it refuses outdated/unknown occupied schemas. Do not attach reset
   or downgrade commands to deploy. Keep secrets in
   Render's private environment. Preserve exact CORS, cookie and trusted-proxy settings.

Render documents the [CI deployment gate](https://render.com/docs/deploys),
[persistent disks](https://render.com/docs/disks) and
[PostgreSQL recovery](https://render.com/docs/postgresql-backups). Actual purchased
plan, retention, storage and restore evidence must be confirmed by the operator.

Netlify's existing static deployment and API routing remain unchanged. Configure
its deploy/branch policy separately if coordinated frontend/backend releases are
needed. This backend CI change does not establish a Netlify deployment gate.

The durability release additionally requires real PostgreSQL startup/account
replacement and atomic-bootstrap rollback evidence. Only the exact non-POSIX
platform guard is exempted on POSIX, identified by testcase name/class/reason;
missing or skipped mandatory PostgreSQL cases still fail the aggregate. This
avoids treating a test that cannot apply to Ubuntu as a skipped database check.
