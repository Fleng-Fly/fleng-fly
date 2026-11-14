# Database CI and hosting gate

`.github/workflows/database.yml` runs on every push and pull request, without path
filters or production secrets. SQLite verifies fresh Alembic schema creation,
upgrade reruns and ORM drift, seed/import idempotency, draft isolation, learner
preservation, backup round trip and the full backend suite. Ruff, mypy, frontend
Node tests and structural curriculum validation are mandatory. PostgreSQL 16 runs
as a disposable service with test-only credentials and runs migrations, the same
database pipeline and the full backend suite via isolated per-test schemas.
No database is uploaded as an artifact and no deployment or publication is run.

The `Required database checks` aggregator runs even after job failure and succeeds
only if both jobs succeed. Configure GitHub branch protection/rulesets for the
release branch to require this exact check, prevent bypass and require PR review.
Do not mark database jobs continue-on-error or allow skipped jobs to count here.
The Actions file has been prepared locally; no remote workflow run is claimed.

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
4. Retain current production DATABASE_URL. Plan a durable paid PostgreSQL service
   with recovery retention, TLS and a tested restore; switching the URL and moving
   data require [separate release approval](../05-database/persistence-and-recovery.md).
5. If SQLite is retained temporarily, attach a persistent disk and use an absolute
   path within its mount (e.g. `/var/data/fleng.db`), one instance and off-host online
   backups. Move existing data only in a separately approved maintenance procedure.
   Do not change the URL to a new empty file and assume the users were transferred.
6. PostgreSQL migrations are a reviewed explicit release operation before startup;
   do not attach seed/import/reset/downgrade commands to deploy. Keep secrets in
   Render's private environment. Preserve exact CORS, cookie and trusted-proxy settings.

Render documents the [CI deployment gate](https://render.com/docs/deploys),
[persistent disks](https://render.com/docs/disks) and
[PostgreSQL recovery](https://render.com/docs/postgresql-backups). Actual purchased
plan, retention, storage and restore evidence must be confirmed by the operator.

Netlify's existing static deployment and API routing remain unchanged. Configure
its deploy/branch policy separately if coordinated frontend/backend releases are
needed. This backend CI change does not establish a Netlify deployment gate.
