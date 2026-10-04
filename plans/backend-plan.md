# Backend Plan

> Aligns with `plans/roadmap.md` Stage 1 and beyond. Stack: NestJS + Prisma +
> PostgreSQL. See `docs/backend.md` for the durable design.

## Phase 1 — Bootstrap

- [ ] Root workspace manifests + `@fleng/backend` package.
- [ ] NestJS bootstrap: `main.ts`, `app.module.ts`, `config/` (validated env),
      Pino logging, global `ValidationPipe`, exception filter, `helmet`, CORS.
- [ ] `PrismaModule`/`PrismaService` with connection lifecycle and graceful
      shutdown.
- [ ] `/api/v1/health` endpoint.
- [ ] Base error classes and the standard error envelope. *(M1)*

## Phase 2 — Identity & users

- [ ] Prisma models: `User`, `Profile`, `RefreshToken`. *(M2)*
- [ ] `auth` module: register, login, refresh (rotation + reuse detection),
      logout, `GET /auth/me`. Argon2id hashing; rate limiting on auth. *(M3)*
- [ ] `users` module: `GET/PATCH /users/me`, settings, account delete policy.
- [ ] Guards: `JwtAuthGuard`, `RolesGuard`, `@CurrentUser()` decorator.
- [ ] Tests: unit (services, token logic) + API e2e (auth flows).

## Phase 3 — Catalog & learning

- [ ] Models: `Course`, `Lesson`, `Exercise`, `ExerciseSubmission`,
      `LessonProgress`. *(M4)*
- [ ] `catalog` module: list/detail courses and lessons (public read, admin
      write).
- [ ] `exercises` module: exercise detail (answer hidden), submit + grade per
      type (start with `MULTIPLE_CHOICE`, `FILL_BLANK`, `MATCH`).
- [ ] `progress` module: lesson start/complete, course progress, summary.
- [ ] Tests for grading, ownership and progress transitions.

## Phase 4 — Vocabulary & gamification

- [ ] Models: `VocabularyWord`, `UserVocabulary`, `FlashcardReview`,
      `XpEvent`, `Streak`, `Achievement`, `UserAchievement`. *(M5, M6)*
- [ ] `vocabulary` module: dictionary search, personal list, due queue,
      review recording (SRS update in a transaction).
- [ ] `gamification` module: XP ledger, level derivation, streak updates,
      achievement evaluation (idempotent).
- [ ] Hook lesson completion into progress + gamification within a transaction.

## Phase 5 — Cross-module services

- [ ] `challenges` module (participate, leaderboard).
- [ ] `notifications` module (in-app feed).
- [ ] `recommendations` module (rule-based first; AI later).
- [ ] `analytics` module (event recording).
- [ ] `subscriptions` module (deferred until billing is decided).

## Conventions (from `docs/backend.md`)

- Controllers thin; services own rules; repositories own Prisma.
- No cross-module repository access.
- DTOs at every boundary; never return Prisma models.
- One logical commit per sub-task with its tests.

## Risks / watch-items

- Transaction boundaries across modules (lesson completion) — define the owner
  service explicitly.
- SRS correctness — add focused unit tests before tuning parameters.
- Rate-limit storage — in-memory is fine for dev; revisit with Redis only if
  multi-instance rate limiting is required.
