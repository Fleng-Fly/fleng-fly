# Deployment

Fleng can run as **one FastAPI service containing `backend/` and `frontend/`**.
There is no frontend build or Node process in production. The Netlify site at
<https://fleng.netlify.app> is a separate static-frontend deployment. The user
reports a running FastAPI deployment on free Render with SQLite and
authentication returning 503. Live Render configuration/log details and its URL
have not been supplied for independent verification. A successful static
Netlify deployment alone does not prove a working app.

## Netlify: static frontend only

The root `netlify.toml` sets `[build] base = "frontend"` and `publish = "."`.
Netlify resolves publish relative to base, so the published directory is exactly
`frontend/`, not the repository root. Leave the build command empty. There is
no bundler, build step or frontend package manifest.

The explicit base is necessary to avoid root dependency detection: Netlify
automatically runs pnpm when the base contains `pnpm-lock.yaml`, and this
repository's root lockfile is out of sync with its development tooling manifest.
The frontend needs none of those packages. This isolates static deployment
without changing dependencies or weakening frozen-install checks. See Netlify's
[base/publish definitions](https://docs.netlify.com/build/configure-builds/overview/)
and [dependency detection](https://docs.netlify.com/build/configure-builds/manage-dependencies/).
Do not select the repository root as the publish directory.
Do not add a catch-all SPA redirect: pages are separate HTML files and unknown
URLs and API requests must remain 404 until a backend proxy is enabled.

Only files inside `frontend/` are publishable. Backend sources, migrations,
tests, SQLite files, `.env` files (including example templates), `AGENTS.md`,
documentation, plans, project maps, Git metadata, logs and local configuration
must stay outside that directory. `.gitignore` is not a publication boundary:
inspect the complete frontend tree, including ignored files and symlinks, before
each release. Never copy secrets or private data into it.

Until the FastAPI proxy is configured and verified, authentication, catalog and
user APIs, saved progress and AI are unavailable on Netlify. Static HTML returning
200 does not imply that
protected pages or API-dependent features work in the browser.

After deploying FastAPI with a persistent database (managed PostgreSQL is the
intended production choice), replace the placeholder with its real HTTPS host
and uncomment the existing example in `netlify.toml`:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://YOUR-BACKEND.example.com/api/:splat"
  status = 200
  force = true
```

The `/api/` prefix is intentional: `/api/v1/health` must reach the backend as
`/api/v1/health`. Never point this rule at localhost. Keep the existing frontend
API client and endpoints. Configure backend `CORS_ORIGIN` to the exact frontend
origin (`https://fleng.netlify.app` for this site), secure cookies and trusted
ingress settings, then verify cookie refresh, origin checks and SSE through the
proxy before claiming integration works. Store `OPENROUTER_API_KEY`, database
credentials and JWT secrets only in the backend host's secret store, never in
frontend files or browser-injected Netlify variables.

### Static deployment verification

Before the proxy is enabled, check HTTP responses against the local publish
directory and repeat against the deployed Netlify URL after the user deploys:

| Expected status | Paths |
| --- | --- |
| 200 | `/`, `/index.html`, `/courses.html`, `/dashboard.html`, existing `/css/*.css` and `/js/*.js` assets |
| 404 | `/unknown-page`, `/api/v1/health`, `/backend/app/core/config.py`, `/backend/data/fleng.db`, `/AGENTS.md`, `/.env`, `/.env.production`, `/.env.example`, `/.env.production.example`, `/docs/deployment.md`, `/plans/roadmap.md`, `/project-map/architecture.md`, `/tests/`, `/backend/alembic/env.py`, `/.git/config` |

Inspect the Netlify deploy file list: it must contain only the frontend tree.
Verify that a missing URL returns an actual 404, not `index.html` with 200.
If Netlify CLI is unavailable, use this local static-path check:

```sh
python3 -m http.server 8080 --bind 127.0.0.1 --directory frontend
```

This does not emulate Netlify redirects or prove the public deployment.
After proxy activation, health must return the real backend JSON and readiness
must confirm database access;
the private-file checks must still return 404. An old deployment publishing the
repository root remains exposed until a corrected deployment replaces it.

The tracked `pnpm-lock.yaml` had a trailing `---` creating an empty second YAML
document, not a duplicated package block. Only that marker was removed; package
versions were preserved. Its root importer does not list the `prettier`
devDependency declared by `package.json`; dependency synchronization remains
separate work. The frontend base avoids invoking this root install altogether.

### Local verification — 2026-11-04

- Parsed active TOML and the uncommented proxy example; verified that base plus
  publish resolves exactly to `frontend/`. Netlify CLI was unavailable.
- Inspected all 35 frontend files, including ignored/hidden paths: no symlinks,
  private file types or routing overrides. Secret-pattern and local-credential
  comparisons covered tracked working files, Git index, frontend and 555
  reachable historical blobs without printing values. No confirmed secrets;
  the credential-URL finding was an intentional test fixture.
- Local static HTTP checks passed for 46 paths: required pages and all 25 CSS/JS
  assets returned 200; missing/API/private paths returned 404. This tests the
  publish directory, not Netlify's production routing or proxy behavior.
- `git diff --check`, syntax checks for 17 frontend JS files, 26 existing
  frontend tests, Ruff and mypy (64 source files) passed. Backend pytest passed
  outside the restricted sandbox: 228 passed, 15 PostgreSQL tests skipped;
  existing Starlette/httpx deprecation warning remains. The sandbox run timed
  out. Tests used isolated databases, not the local application SQLite file.
- Separate self-review checked publication boundaries, proxy prefix, lockfile
  semantics, scope and documentation. No backend or UI code was changed.
- No push or production deployment was run. Public exposure remains unverified
  until the corrected Netlify deployment and its file-list/HTTP checks.

## Local and production commands

Local development remains `npm run dev`: SQLite preparation and uvicorn reload.
Production uses `backend/run.py` (also declared in the root `Procfile`), binds
`0.0.0.0:$PORT`, and disables reload and proxy trust by default.

On a Python 3.11+ host, keep the entire repository in the deployed checkout.
Install from the repository root with the host's Python environment:

```sh
python -m pip install ./backend
```

Inject the variables below through the hosting secret store. For **PostgreSQL**,
run this release command once before starting the web service:

```sh
cd backend
alembic upgrade head
# Catalog CLI seed is development-only. For a controlled PostgreSQL catalog
# import, call seed_catalog from an approved maintenance session; no demo accounts.
```

Start command from the repository root:

```sh
cd backend && python run.py
```

For **file-backed SQLite**, the start command itself runs preparation before
Uvicorn: write-access probe (rolled back), `alembic upgrade head`, mapped
schema validation, and the existing catalog seed only if no course exists.
Accounts, refresh sessions and progress are not reset. A failed stage exits
nonzero without opening the HTTP listener. Logs show the resolved SQLite path,
stage, exception class and SQLite error code without SQL parameters/secrets.
Preparation is in the launcher, never the ASGI lifespan; the launcher explicitly
uses one worker. Do not run multiple launcher instances against one SQLite file.
Direct `uvicorn app.main:app` bypasses this preparation and is not the production
start command. PostgreSQL keeps its explicit release migration workflow.

For a local virtualenv use `backend/.venv/bin/python` / `.venv/bin/alembic`
as appropriate. Do not use `npm run dev`, demo-account preparation or `--reload`
for production. No new migration is required
for Leaderboard; it reads existing tables. Back up data before upgrades and
check `alembic current` against `alembic heads` after release.

## Production environment

See [the production template](../.env.production.example). This template is a
reference: it is not loaded automatically. Settings load optional `backend/.env`
and root `.env` (root wins), followed by environment variables (highest priority).
Avoid shipping local `.env` files to the host.

| Variable | Production value |
| --- | --- |
| `APP_ENV` | `production` (exact spelling) |
| `PORT` | Platform-assigned port; launcher reads the same Settings as the API |
| `DATABASE_URL` | Managed PostgreSQL URL (durable storage), or explicit file-backed SQLite for an ephemeral demo; `postgres://` and `postgresql://` select asyncpg |
| `JWT_ACCESS_SECRET` | Unique random secret, at least 32 characters; generate with `python -c 'import secrets; print(secrets.token_urlsafe(48))'` |
| `CORS_ORIGIN` | Exact public HTTPS origin, e.g. `https://fleng.example`, no trailing slash/path; comma-separated if necessary |
| `COOKIE_SECURE` | `true`; enforced in production |
| `COOKIE_SAMESITE` | `lax` for the supported same-origin frontend |
| `TRUSTED_PROXY_IPS` | Empty by default; only actual ingress IPs/networks if forwarding headers are needed |
| `LEARNING_TIMEZONE` | `UTC` or chosen valid IANA timezone, shared by streaks and Leaderboard |
| `AI_ENABLED` | `false` until OpenRouter is configured |
| `OPENROUTER_API_KEY` | Backend secret, needed only for AI |
| `OPENROUTER_MODEL` | Valid `provider/model` identifier, needed only for AI |
| `RESET_DELIVERY` | `disabled`; enable SMTP only after configuring and testing delivery |

Durable SQLite hosting requires an explicit durable volume, an absolute database
path and a single application instance. Free Render SQLite is supported only as
an ephemeral demo with possible loss of accounts and progress. Ephemeral
service storage loses SQLite data on replacement; PostgreSQL is the intended
online database. Follow the database provider's asyncpg-compatible TLS settings;
validate the real connection and migrations before accepting users. There is no
silent fallback from PostgreSQL to SQLite.

## HTTPS, authentication and proxies

Serve frontend and API from the **same HTTPS URL**. All frontend requests use
relative `/api/v1`; no frontend environment injection is needed. Refresh cookies
are HttpOnly, Secure, host-only, scoped to `/api/v1/auth`; access JWTs stay in
browser memory. No cookie domain setting is needed for this topology.

The auth origin guard accepts the request's own origin or `CORS_ORIGIN`.
Behind TLS termination, configure the exact public HTTPS origin even if the
upstream request is HTTP. CORS is not a replacement for the cookie-endpoint
origin guard. Wildcards and HTTP origins are rejected in production.

Preserve Host and stream AI SSE responses without proxy buffering. To use
forwarded scheme/client IP for authentication rate limits, set
`TRUSTED_PROXY_IPS` to the actual ingress IPs/networks and ensure the ingress
replaces incoming client forwarding headers. Never set it to `*` on a directly
reachable service. Without a trusted proxy, clients share the ingress peer-IP
quota; email quotas remain per account. Restrict direct upstream access at the
host. HTTPS termination and ingress settings must be verified on the chosen host.

AI failure/disabled configuration does not block lessons or rankings. Check
`GET /api/v1/ai/status` with a session, then a real SSE turn after enabling AI.
The reset API exists, but there is no reset-password frontend page in this
checkout: do not enable public reset email until a usable `RESET_URL` is provided.

## Health and release verification

- `GET /api/v1/health`: existing HTTP 200 liveness response with database status.
- `GET /api/v1/health/ready`: HTTP 200 when `SELECT 1` succeeds; HTTP 503 on
  database error or a five-second probe timeout. It checks connectivity, not
  schema version; migrations remain a release prerequisite.
- Startup fails in production if the static frontend directory is missing.
  If deploying it elsewhere, supply `FRONTEND_DIR` as an absolute path.

After deployment, check readiness, `/`, `/login.html`, `/leaderboard.html`, CSS
and JS. Register/login; reload a protected page to exercise cookie refresh;
complete a lesson; check Dashboard XP, streak and Leaderboard; test logout and
that an untrusted Origin is rejected. Test the AI SSE path if enabled. Confirm
state survives a service restart and perform a PostgreSQL backup/restore drill.

## Remaining external work

Choose a Python web host and managed PostgreSQL, supply secrets, configure HTTPS
and proxy trust, run the release command, start the service and run the checks
above against its public URL. Live PostgreSQL, TLS/proxy behavior, provider SSE,
SMTP and public URL access are **NOT VERIFIED** in this environment.

## Free Render SQLite configuration

Keep Root Directory empty (repository root), runtime Python, Build Command
`python -m pip install ./backend`, Start Command `cd backend && python run.py`,
and Health Check Path `/api/v1/health/ready`. Do not put migrations only in Build
Command: runtime storage can be replaced independently. Set `APP_ENV=production`,
`DATABASE_URL=sqlite+aiosqlite:///./data/fleng.db`, a host-stored random
`JWT_ACCESS_SECRET`, `COOKIE_SECURE=true`, `COOKIE_SAMESITE=lax` and the exact
public HTTPS frontend origin in `CORS_ORIGIN`. Let Render provide `PORT`. Retain
the entire checkout for static frontend and Alembic files. The SQLite path
resolves to `backend/data/fleng.db` regardless of cwd; use an absolute path for
an intentionally chosen writable location. Never use `:memory:`.

Render's [free service documentation](https://render.com/docs/free) states that
local SQLite files are lost on service restart, redeploy or spin-down. A plain
Python process restart with the same file preserves data; a Render service
restart is not equivalent. This fix recreates schema/catalog on an empty disk,
not lost user data. Persistent disks are unavailable for free web services;
use durable external PostgreSQL for retained accounts/progress.

No Render connector, service URL or dashboard configuration was available in
this session. These are reviewed deployment settings, not a claim that the live
service has been inspected or repaired. See [SQLite startup verification](render-sqlite-startup.md).
