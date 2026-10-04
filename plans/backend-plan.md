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
- [x] `GET /api/v1/users/me` with a development-only auth dependency.
- [x] pytest tests for health and users (no database required).
- [x] Ruff + mypy passing.

## Phase 2 — Database & auth

- [x] SQLAlchemy models `User`, `Profile`; Alembic initial migration.
- [ ] Expand models with auth fields (`role`, `email_verified_at`) and
      `RefreshToken`.
- [ ] `auth` module: register, login, refresh (rotation + reuse detection),
      logout. Argon2id hashing; rate limiting.
- [ ] Replace the dev dependency with a real `get_current_user` + `require_role`.
- [ ] `users` module: `PATCH /users/me`, settings.
- [ ] Integration tests against a test PostgreSQL database.

## Phase 3 — Catalog & learning

- [ ] Models: `Course`, `Lesson`, `Exercise`, `ExerciseSubmission`,
      `LessonProgress`.
- [ ] `catalog` module: list/detail courses and lessons (public read, admin
      write).
- [ ] `exercises` module: exercise detail (answer hidden), submit + grade per
      type (start with `MULTIPLE_CHOICE`, `FILL_BLANK`, `MATCH`).
- [ ] `progress` module: lesson start/complete, course progress, summary.
- [ ] Tests for grading, ownership and progress transitions.

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
