# Infrastructure integration — 2026-11-14

This is an evidence inventory and operator runbook, not a production release.
No commit, push, deployment, production migration, URL cutover, paid provisioning,
restore into production, or curriculum publication was performed.

## Inventory

| Component | Repository implementation | External connection/configuration | Verification |
| --- | --- | --- | --- |
| Git | Initial `main`, clean tree, `fc57232` | Public GitHub API confirms main SHA `fc57232a95741912cf77c3ab90534b81f92c9afe` | Local edits remain uncommitted |
| Actions | Existing database.yml improved, no duplicate workflow | Existing hosted run at original SHA failed both full backend suites | Current edits not pushed/run remotely |
| Required check | `Required database checks`, always runs; requires all three jobs to succeed | No rulesets; public main branch API reports protected=false | Main is currently unprotected |
| PostgreSQL | asyncpg, migrations, isolated schema tests, transfer and logical recovery drills | No TEST_DATABASE_URL, PostgreSQL clients/server or container runtime here | New cross-engine and logical restore drills NOT RUN |
| Render | Existing production launcher/Procfile, readiness, CORS/cookie guards | Public readiness returns HTTP 200, database=up | Database engine/durability, deployed SHA, environment and CI gate not inspectable |
| Netlify | base=frontend, publish=.; API proxy remains commented out | Homepage HTTP 200; /api/v1/health HTTP 404 | Hosted UI exists; frontend API integration is incomplete |
| SQLite | Existing online private backup, new typed transfer tool | No application DB modified | Disposable migration/backup/transfer tests pass locally |
| A0–B2 | 5 drafts, 50 lessons, 500 vocabulary entries, 400 exercises | No publication performed | Structural validation passes; linguistic approval incomplete |
| Provider backups | Runbook and mandatory CI logical recovery drill | No backup schedule, storage bucket or provider recovery settings configured here | Provider restore/PITR NOT VERIFIED |

GitHub branch API explicitly reports main protected=false. Detailed classic protection
requires authentication (HTTP 401); hosted log download was denied (HTTP 403), so
the failing test names/root cause are not available from the public API.

Public read-only checks were performed from an unrestricted network context after
sandbox/browser fetches failed. An HTTP 200 readiness response proves current DB
connectivity only; it does not identify the engine, migration revision, retained
storage, backup configuration, or end-to-end authentication.

