# Deployment

> Status: **planned**. No deployment exists yet. This document defines the
> intended shape so it can be adopted without rework.

## 1. Topology (initial)

One application deployable plus a database:

```
[ CDN / edge ] → backend (FastAPI)  ──HTTPS──► AI providers
                    │  serves the static frontend at /
                    │  serves REST at /api/v1
                    │ SQLAlchemy/asyncpg
                    ▼
                 PostgreSQL (managed)
```

- **Backend**: FastAPI/uvicorn — serves both the REST API (`/api/v1`) and the
  static HTML/CSS/JS frontend (`/`) from the same origin, so the HttpOnly
  refresh cookie is first-party. Horizontally scalable stateless instances behind
  a load balancer.
- **Frontend**: static files shipped with the backend (no separate Node/CDN
  deployable is required; a CDN may still front the static assets).
- **Database**: managed PostgreSQL with automated backups.
- **AI**: external provider APIs; the backend holds the keys.

## 2. Environments

| Environment | Purpose | Notes |
| ----------- | ------- | ----- |
| Local | development | docker compose: Postgres (+ backend/frontend when containerised) |
| CI | tests | ephemeral Postgres; `AI_PROVIDER=mock` |
| Staging | pre-production | production-like, separate secrets/data |
| Production | users | strict secrets, backups, monitoring |

Environment configuration differs only by env vars; no environment-specific code
branches.

## 3. Local development

```bash
docker compose up -d db   # PostgreSQL
pnpm install              # frontend dependencies
pnpm setup                # backend virtualenv + Python dependencies
pnpm db:migrate           # Alembic
pnpm dev
```

A full `docker compose up` (db + backend + frontend) becomes available once the
apps are containerised.

## 4. Build and release

1. `pnpm setup` (backend virtualenv + dependencies)
2. `pnpm lint && pnpm typecheck && pnpm test`
3. No frontend build step — the static files ship as-is and are served by the
   backend.
4. Run migrations `cd backend && .venv/bin/alembic upgrade head` (never
   `--autogenerate` in production).
5. Deploy frontend and backend; smoke-test `/api/v1/health`.

Rollbacks: backwards-compatible migrations by default; if a migration is
irreversible, document the forward fix.

## 5. Configuration and secrets

- Injected via the platform's secret store into environment variables.
- `.env` never ships in images; `.env.example` documents names only.
- Required production secrets: `APP_ENV=production`, `DATABASE_URL`,
  `CORS_ORIGIN`, `JWT_ACCESS_SECRET`, plus `AI_API_KEY` for the AI milestone.

## 6. Observability

- Structured JSON logs (stdout) collected by the platform.
- Health endpoint (`/api/v1/health`) for liveness/readiness.
- Error tracking added before public launch (provider TBD).
- Metrics: request rate/latency/errors; AI token usage and cost.

## 7. Data and backups

- Automated Postgres backups + tested restore procedure before launch.
- Migrations are committed and applied via a release step, not manually.
- Retention/deletion policy to be finalised (see `docs/database.md`).

## 8. Security in deployment

Per `docs/security.md`: force HTTPS/HSTS, restrict CORS, least-privilege
database credentials, no secrets in images or logs, and review the dependency
surface before launch.

## 9. Open questions

- Hosting provider for the single FastAPI deployable (and whether to front the
  static assets with a CDN).
- Container registry and CI platform.
- Blue/green vs. rolling deploys — revisit at launch scale.
