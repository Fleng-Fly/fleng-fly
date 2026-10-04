# Project Map

Living map of the Fleng repository. It must stay close to reality:
when a module, flow, API or dependency changes, update the relevant file here
**in the same commit** (`AGENTS.md` rule 5).

## Files

| File | Answers |
| ---- | ------- |
| `architecture.md` | How the system is shaped and how layers interact |
| `modules.md` | What each module is and its dependencies |
| `data-flow.md` | How data moves through key flows |
| `api-map.md` | Condensed endpoint map |
| `dependencies.md` | Dependency rules, installed and planned libraries |

## Status legend

- 🟢 implemented · 🟡 partially implemented · 🔴 documented only (not built)

## Current status at a glance — M1

Implemented and verified:

- pnpm workspace (frontend) + Python virtualenv (backend) + Docker-compose PostgreSQL.
- FastAPI app at `/api/v1` with CORS, Pydantic settings, error handlers.
- SQLAlchemy async `User` + `Profile` models with an Alembic migration.
- `GET /api/v1/health` and `GET /api/v1/users/me` (dev-only auth stub).
- Next.js app (`/`, `/learn`, `/login`) with a typed API client, TanStack Query
  and a live backend-status indicator.

Not built: authentication, catalog/lessons, vocabulary, gamification, AI,
notifications, analytics, deployments.
