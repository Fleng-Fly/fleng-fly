# Database Plan

> Aligns with `plans/roadmap.md`. Model details: `docs/database.md`.
> Legend: ✅ done · ⬜ next · 🔴 planned.

## Approach

- Add tables **per stage**, owned by the module that uses them. Do not create
  the full schema upfront (avoids unused tables and premature constraints).
- SQLAlchemy 2 declarative models in `backend/app/db/models.py`; migrations via
  Alembic (`backend/alembic/`).
- Integrity in the database: FKs, unique constraints, not-null, defaults.
- Naming: snake_case tables/columns; JSON is camelCase at the API boundary only.
- Never edit an applied migration; add a new one.

## Stage 1 — Identity & users ✅

- [x] `User`, `Profile` models.
- [x] Unique `users.email`; unique `profiles.user_id`; FK with `ON DELETE CASCADE`.
- [x] Initial Alembic migration `20261004_1200_init`.
- [x] `RefreshToken` (`token_hash` unique, chain via `replaced_by_id`) +
      `Progress` aggregate; migration `20261005_1000_auth_progress`.
- [ ] Auth fields on `User` (`role`, `email_verified_at`) — deferred until RBAC
      or email verification is needed.
- [ ] Seed: one admin user for local development (dev only, not production).

## Stage 2 — Learning ✅

- [x] `Course`, `Lesson` (migration `20261011_1200_catalog`).
- [x] Unique `courses.slug`, globally unique `lessons.slug`, index
      `lessons.course_id`, CEFR `level` check constraint.
- [x] Seed: two sample courses (A1, B1) with three lessons each.
- [x] `Exercise`, `ExerciseSubmission`, `LessonProgress` (migration
      `20261011_1400_exercises`).
- [x] Unique `exercises.slug`, `(user_id, exercise_id)` and
      `(user_id, lesson_id)`; exercise `type` check constraint; ordered indexes.
- [x] Seed exercises (all three types) with correct/incorrect paths.

## Stage 3 — Vocabulary & gamification ⬜

- [ ] `VocabularyWord`, `UserVocabulary`, `FlashcardReview`.
- [ ] `XpEvent`, `Streak`, `Achievement`, `UserAchievement`.
- [ ] Unique `(user_id, word_id)`, `(user_id, achievement_id)`; index
      `(user_id, due_at)`.

## Stage 4 — Platform 🔴

- [ ] `Challenge`, `ChallengeParticipant`.
- [ ] `AIConversation`, `AIMessage`.
- [ ] `Notification`.
- [ ] `Subscription` (deferred until billing is decided).

## Cross-cutting tasks

- [ ] Backup/restore tested before launch.
- [ ] Decide soft-delete vs. hard-delete policy for `User`.
- [ ] Decide analytics storage (in Postgres vs. elsewhere).
- [ ] Integration test suite with a test database (apply migrations in CI).

## Risks / watch-items

- Over-indexing early: add indexes with a query in mind, not speculatively.
- Migration reversibility: prefer additive, backwards-compatible migrations.
- Async lazy-loading: eager-load relationships used in serialization.

## Implementation checkpoint — 2026-10-18

Revision 20261018_1200 adds vocabulary/reviews, daily activity, deterministic
achievement definitions/awards, reset tokens, persistent quota windows and AI
conversations/messages/usage plus CEFR/language profile fields. These actual
schemas supersede the older proposed Stage 3/4 model names above. Offline SQL
compiles; live migration remains blocked by unavailable PostgreSQL. Opt-in
TEST_DATABASE_URL tests validate the full chain and ORM drift in temporary schemas.

## Local SQLite startup — 2026-10-22

- [x] SQLite is the local default; relative paths are rooted at backend/.
- [x] Dev workflow upgrades an existing file safely and seeds only an empty catalog.
- [x] Alembic uses the application engine and SQLite connection configuration.
- [x] PostgreSQL remains configurable; no automatic production migrations/seeding.
- [x] File-backed migration/idempotency/preservation tests added.
- [x] HTTP auth/cookie/lesson/XP/Dashboard checks passed, including a full restart.
- [x] Firefox login, Dashboard layouts and navigation checked at 360/768/1440 px.
- [ ] Live PostgreSQL migration verification remains dependent on an available server.
