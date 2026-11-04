# Deployment

Fleng ships as **one FastAPI service containing `backend/` and `frontend/`**.
There is no frontend build or Node process in production. A public deployment
has not been created; the host, database credentials and domain are not supplied.

## Local and production commands

Local development remains `npm run dev`: SQLite preparation and uvicorn reload.
Production uses `backend/run.py` (also declared in the root `Procfile`), binds
`0.0.0.0:$PORT`, and disables reload and proxy trust by default.

On a Python 3.11+ host, keep the entire repository in the deployed checkout.
Install from the repository root with the host's Python environment:

```sh
python -m pip install ./backend
```

Inject the variables below through the hosting secret store, then run this
**release command once**, before starting the web service:

```sh
cd backend
alembic upgrade head
# First deployment only, if you want the existing learning catalog:
python -m app.db.seed
```

Start command from the repository root:

```sh
cd backend && python run.py
```

For a local virtualenv use `backend/.venv/bin/python` / `.venv/bin/alembic`
as appropriate. Do not use `npm run dev`, demo-account seeding, `--reload`, or
`app.db.prepare` as a production release command. No new migration is required
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
| `DATABASE_URL` | Managed PostgreSQL URL; `postgres://` and `postgresql://` select asyncpg |
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

SQLite still works locally. A host may use SQLite only with an explicit durable
volume, an absolute database path and a single application instance. Ephemeral
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
