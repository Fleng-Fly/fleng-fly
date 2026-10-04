# Milestones & Status

> Living status board. Keep in sync with `plans/roadmap.md` and the actual repo.
> Legend: ✅ completed · 🚧 in progress · ⛔ blocked · ⬜ next/not started ·
> ❌ cancelled.

Last updated: M1 — Frontend + FastAPI backend.

| # | Milestone | Status | Notes |
| - | --------- | ------ | ----- |
| M0 | Repository foundation (docs, map, plans, design) | ✅ completed | |
| M1 | Frontend + FastAPI backend vertical slice | ✅ completed | pnpm workspace, FastAPI, SQLAlchemy/Alembic, health + users (dev stub), Next.js status indicator |
| M2 | Database: full identity + auth | ⬜ next | `RefreshToken`, auth fields, argon2 |
| M3 | Authentication & profiles | ⬜ next | register/login/refresh/logout, replace dev stub |
| M4 | Catalog & learning | ⬜ | courses, lessons, exercises, submissions, progress |
| M5 | Vocabulary + SRS | ⬜ | words, user vocabulary, flashcards |
| M6 | Gamification | ⬜ | XP, levels, streaks, achievements |
| M7 | Frontend MVP | ⬜ | app shell + core screens + design system |
| M8 | AI tutor | ⬜ | Python AI layer + tutor + writing correction |
| M9 | Polish & launch | ⬜ | practice depth, notifications, analytics, deploy |

## Blocked

Nothing is blocked.

## Immediate next actions (M2–M3)

1. Add `RefreshToken` + auth fields (`role`, `email_verified_at`) with a new
   Alembic migration.
2. Implement the `auth` module (register/login/refresh/logout) with argon2id.
3. Replace the development auth dependency with a real `get_current_user`.
4. Add integration tests against a test PostgreSQL database.

## Decisions log

| Date | Decision | Rationale |
| ---- | -------- | --------- |
| Foundation | Modular monolith | Simplicity, team consistency (`AGENTS.md` 9) |
| Foundation | PostgreSQL | Relational integrity + JSONB flexibility |
| Foundation | pnpm workspace (frontend) | Efficient JS monorepo without extra tooling |
| M1 | **Backend rewritten in Python / FastAPI** | Explicit product decision; SQLAlchemy 2 async + Alembic + Pydantic |
| M1 | **FastAPI + Python is the only backend stack finalized** | NestJS/Express/TypeScript backend is forbidden; TypeScript stays frontend-only (`AGENTS.md` backend stack rules) |
| M1 | Backend runs in its own virtualenv, orchestrated by root Node scripts | Polyglot repo without adding Turborepo/Nx |
| M1 | Database-unavailable errors map to `503` (including asyncpg `OSError`) | Honest availability signal; keeps `/health` informative |
