# Backend Plan

> Aligns with `plans/roadmap.md`. Stack: Python / FastAPI / SQLAlchemy / Alembic.
> See `docs/backend.md` for the durable design. Legend: ✅ done · 🚧 in progress
> · ⬜ next · 🔴 planned.

## Phase 1 — Bootstrap ✅

- [x] Python project (`pyproject.toml`) + virtualenv setup script.
- [x] FastAPI app factory with `/api/v1` router, CORS from settings.
- [x] `pydantic-settings` configuration (`app/core/config.py`).
- [x] Standard error envelope handlers (`app/core/errors.py`).
- [x] `GET /api/v1/health` (service + database status).
- [x] `GET /api/v1/users/me` (initially with a development-only auth dependency;
      replaced with real authentication in Phase 2).
- [x] pytest tests for health and users (no database required).
- [x] Ruff + mypy passing.

## Phase 2 — Database & auth

- [x] SQLAlchemy models `User`, `Profile`; Alembic initial migration.
- [x] `RefreshToken` and `Progress` models + migration `20261005_1000`.
- [x] `auth` module: register, login, refresh (rotation + reuse detection),
      logout. Argon2id hashing; opaque refresh tokens stored hashed.
- [x] Replace the dev dependency with a real `get_current_user`.
- [x] `GET /progress/me` (read-only, server-derived).
- [ ] Auth fields `role`, `email_verified_at` (+ `require_role`) — deferred.
- [ ] Rate limiting on login/register/refresh.
- [ ] `users` module: `PATCH /users/me`, settings.
- [ ] Integration tests against a test PostgreSQL database.

## Phase 3 — Catalog & learning

- [x] Models `Course`, `Lesson` + migration `20261011_1200_catalog`.
- [x] Idempotent seed (`app/db/seed.py`, `pnpm db:seed`).
- [x] `catalog` module: list/detail courses and lesson read (published-only,
      public read). Admin write and pagination deferred.
- [x] Tests: catalog listing/publication/ordering/404 behaviour.
- [x] Models `Exercise`, `ExerciseSubmission`, `LessonProgress` + migration
      `20261011_1400_exercises`; exercise seed content.
- [x] `exercises` module: public exercises (answer hidden), submit + grade for
      `single_choice` and `text`; explicit `self_check` (no server grading).
- [x] `exercises`/`progress`: lesson start/submit/progress, once-only XP,
      derived exercise and per-course counters on `/progress/me`.
- [x] Tests for grading, answer secrecy, ownership, completion rules and
      idempotency.

## Phase 4 — Vocabulary & gamification

- [ ] Models: `VocabularyWord`, `UserVocabulary`, `FlashcardReview`, `XpEvent`,
      `Streak`, `Achievement`, `UserAchievement`.
- [ ] `vocabulary` module: dictionary search, personal list, due queue, review
      recording (SRS update in a transaction).
- [ ] `gamification` module: XP ledger, level derivation, streak updates,
      achievements (idempotent).
- [ ] Hook lesson completion into progress + gamification within a transaction.

## Phase 5 — Cross-module services

- [ ] `challenges`, `notifications`, `recommendations`, `analytics` modules.
- [ ] `subscriptions` module (deferred until billing is decided).

## Conventions (from `docs/backend.md`)

- Routers thin; services own rules; Pydantic models at every boundary.
- No cross-module access that bypasses services.
- One logical commit per sub-task with its tests.

## Risks / watch-items

- Transaction boundaries across modules (lesson completion) — define the owner
  service explicitly.
- Async SQLAlchemy lazy-loading pitfalls — eager-load relationships that are
  serialized (`selectinload`).
- SRS correctness — add focused unit tests before tuning parameters.
- Rate-limit storage — in-process is fine for dev; revisit with Redis only when
  multi-instance rate limiting is required.

## Implementation checkpoint — 2026-10-18

Backend vocabulary/review workflow, streak/achievement logic, profile updates,
password reset and OpenRouter AI APIs are now implemented. These use simpler
VocabularyItem/Review and daily-activity tables rather than the older proposed
schema names above. Advanced SRS/dictionary search/XP ledger remain future scope.
Tests/static checks pass; live PostgreSQL and OpenRouter integration remain
blocked. See ai-plan.md for completed/blocked/next work. No automatic commits.

## Stabilization — 2026-10-28

- completed: atomic refresh claims and rollback, auth rate limits, bounded Argon2,
  password/reset session invalidation, SQLite learner-write serialization.
- completed: independent-connection regression tests and temporary SQLite
  `npm run dev`/auth/Dashboard/Lessons/restart smoke; see verification report.
- next: optional real PostgreSQL suite/migration drift, real SMTP/OpenRouter checks.
- blocked: live PostgreSQL verification lacks a configured test database;
  no local server/credentials are changed for this phase.
