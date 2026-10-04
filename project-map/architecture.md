# Project Map — Architecture

> Status: M1 implemented. Canonical detail: `docs/architecture.md`.

## System diagram (current)

```
User
 ↓
Frontend (Next.js, TypeScript) 🟢
  • routes: /, /learn, /login
  • API client: src/lib/api/client.ts
  • state: TanStack Query
 ↓  HTTPS · REST /api/v1   (default http://localhost:3001/api/v1)
FastAPI (Python) 🟢
  • main.py: CORS, error handlers, /api/v1 router
  • modules: health 🟢, users 🟢 (dev auth stub)
  • infrastructure: core (config, errors, schemas) 🟢, db (models, session) 🟢,
    api (router, deps) 🟢
  • planned modules (all 🔴): auth, catalog, content, exercises, vocabulary,
             progress, gamification, challenges, recommendations, ai,
             notifications, subscriptions, analytics
 ↓  SQLAlchemy 2 (async) → asyncpg
PostgreSQL 🟢 (models + Alembic migration committed; runtime needs a running instance)

Backend ↔ AI  (Python AI layer) 🔴  — not built; no AI module or dependency yet
```

## Layer boundaries

| From → To | Allowed? | Notes |
| --------- | -------- | ----- |
| Frontend → Backend API | ✅ | HTTP/JSON only, via `src/lib/api` |
| Frontend → Database | ❌ | Never |
| Frontend → AI provider | ❌ | Keys are server-side |
| Backend → Database | ✅ | Only via SQLAlchemy |
| Backend → AI layer | 🔴 | Planned, in-process Python import |
| AI layer → Database | ❌ | Layer is persistence-free |
| Module → other module's service | ✅ | Import the service, not internals |
| Module → another module's ORM models | ⚠️ | Prefer going through services |

## Trust boundaries

- Browser is untrusted: validate everything at the API edge (Pydantic).
- AI provider output will be untrusted: validate against a schema before use.
- The database is trusted but access is least-privilege.

## Deployment units (target)

1. `frontend` — Next.js app.
2. `backend` — FastAPI app.
3. AI layer — Python package inside the backend (not deployed separately).

## Evolution rules

- Keep the monolith until evidence justifies extraction (`docs/architecture.md §8`).
- Any new top-level directory must be added to this map and to `README.md`.
- New backend modules must be added to `modules.md` and `api-map.md`.
