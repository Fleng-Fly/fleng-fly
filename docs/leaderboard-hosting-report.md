# Leaderboard and hosting preparation — 2026-11-04

## Delivered

The new protected `/leaderboard.html` screen shares the Dashboard/Lessons
workspace: sidebar, catalog search, notification placeholder, profile and logout.
It displays Top Learners, three podium cards (first place emphasized), a semantic
ranking table and highlighted caller rows. Initials replace external avatar URLs.
Names are inserted as text. Mobile cards stack; the table scrolls horizontally
inside a focusable region. Loading, empty, short-list, service/session error,
retry and success states are implemented. There are no fictional ranking rows.
Notifications remain disabled, as in the existing workspace.

`GET /api/v1/leaderboard?limit=100` requires a session. Existing gamification
code ranks Profile XP descending, user UUID ascending, using SQL window functions
before limiting. Positions are unique and global; lessons and streak do not
break ties. Existing Progress totals and LearningActivity/current-streak policy
supply informational statistics. One batched activity query avoids per-row reads.
The response exposes display name, XP, completed lessons, streak, rank and caller
flag; no email, UUID, password or session data. The caller's entry remains
available outside the requested top 100. No schema migration is needed.

Production uses the same Python/FastAPI process to serve frontend and API.
`backend/run.py` and `Procfile` provide a no-reload start command, Settings-based
port and opt-in proxy trust. Configuration rejects default/short/sample JWT
secrets, insecure production cookies and non-exact/non-HTTPS production CORS
origins. SameSite=None requires Secure cookies in every environment. Missing
production frontend assets fail startup. SQLite defaults stay intact; existing
DATABASE_URL normalization supports PostgreSQL/asyncpg. Environment precedence
and explicit Alembic release workflow are documented in `docs/deployment.md`.

New `GET /api/v1/health/ready` returns 503 on DB failure/timeout; existing `/health`
behavior stays compatible. It does not validate migration version.

## Changed files

- Frontend: `leaderboard.html`, `css/leaderboard.css`, `js/leaderboard.js`,
  `dashboard.html`, `js/api.js`, `js/workspace.js`.
- Backend: `app/modules/gamification/{router,schemas,service}.py`,
  `app/modules/health/router.py`, `app/core/config.py`, `app/main.py`, `run.py`.
- Tests/tooling: `tests/test_leaderboard.py`, `tests/test_production.py`,
  `tests/test_health.py`, `tests/test_frontend.py`,
  `scripts/backend-stabilization-smoke.py`.
- Deployment/config: `Procfile`, `.env.production.example`, `.env.example`,
  `.gitignore`, `README.md`, `docs/deployment.md`.
- Documentation: this report, `docs/{api,architecture,frontend}.md`,
  `project-map/{modules,api-map,data-flow}.md`,
  `plans/{roadmap,milestones,frontend-plan}.md`.

All backend paths above are relative to `backend/`; frontend paths to
`frontend/`. The working tree was clean before implementation. At the initial handoff, no
commit or push was created, per the task instruction. The subsequent user-requested
Git audit groups completed work into logical commits; push remains manual.

## Verification

- Full pytest: **184 passed, 15 skipped**, one existing deprecation warning.
  PostgreSQL-only tests need an actual `TEST_DATABASE_URL`; skips do not count
  as live PostgreSQL verification.
- Ruff and mypy passed, including a separate Ruff check for `backend/run.py`.
- All frontend JS and repository `.mjs` syntax checks passed.
- Existing AI API client tests: 3 passed; SSE parser tests: 7 passed.
- `git diff --check` passed.
- Expanded `scripts/backend-stabilization-smoke.py` passed outside the sandbox:
  actual `npm run dev`, fresh temporary SQLite migrations/catalog, registration,
  login, refresh rotation/reuse, password change/logout, Dashboard/lesson APIs,
  once-only XP, Leaderboard totals, assets, AI status/recommendations and restart
  persistence. No real application database was modified.
- The same smoke script started `backend/run.py` with production configuration:
  static pages, DB readiness, Secure/HttpOnly cookie flags, allowed HTTPS Origin,
  rejection of untrusted Origin and refresh rotation passed. Transport was local
  HTTP; the Secure cookie was explicitly supplied for the refresh request.
  This does not verify real browser HTTPS cookie behavior.

The first sandboxed pytest hung on aiosqlite and was interrupted. Outside the
sandbox it completed. The sandbox also rejects sockets, so the local server
smoke required execution outside it. An existing Starlette/httpx deprecation
warning remains; no dependency change was needed for this task.

## Independent self-review

Reviewed ordering before limiting, deterministic ties, own rank outside the
limit, zero/short/empty results, inactive streak calculation, email/ID exclusion,
DOM text handling, query count, session errors/retry, existing navigation,
production cookie guards, CORS/origin behavior, proxy-header trust, static
packaging, DB migration compatibility and environment precedence. Added typed
service return values and an empty-result regression; removed unrelated HTML
formatting churn and corrected stale Leaderboard/stack documentation.
No new stack, package, database table, service or build step was introduced.

## Not verified and remaining external steps

- Figma source was not provided: exact design comparison is NOT VERIFIED.
- Browser inventory is empty and in-app browser creation fails. Visual layout,
  navigation interaction and responsive behavior at 360/768/desktop are
  NOT VERIFIED; CSS implements those layouts without a browser acceptance claim.
- Live PostgreSQL, actual HTTPS/reverse proxy, OpenRouter provider/SSE, SMTP and
  externally hosted URL are NOT VERIFIED. Existing tests cover their local
  contracts, not external operation.
- Existing repository has Dashboard progress and lesson vocabulary surfaces,
  rather than standalone Progress/Vocabulary pages. Reset API lacks a reset
  frontend; do not enable public reset delivery without a usable destination.

Choose a Python host and managed PostgreSQL, inject production environment
secrets, keep both frontend/backend in the deploy checkout, run Alembic and
optional catalog seed, configure HTTPS and exact proxy trust, start the service,
then exercise the public URL checklist in `docs/deployment.md`.


## Final Git audit

Reviewed all modified and untracked files before staging. No tracked ignored
files, tracked runtime environment/database/key files, provider-token signatures,
or matches for actual local environment secrets were found in publishable files.
Test passwords and example/development configuration values are synthetic.
The ignore rules explicitly cover `fleng.db` and its journals in every directory,
in addition to existing backend/data, environment, cache and log exclusions.
Only the two reviewed environment example files are allowed through the env rule.
Dashboard, Lessons, backend stabilization/SQLite and AI Assistant already exist
in earlier commits; the new commits cover Leaderboard, production hosting and
shared documentation. Branch, remote and existing commit history are preserved.

Final audit quick checks passed: Ruff for app/tests and production launcher,
mypy, syntax checks for 21 JavaScript/tooling files, 3 AI client tests,
7 SSE parser tests, ignore-rule probes and staged/working `git diff --check`.
The full pytest and server smoke results above are from implementation
verification; they were not repeated for this documentation/ignore-only audit.
