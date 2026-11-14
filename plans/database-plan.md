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
- [x] Seed: two sample courses (A1, B1) and seven lessons.
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
- [x] PostgreSQL remains configurable with manual migrations. Production SQLite
      now prepares automatically (see the 2026-11-04 update below).
- [x] File-backed migration/idempotency/preservation tests added.
- [x] HTTP auth/cookie/lesson/XP/Dashboard checks passed, including a full restart.
- [x] Firefox login, Dashboard layouts and navigation checked at 360/768/1440 px.
- [ ] Live PostgreSQL migration verification remains dependent on an available server.


## Render SQLite startup fix — 2026-11-04

- **Completed:** production launcher performs SQLite write probe, existing Alembic
  upgrades, mapped-schema validation and empty-catalog seed before single-worker
  Uvicorn. No user-data reset; PostgreSQL release migrations remain explicit.
- **Completed:** regression coverage for fresh production disk, registration,
  login, refresh, Dashboard APIs, XP/session/account persistence on process restart,
  unwritable files/directories, invalid path, memory DB and incorrectly stamped DB.
- **Completed:** existing checks, separate self-review, docs/project-map update.
- **Next / externally blocked:** live Render settings/log and public HTTPS checks
  need the service URL/configuration; live PostgreSQL needs TEST_DATABASE_URL.
- **Limitation:** free Render storage is ephemeral; process-only restart evidence
  with the same SQLite file does not establish persistent hosting storage.

Verification: `docs/render-sqlite-startup.md`. Prepared for deployment; no push.

## Persistence and CI — 2026-11-14

- **Completed:** read-only inventory of the populated local database; drafts absent
  by design, existing user data intact; no production database inspected.
- **Completed:** select managed PostgreSQL as production target, retain local SQLite
  and current production URL; document SQLite persistent-disk alternative.
- **Completed:** online SQLite backup helper and WAL round-trip verification;
  npm draft import/isolated preview commands; mandatory SQLite/PostgreSQL CI definition.
- **Completed:** migration-based idempotency/FK/learner/card preservation test;
  persistence/backup/restore/transfer/rollback and external hosting gate documentation.
- **Next:** execute PostgreSQL CI and staging transfer rehearsal; implement/review the
  typed cross-engine transfer described in the runbook before production approval.
- **External / not enabled:** GitHub required branch checks, Render After CI Checks
  Pass, durable storage plan, off-host backups and production recovery drill.
- **Not authorized:** production migration/URL switch and content publication.
- **Finalization:** one infrastructure commit and ordinary push to main separately
  authorized after final checks; production operations remain separate.

## Final infrastructure integration — 2026-11-14

- **Completed locally:** typed SQLite-to-PostgreSQL utility, mandatory backup, dry-run rollback, strict empty-target policy, UTC/UUID/JSON preservation, FK/row reconciliation and refusal/rollback regression tests.
- **Completed locally:** real asyncpg transfer test and pg_dump/pg_restore test definitions; docs/contracts, actionlint and no-skips PostgreSQL JUnit gate in existing CI; importable main ruleset; owner runbooks and self-review.
- **Observed live:** Render readiness 200/database up; Netlify homepage 200/API 404; GitHub main protected=false/no rulesets; original workflow full suites failed although db:verify passed.
- **Blocked externally:** no staging URL/server/client/container or hosting write credentials here; full hosted failure logs require auth. New live transfer, provider restore and revised hosted CI are not verified.
- **Next:** owner PR/run, resolve runner failures, activate ruleset/Render CI gate, stage transfer and provider recovery, test Netlify routing and cookies.
- **Not authorized:** automatic commit/push, production release/URL cutover/restore, paid services or draft publication. This supersedes the earlier checkpoint commit/push authorization for this task.

## Default local courses — 2026-11-14

- **Completed:** npm dev uses existing local SQLite with pre-change backup and idempotent A0–B2 draft import; ordinary accounts see seven courses through authenticated loopback-only routes.
- **Completed:** reuse current catalog/grading/progress services and private preview; reject hosted/production and non-file-SQLite dev configuration.
- **Next:** teacher/translator review and separate production publication authorization remain pending. No production database connection or content publication was performed.
