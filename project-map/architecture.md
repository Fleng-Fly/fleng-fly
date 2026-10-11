# Project Map — Architecture

> Status: M2/M3 implemented (Phase A: static frontend served by FastAPI).
> Canonical detail: `docs/architecture.md`.

## System diagram (current)

```
User
 ↓  HTTPS
FastAPI (Python) 🟢  — one deployable on :3001
  • serves the static frontend at /  🟢  (frontend/: HTML, CSS, vanilla JS)
  • serves REST /api/v1              🟢
  • main.py: CORS, error handlers, /api/v1 router, StaticFiles mount 🟢
  • modules: health 🟢, auth 🟢, users 🟢, progress 🟢
  • infrastructure: core (config, errors, schemas) 🟢, db (models, session) 🟢,
    api (router, deps) 🟢
  • planned modules (all 🔴): catalog, content, exercises, vocabulary,
             gamification, challenges, recommendations, ai,
             notifications, subscriptions, analytics
  ↓  SQLAlchemy 2 (async) → asyncpg
PostgreSQL 🟢 (models + 2 Alembic migrations committed; runtime needs a running instance)

Backend ↔ AI  (Python AI layer) 🔴  — not built; no AI module or dependency yet
```

## Frontend (static)

```
frontend/ (no build step)
  • pages:  index.html, login.html, register.html, dashboard.html, settings.html
  • styles: css/app.css (design tokens from design/)
  • scripts (ES modules):
      js/api.js       — fetch wrapper, in-memory access token, 401 refresh
      js/errors.js    — user-facing error messages
      js/session.js   — loadSession / requireSession
      js/layout.js    — shared header, backend-status badge, DOM helper
      js/{home,login,register,dashboard,settings}.js
```

Served by `app.main` via `StaticFiles(html=True)` mounted at `/` after the API
router, so `/api/v1` and `/docs` take precedence. The browser talks only to the
relative `/api/v1`; there is no frontend environment configuration.

## Layer boundaries

| From → To | Allowed? | Notes |
| --------- | -------- | ----- |
| Browser (static pages) → Backend API | ✅ | HTTP/JSON only, via `frontend/js/api.js` |
| Frontend → Database | ❌ | Never |
| Frontend → AI provider | ❌ | Keys are server-side |
| Backend → Database | ✅ | Only via SQLAlchemy |
| Backend → AI layer | 🔴 | Planned, in-process Python import |
| AI layer → Database | ❌ | Layer is persistence-free |
| Module → other module's service | ✅ | Import the service, not internals |
| Module → another module's ORM models | ⚠️ | Prefer going through services |

## Trust boundaries

- Browser is untrusted: validate everything at the API edge (Pydantic).
- The static frontend renders server/user text with `textContent` (never
  `innerHTML`).
- AI provider output will be untrusted: validate against a schema before use.
- The database is trusted but access is least-privilege.

## Deployment units (target)

1. `backend` — FastAPI app serving the API **and** the static frontend.
2. AI layer — Python package inside the backend (not deployed separately).

## Evolution rules

- Keep the monolith until evidence justifies extraction (`docs/architecture.md §8`).
- Any new top-level directory must be added to this map and to `README.md`.
- New backend modules must be added to `modules.md` and `api-map.md`.
