# Milestones & Status

> Living status board. Keep in sync with `plans/roadmap.md` and the actual repo.
> Legend: ✅ completed · 🚧 in progress · ⛔ blocked · ⬜ next/not started ·
> ❌ cancelled.

Last updated: M2/M3 — authentication + progress vertical slice.

| # | Milestone | Status | Notes |
| - | --------- | ------ | ----- |
| M0 | Repository foundation (docs, map, plans, design) | ✅ completed | |
| M1 | Frontend + FastAPI backend vertical slice | ✅ completed | pnpm workspace, FastAPI, SQLAlchemy/Alembic, health + users, Next.js status indicator |
| M2 | Identity + auth storage | ✅ completed | `User`, `Profile`, `RefreshToken`, `Progress`; argon2id; migration `20261005_1000` |
| M3 | Authentication & progress API + frontend session | ✅ completed | register/login/refresh/logout, read-only `/users/me`, `/progress/me`; `/login`, `/register`, protected `/learn` |
| M4 | Catalog & learning | ⬜ next | courses, lessons, exercises, submissions, progress recording |
| M5 | Vocabulary + SRS | ⬜ | words, user vocabulary, flashcards |
| M6 | Gamification | ⬜ | XP, levels, streaks, achievements |
| M7 | Frontend MVP | ⬜ | app shell + core screens + design system |
| M8 | AI tutor | ⬜ | Python AI layer + tutor + writing correction |
| M9 | Polish & launch | ⬜ | practice depth, notifications, analytics, deploy |

## Known limitations / not yet verified

- **PostgreSQL runtime is unverified in this environment** (no Docker/PostgreSQL
  available). Migrations are verified offline with `pnpm db:sql`; applying them
  to a real PostgreSQL instance and running DB integration tests remain tasks in
  `plans/testing-plan.md`.
- Auth tests use in-memory SQLite, not PostgreSQL.
- Profile editing, email verification, password reset and rate limiting are not
  implemented.

## Blocked

Nothing is blocked. The PostgreSQL runtime checks above are environment
limitations, not project blockers.

## Immediate next actions (M4)

1. Add catalog models (`Course`, `Lesson`, `Exercise`, `ExerciseSubmission`) and
   a `LessonProgress` table, with a new Alembic migration.
2. Implement the `catalog` and `exercises` modules; grade submissions server-side.
3. Record progress from lesson completion (server-derived) and add write
   endpoints; keep the client unable to set its own XP/progress.
4. Apply migrations and run the suite against a real PostgreSQL instance in CI.
5. Deferred auth follow-ups: profile editing, email verification, password
   reset, rate limiting.

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
| M3 | Refresh tokens are opaque random strings stored as SHA-256 hashes (not JWTs) | Nothing to verify client-side; DB lookup by hash; a leak reveals no usable token |
| M3 | `/progress/me` is read-only (no client `PATCH`) | Progress must be server-derived; a client-writable progress endpoint breaks integrity (`docs/security.md`) |
| M3 | Access token stays in memory; refresh token in an HttpOnly cookie | Avoids XSS-exfiltratable long-lived secrets (`localStorage`) |
