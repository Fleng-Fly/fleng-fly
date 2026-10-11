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

## Current status at a glance — M2/M3

Implemented and verified:

- Python virtualenv (backend) + Docker-compose PostgreSQL; root Node scripts.
- FastAPI app at `/api/v1` with CORS, Pydantic settings, error handlers.
- SQLAlchemy async `User`, `Profile`, `RefreshToken`, `Progress` models with two
  Alembic migrations.
- `GET /api/v1/health`.
- Authentication: `POST /auth/register`, `/login`, `/refresh`, `/logout` with
  argon2id, rotating hashed refresh tokens and reuse detection.
- `GET /api/v1/users/me` and `GET /api/v1/progress/me` (Bearer-protected,
  read-only).
- Read-only catalog: `GET /api/v1/courses`, `/courses/{slug}` and `/lessons/{slug}`
  (published content only), with `Course`/`Lesson` models, migration
  `20261011_1200_catalog` and an idempotent seed (`app/db/seed.py`).
- A static HTML/CSS/JS frontend (`frontend/`) served by the same FastAPI app:
  `/index.html`, `/login.html`, `/register.html`, `/dashboard.html`,
  `/courses.html`, `/course.html`, `/lesson.html`, `/settings.html`. In-memory
  access token, automatic refresh, `requireSession` redirect guard, and a live
  backend-status indicator.

Not built: exercises/grading, lesson completion, vocabulary, gamification, AI,
notifications, analytics, deployments.

> Environment note: migrations were verified offline (`pnpm db:sql`); applying
> them to a real PostgreSQL and running DB integration tests remain tasks.