The original hosted [Actions run](https://github.com/Fleng-Fly/fleng-fly/actions/runs/43603490841)
completed with failures in both full backend pytest steps. Earlier db:verify steps
passed on SQLite and PostgreSQL, so there is **limited historical live PostgreSQL
migration/pipeline evidence**, not a successful full suite or transfer rehearsal.
Current changes must earn a fresh green run. No failure is waived by the new gate.

## CI and branch protection

CI pins Ubuntu 24.04 (avoiding the moving ubuntu-latest image), Python 3.11, Node 22 and PostgreSQL 16 with disposable credentials. It runs
Ruff, mypy, complete backend tests, Alembic migration/drift/preservation checks,
frontend Node tests, both curriculum validators, documentation links/contracts,
actionlint 1.7.7 and whitespace checks. PostgreSQL JUnit evidence must contain the
migration, learner pipeline, transfer and logical restore tests, with no skipped,
failed or errored test cases. No production secret is used. Workflows run on push,
PR, merge-group and manual events without path filters. The always-running aggregate
requires sqlite, postgres and workflow jobs to return exactly success.

Owner steps (no hosted write credentials available in this session):

1. Review these uncommitted changes; create a feature branch and commit/push only
   when authorized. Open a PR. Keep production deployment disabled while testing.
2. In GitHub → repository → Actions, inspect every job and confirm the new
   `Required database checks` is green for the exact PR SHA. Download failure logs
   privately if necessary; correct mandatory failures before proceeding.
3. Repository → Settings → Rules → Rulesets → New ruleset → New branch ruleset
   (or import [.github/main-ruleset.json](../../.github/main-ruleset.json)).
   Name `Protect main`, enforcement Active, target `main`, no bypass actors.
4. Enable Restrict deletions, Block force pushes, Require a pull request before
   merging, one approval, dismiss stale approvals, require approval of the most
   recent reviewable push, and require conversation resolution. No CODEOWNERS file
   is assumed. One independent reviewer is required; a sole maintainer must arrange
   review rather than silently bypass this policy.
5. Enable Require status checks → add exact `Required database checks`, select the
   GitHub Actions app as expected source after its first run, and require branch
   up to date. Save. If the repository plan does not support this rule, document
   that limitation; do not change billing automatically.
6. Inspect existing classic branch protection and inherited organization rules
   for overlap/bypass. Reopen the saved ruleset and verify enforcement. On a
   disposable PR, verify a failing job blocks merge and a skipped/cancelled
   mandatory job cannot produce a green aggregate. Do not force-push/delete main
   to test protection. Do not merge to production just for a deployment test.

The prepared JSON omits an unverified app integration ID; bind the check's source
in the dashboard after the workflow exists. [GitHub ruleset reference](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

## Disposable PostgreSQL staging

Prerequisites: Docker or a separately supplied isolated PostgreSQL 16 database,
PostgreSQL 16 pg_dump/pg_restore, backend dependencies. The test role needs CREATE
SCHEMA and CREATEDB for the logical recovery drill; never use production credentials.
The CI service supplies these privileges. All test-created names are random and
cleaned up; abrupt termination can leave disposable resources for the owner to inspect.

Example on a development host (new temporary container only):

```sh
docker run --rm --name fleng-infra-stage \
  -e POSTGRES_USER=fleng_stage -e POSTGRES_PASSWORD=disposable_stage_only \
  -e POSTGRES_DB=fleng_stage -p 127.0.0.1:15432:5432 \
  --tmpfs /var/lib/postgresql/data postgres:16
# In another terminal, after pg_isready succeeds:
export APP_ENV=development AI_ENABLED=false RESET_DELIVERY=disabled
export TEST_DATABASE_URL=postgresql+asyncpg://fleng_stage:disposable_stage_only@127.0.0.1:15432/fleng_stage
export DATABASE_URL="$TEST_DATABASE_URL"
npm run backend:test -- -q -rs --junitxml=/tmp/fleng-postgres-tests.xml
python3 scripts/check-test-report.py /tmp/fleng-postgres-tests.xml
# Once the drill is complete, stop only this disposable container:
docker stop fleng-infra-stage
```

The suite opens real asyncpg connections; verifies Alembic upgrade/rerun and ORM
schema, auth, UUID relationships, progress/once-only XP, vocabulary, flashcards,
draft isolation and idempotency. The new transfer drill imports a real API-created
SQLite learner snapshot into a fresh PostgreSQL schema, first rolling back a dry
run, then committing, comparing rows, resuming auth/cards and replaying XP safely.
The logical recovery drill creates two empty disposable databases, seeds a learner,
pg_dumps one, restores into the other transactionally, compares every typed row and
checks auth refresh/card resume. It fails if clients are missing; it never falls
back to SQLite. Provider-specific TLS/connectivity/PITR must additionally be tested
on an approved staging service. See [transfer/recovery](../05-database/transfer-and-recovery.md).

## Render owner configuration

Preserve the existing service. Dashboard → Settings → Build & Deploy: repository
Fleng-Fly/fleng-fly, branch main, Python runtime, repository root, build
`python -m pip install ./backend`, start `cd backend && python run.py`, health
`/api/v1/health/ready`. Check the deployed commit against the approved release.
Under Auto-Deploy choose **After CI Checks Pass**, or Off until CI is green and
branch rules are active. Review deploy hooks and manual deploy permissions.
[Render treats neutral/skipped checks as passed](https://render.com/docs/deploys),
so the aggregate must remain fail-closed.

Privately verify APP_ENV, DATABASE_URL, JWT_ACCESS_SECRET, CORS_ORIGIN,
COOKIE_SECURE, COOKIE_SAMESITE, TRUSTED_PROXY_IPS, AI_ENABLED and reset settings.
The current launcher explicitly does **not** migrate PostgreSQL. Apply
`alembic upgrade head` from backend/ against approved staging first; production
migration is an owner-authorized release step, not automatic startup. Do not add
seeding, draft importing or publication to a deploy command. Readiness tests a
query, not complete schema compatibility. Exact schema verification belongs to
migration/drift checks and staging smoke tests.

Do not change the live DATABASE_URL until staging transfer and restore pass and
the owner authorizes cutover. If the current backend uses ephemeral SQLite, HTTP
health does not resolve the existing data-loss risk. Provisioning persistent
storage or changing plans requires separate owner action.

## Netlify owner configuration

Project configuration → Build & deploy: confirm repository main is production,
base frontend, publish . relative to that base, no build command/framework.
Inspect deployed files, assets at desktop/mobile sizes and private-path 404s.
Keep Netlify environment free of backend/database/provider credentials.
Deploy Previews must use static assets or a separate published-only staging API;
never deploy app.preview/reviewer secrets, curriculum JSON, SQLite files or a
production-authenticated backend proxy into a preview. Do not wildcard-allow
`*.netlify.app` in backend CORS. [Preview configuration reference](https://docs.netlify.com/deploy/deploy-types/deploy-previews/).

The committed frontend uses relative `/api/v1`. Live Netlify currently returns
404 there; setting a dashboard API_BASE environment variable alone will not alter
plain static JavaScript. Leave the proxy disabled until tested on isolated staging.
Test an approved staging-only proxy preserving `/api/` end to end: readiness,
register/login/reload/refresh/logout, actual Set-Cookie storage, rejected Origins,
preflights, SSE if enabled, and mobile assets. With same-origin proxy keep Secure
HttpOnly cookies and verify the existing lax policy. For a separately implemented
direct cross-site API, SameSite=None; Secure may be necessary and browser third-party
cookie policies still apply; that path is not implemented by this task.

GitHub branch checks and Render CI gating do not gate Netlify's independent
publication. Confirm preview/production deploy policy in Netlify before relying on
a coordinated release; dashboard changes were not made here.

## Release boundary and remaining risks

After owner review: feature branch → PR → all CI green → rule enforcement verified
→ staging transfer and restore evidence → editorial approval only for a separate
content release → explicit production migration/cutover approval → reviewed merge
→ verify provider deploy SHA/CI gate → readiness plus authenticated smoke with an
approved disposable account → persistence and backup monitoring. Do not manufacture
a production release to complete this diagram.

Still pending: new hosted CI, authenticated classic protection review, enforced
ruleset, Render deployment settings/current DB durability, staged PostgreSQL transfer,
provider recovery rehearsal, tested frontend API routing/cookies/browser/mobile QA,
real optional OpenRouter/SMTP, backup scheduling/encryption/retention, owner cutover
approval. Local Python is 3.14; CI is 3.11, so local green does not prove runner parity.
See [verification evidence](../10-testing/infrastructure-verification-2026-11-14.md).
