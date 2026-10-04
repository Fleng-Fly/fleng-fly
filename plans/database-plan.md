# Database Plan

> Aligns with `plans/roadmap.md`. Model details: `docs/database.md`.

## Approach

- Add tables **per stage**, owned by the module that uses them. Do not create
  the full schema upfront (avoids unused tables and premature constraints).
- Prisma Migrate; migrations are committed and reviewed.
- Integrity in the database: FKs, unique constraints, not-null, checks.
- Naming: tables/columns via Prisma defaults (`snake_case` in DB, `camelCase` in
  Prisma/TS) — confirm convention at implementation time.

## Stage 1 — Identity & users

- [ ] `User`, `Profile`, `RefreshToken`.
- [ ] Unique `User.email`; unique `RefreshToken.tokenHash`; FK to user with
      cascade on user deletion.
- [ ] Seed: one admin user for local development (dev only, not production).

## Stage 2 — Learning

- [ ] `Course`, `Lesson`, `Exercise`, `ExerciseSubmission`, `LessonProgress`.
- [ ] Unique `(courseId, slug)`, `(userId, lessonId)`; ordered indexes.
- [ ] Seed: a small sample course with mixed exercise types.

## Stage 3 — Vocabulary & gamification

- [ ] `VocabularyWord`, `UserVocabulary`, `FlashcardReview`.
- [ ] `XpEvent`, `Streak`, `Achievement`, `UserAchievement`.
- [ ] Unique `(userId, wordId)`, `(userId, achievementId)`; index `(userId, dueAt)`.

## Stage 4 — Platform

- [ ] `Challenge`, `ChallengeParticipant`.
- [ ] `AIConversation`, `AIMessage`.
- [ ] `Notification`.
- [ ] `Subscription` (deferred until billing is decided).

## Cross-cutting tasks

- [ ] Backup/restore tested before launch.
- [ ] Decide soft-delete vs. hard-delete policy for `User`.
- [ ] Decide analytics storage (in Postgres vs. elsewhere).

## Risks / watch-items

- Over-indexing early: add indexes with a query in mind, not speculatively.
- Migration reversibility: prefer additive, backwards-compatible migrations.
- Never edit applied migrations; always add a new one.
