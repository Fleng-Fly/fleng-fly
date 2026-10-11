# Milestones & Status

> Living status board. Keep in sync with `plans/roadmap.md` and the actual repo.
> Legend: ✅ completed · 🚧 in progress · ⛔ blocked · ⬜ next/not started ·
> ❌ cancelled.

Last updated: M4 — catalog read vertical slice (courses + lessons) landed;
Phase A (static frontend served by FastAPI) complete.

| # | Milestone | Status | Notes |
| - | --------- | ------ | ----- |
| M0 | Repository foundation (docs, map, plans, design) | ✅ completed | |
| M1 | Frontend + FastAPI backend vertical slice | ✅ completed | pnpm workspace, FastAPI, SQLAlchemy/Alembic, health + users, Next.js status indicator |
| M2 | Identity + auth storage | ✅ completed | `User`, `Profile`, `RefreshToken`, `Progress`; argon2id; migration `20261005_1000` |
| M3 | Authentication & progress API + frontend session | ✅ completed | register/login/refresh/logout, read-only `/users/me`, `/progress/me` |
| M3a | Phase A: static frontend served by FastAPI | ✅ completed | Next.js removed; `frontend/` HTML/CSS/JS; landing/login/register/dashboard/settings; same-origin CSRF fix |
| M4 | Catalog & learning | 🚧 in progress | ✅ courses + lessons read API, seed, frontend pages; ⬜ exercises/grading, lesson completion, progress writes |
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

## Immediate next actions (M4, continued)

1. ✅ Catalog models (`Course`, `Lesson`) + migration `20261011_1200_catalog` and
   idempotent seed (`app/db/seed.py`).
2. ✅ `catalog` module: published-only list/detail/lesson reads with tests.
3. ⬜ Add `Exercise`, `ExerciseSubmission` and `LessonProgress` + migration;
   implement the `exercises` module and grade submissions server-side.
4. ⬜ Lesson start/complete; record progress (server-derived). Keep the client
   unable to set its own XP/progress.
5. ⬜ Apply migrations and run the suite against a real PostgreSQL instance in CI.
6. Deferred auth follow-ups: profile editing, email verification, password
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
| M3a | **Frontend replaced with plain HTML/CSS/JS served by FastAPI** | No build step; one deployable; first-party cookies; smaller, understandable UI (`AGENTS.md` 1–2) |
| M3a | Same-origin requests accepted by the CSRF Origin check | Browsers send `Origin` on same-origin POSTs; the static UI shares the API origin |
| M4 | Lesson `slug` is **globally** unique (not per course) | `GET /lessons/{slug}` has no course context; global uniqueness avoids ambiguity |
| M4 | Lesson `theory` is plain text with light markup (`## `, `- `), rendered via `textContent` | Keeps content authoring simple and prevents stored/rendered HTML/XSS |
| M4 | Catalog read endpoints are public; catalog **pages** are behind `requireSession` | Content is not sensitive; the UI stays part of the signed-in learning flow |
