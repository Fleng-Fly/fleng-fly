# Database

> Status: **M2 implemented** for `User`, `Profile`, `RefreshToken` and `Progress`,
> plus the catalog (`Course`, `Lesson`) and exercises (`Exercise`,
> `ExerciseSubmission`, `LessonProgress`) and learning/AI extensions described below.
> Engines: SQLite for local development, PostgreSQL available via DATABASE_URL.
> Access: SQLAlchemy 2 (async) from the backend only;
> migrations via Alembic.

## 0. Implemented

Identity, authentication sessions and aggregate progress exist (SQLAlchemy models
in `backend/app/db/models.py`):

- **`User`** (`users`) — `id` (UUID PK), `email` (unique), `password_hash`
  (argon2id), `created_at`, `updated_at`.
- **`Profile`** (`profiles`) — `id` (UUID PK), `user_id` (unique FK → `users`,
  `ON DELETE CASCADE`), `display_name`, `level` (int, default 1), `xp` (int,
  default 0), `created_at`, `updated_at`.
- **`RefreshToken`** (`refresh_tokens`) — `id` (UUID PK), `user_id` (FK → `users`,
  `ON DELETE CASCADE`, indexed), `token_hash` (unique, SHA-256 hex), `expires_at`,
  `revoked_at`, `replaced_by_id` (self FK → `refresh_tokens`, `SET NULL`),
  `created_at`.
- **`Progress`** (`progress`) — `id` (UUID PK), `user_id` (unique FK → `users`,
  `ON DELETE CASCADE`), `lessons_started`, `lessons_completed`, `study_minutes`,
  `last_activity_at`, `created_at`, `updated_at`.
- **`Course`** (`courses`) — `id` (UUID PK), `slug` (unique), `title`,
  `description`, `level` (CEFR `A1`–`C2`, check constraint), `position`,
  `is_published` (default false), `created_at`, `updated_at`.
- **`Lesson`** (`lessons`) — `id` (UUID PK), `course_id` (FK → `courses`,
  `ON DELETE CASCADE`, indexed), `slug` (unique, global), `title`, `summary`,
  `theory` (text), `position`, `estimated_minutes`, `is_published` (default
  false), `created_at`, `updated_at`.
- **`Exercise`** (`exercises`) — `id` (UUID PK), `lesson_id` (FK → `lessons`,
  `ON DELETE CASCADE`, indexed), `slug` (unique), `position`, `type`
  (`single_choice`|`text`|`self_check`, check constraint), `prompt`, `points`
  (default 1), `options` (JSON), `correct_option_id`, `accepted_answers` (JSON),
  `model_answer`, `explanation`, `created_at`, `updated_at`.
- **`ExerciseSubmission`** (`exercise_submissions`) — `id` (UUID PK), `user_id`
  (FK → `users`, indexed), `exercise_id` (FK → `exercises`, indexed), `answer`,
  `is_correct`, `completed`, `xp_awarded`, `attempts`, `submitted_at`,
  `updated_at`; unique `(user_id, exercise_id)`.
- **`LessonProgress`** (`lesson_progress`) — `id` (UUID PK), `user_id` (FK →
  `users`, indexed), `lesson_id` (FK → `lessons`, indexed), `status`
  (`in_progress`|`completed`, check constraint), `started_at`, `completed_at`,
  `updated_at`; unique `(user_id, lesson_id)`.
- Relations: `User 1──1 Profile`, `User 1──1 Progress`,
  `User 1──* RefreshToken`, `Course 1──* Lesson`, `Lesson 1──* Exercise`,
  `User 1──* ExerciseSubmission *──1 Exercise`,
  `User 1──* LessonProgress *──1 Lesson` (cascade delete).
- Migrations: `20261004_1200_init` (users, profiles),
  `20261005_1000_auth_progress` (refresh_tokens, progress),
  `20261011_1200_catalog` (courses, lessons) and `20261011_1400_exercises`
  (exercises, exercise_submissions, lesson_progress).

### Catalog content notes

- **Lesson slugs are globally unique.** `GET /lessons/{slug}` has no course
  context, so a per-course-unique slug would be ambiguous. The stricter global
  constraint is intentional.
- **`theory` markup.** Lesson theory is plain text. Blocks are separated by blank
  lines; a block beginning with `## ` is a heading; consecutive lines beginning
  with `- ` are a list; anything else is a paragraph. The frontend renders this
  into DOM nodes with `textContent`. There is no HTML in stored content.
- **Publication.** Only `is_published` courses and `is_published` lessons of
  published courses are returned by the API; drafts are invisible (`404`).
- **Seeding.** `backend/app/db/seed.py` (`pnpm db:seed`) is idempotent: courses,
  lessons and exercises are matched by `slug` and updated in place. It never
  touches user submissions or progress.

### Exercise, grading and progress rules

- **Types.** `single_choice` (options + one `correct_option_id`), `text`
  (`accepted_answers` compared after normalisation — trim, collapse whitespace,
  casefold) and `self_check` (the learner assesses their own free-text answer;
  the server never grades it).
- **Secrecy.** `correct_option_id`, `accepted_answers`, `model_answer` and
  `explanation` are never serialized in a public lesson response. They are
  revealed only in the submission result.
- **Exercise completion.** A `single_choice`/`text` exercise is completed once a
  correct answer has been submitted. A `self_check` exercise is completed by
  attempting it. `exercise_submissions.completed` is sticky.
- **XP.** Each exercise is worth its `points`; XP is awarded once per
  `(user, exercise)` when the exercise first becomes completed. A conditional
  `UPDATE ... WHERE xp_awarded = false` claims the award atomically, so retries
  cannot farm XP. `Profile.xp` is the running total.
- **Lesson completion.** A lesson is completed when it has at least one exercise
  and every exercise is completed. Opening a lesson only moves it to
  `in_progress`; a lesson with no exercises is never auto-completed. The
  `in_progress → completed` transition happens at most once, incrementing
  `Progress.lessons_completed` and (by `estimated_minutes`)
  `Progress.study_minutes`.

`password_hash` stores argon2id hashes only; plaintext passwords are never
persisted. Refresh tokens are stored as SHA-256 hashes; the raw token only ever
lives in the client's HttpOnly cookie.

## 1. Principles

- The configured SQL database is the single source of persistent truth.
- Every table has a stable primary key (UUID by default).
- Every mutable table carries `created_at` / `updated_at`.
- Ownership is explicit: each entity is owned by exactly one backend module.
- Enforce integrity in the database (FKs, unique constraints, checks); do not
  rely on application code alone.
- Delete strategy is explicit per entity (`cascade` for dependent content,
  soft-delete only where audit/history requires it).

## 2. Entity list

### Identity and account

| Entity         | Owner    | Key fields                                                                                                                                       | Status                                           |
| -------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `User`         | auth     | `id`, `email` (unique), `passwordHash`, `role`, `emailVerifiedAt`, `createdAt`                                                                   | 🟢 implemented (no `role`/`emailVerifiedAt` yet) |
| `Profile`      | users    | `id`, `userId` (unique FK), `displayName`, `level`, `xp`, `avatarUrl`, `nativeLanguage`, `targetLevel`, `timezone`, `dailyGoalMinutes`, `locale` | 🟡 partial (`displayName`, `level`, `xp`)        |
| `RefreshToken` | auth     | `id`, `userId` FK, `tokenHash` (unique), `expiresAt`, `revokedAt`, `replacedById`, `userAgent`, `ip`                                             | 🟢 implemented (no `userAgent`/`ip` yet)         |
| `Progress`     | progress | `id`, `userId` (unique FK), `lessonsStarted`, `lessonsCompleted`, `studyMinutes`, `lastActivityAt`                                               | 🟢 implemented                                   |

### Catalog and content

| Entity               | Owner     | Key fields                                                                                                                                                  | Status         |
| -------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `Course`             | catalog   | `id`, `slug` (unique), `title`, `description`, `level` (`A1`–`C2`), `position`, `isPublished`                                                               | 🟢 implemented |
| `Lesson`             | catalog   | `id`, `courseId` FK, `slug` (unique, global), `title`, `summary`, `theory`, `position`, `estimatedMinutes`, `isPublished`                                   | 🟢 implemented |
| `Exercise`           | exercises | `id`, `lessonId` FK, `slug` (unique), `type`, `prompt`, `points`, `options`, `correctOptionId`, `acceptedAnswers`, `modelAnswer`, `explanation`, `position` | 🟢 implemented |
| `ExerciseSubmission` | exercises | `id`, `userId` FK, `exerciseId` FK (unique per user), `answer`, `isCorrect`, `completed`, `xpAwarded`, `attempts`, `submittedAt`                            | 🟢 implemented |

### Vocabulary

| Entity             | Owner      | Key fields                                                                                | Status         |
| ------------------ | ---------- | ----------------------------------------------------------------------------------------- | -------------- |
| `VocabularyItem`   | vocabulary | `id`, `userId`, optional `lessonId`, `word`, `translation`, `example`, `learned`, `dueAt` | 🟢 implemented |
| `VocabularyReview` | vocabulary | `id`, `itemId`, `remembered`, `createdAt`                                                 | 🟢 implemented |

### Progress and gamification

| Entity             | Owner        | Key fields                                                                               | Status         |
| ------------------ | ------------ | ---------------------------------------------------------------------------------------- | -------------- |
| `LessonProgress`   | progress     | `id`, `userId` FK, `lessonId` FK (unique per user), `status`, `startedAt`, `completedAt` | 🟢 implemented |
| `XpEvent`          | gamification | `id`, `userId` FK, `amount`, `source`, `sourceId`, `createdAt`                           | 🔴             |
| `LearningActivity` | gamification | `id`, unique `(userId, day)`; derived current/longest streak                             | 🟢 implemented |
| `Achievement`      | gamification | `code` PK, `title`, `metric`, `threshold`                                                | 🟢 implemented |
| `UserAchievement`  | gamification | `(userId, achievementCode)` PK, `awardedAt`                                              | 🟢 implemented |

### Challenges, AI, platform

| Entity                 | Owner         | Key fields                                                                                   | Status         |
| ---------------------- | ------------- | -------------------------------------------------------------------------------------------- | -------------- |
| `Challenge`            | challenges    | `id`, `slug` (unique), `title`, `goalType`, `goalValue`, `startsAt`, `endsAt`, `isPublished` | 🔴             |
| `ChallengeParticipant` | challenges    | `id`, `challengeId` FK, `userId` FK, `progress`, `completedAt`                               | 🔴             |
| `AIConversation`       | ai            | `id`, `userId` FK, `model`, `createdAt`                                                      | 🟢 implemented |
| `AIMessage`            | ai            | `id`, `conversationId` FK, `role`, `content`, `model`, `usage`, `createdAt`                  | 🟢 implemented |
| `Subscription`         | subscriptions | `id`, `userId` FK, `plan`, `status`, `provider`, `externalId`, `currentPeriodEnd`            | 🔴             |
| `Notification`         | notifications | `id`, `userId` FK, `type`, `payload`, `readAt`, `createdAt`                                  | 🔴             |

## 3. Relationships (target)

```
User 1──1 Profile                 (implemented)
User 1──1 Progress                (implemented)
User 1──* RefreshToken            (implemented)
Course 1──* Lesson                (implemented)
Lesson 1──* Exercise              (implemented)
User 1──* ExerciseSubmission *──1 Exercise   (implemented)
User 1──* LessonProgress *──1 Lesson         (implemented)
User 1──* UserVocabulary *──1 VocabularyWord
User 1──* FlashcardReview *──1 UserVocabulary
User 1──1 Streak
User 1──* XpEvent
User 1──* UserAchievement *──1 Achievement
User 1──* ChallengeParticipant *──1 Challenge
User 1──* AIConversation 1──* AIMessage
User 1──* Subscription
User 1──* Notification
```

### Why `Progress` is one table

`Progress` is the per-user aggregate (`lessonsStarted`, `lessonsCompleted`,
`studyMinutes`, `lastActivityAt`); per-lesson state lives in `LessonProgress`.
`exercisesCompleted` and per-course progress are derived on read from
`exercise_submissions` and `lesson_progress` rather than denormalised, so those
counters cannot drift. XP is a running total on `Profile.xp`, awarded once per
exercise.

## 4. Indexes

Implemented: unique `users.email`, unique `profiles.user_id`, unique
`refresh_tokens.token_hash`, index `refresh_tokens.user_id`, unique
`progress.user_id`, unique `courses.slug`, unique `lessons.slug`, index
`lessons.course_id`, unique `exercises.slug`, index `exercises.lesson_id`,
unique `exercise_submissions (user_id, exercise_id)`, indexes
`exercise_submissions.user_id` / `exercise_id`, unique `lesson_progress
(user_id, lesson_id)`, indexes `lesson_progress.user_id` / `lesson_id`.

Planned: `user_vocabulary` unique `(user_id, word_id)` and `(user_id, due_at)`;
`xp_events (user_id, created_at)`; `user_achievements` unique
`(user_id, achievement_id)`; `challenge_participants` unique
`(challenge_id, user_id)`; `ai_messages (conversation_id, created_at)`;
`notifications (user_id, read_at, created_at)`.

## 5. Migrations

- Managed by **Alembic**; migration files live in `backend/alembic/versions/`
  and are committed.
- Migrations are hand-written (no live database was required to author them) and
  their SQL is verified with `pnpm db:sql` (offline mode).
- Apply migrations with `npm run db:migrate` (`alembic upgrade head`). SQLite needs
  no server; PostgreSQL requires its configured server.
- The SQLite chain is tested on a fresh file. Live PostgreSQL verification remains a task in
  `plans/testing-plan.md` and `plans/david-work.md`.
- Never edit an applied migration; add a new one.

### Local SQLite workflow

`npm run dev` invokes `app.db.prepare`: upgrade the configured local SQLite file
to head, then seed only an empty course catalog. No table reset occurs. The file
defaults to `backend/data/fleng.db`; config resolves relative paths against
`backend/` and session setup creates the parent directory. Alembic reuses that
same configured async engine, including per-connection foreign-key enforcement
and the `now()` compatibility function needed by existing migration defaults.
Autogenerated SQLite alterations use batch rendering; existing upgrades need no
table recreation. `npm run db:seed` explicitly updates demo catalog content.

SQLite is intended for a local, single-server workflow. It has one writer and
does not provide PostgreSQL row locks (`FOR UPDATE`). Do not infer production
concurrency guarantees from sequential local tests. Keep PostgreSQL for deployments
requiring concurrent writers; backups and a data migration require separate planning.

## 6. Data flow highlights

- **Health**: `SELECT 1` in a try/except; never fails the request.
- **Registration**: creates `User`, `Profile` and an empty `Progress` row in one
  transaction; the password is hashed with argon2id first.
- **Session**: login/refresh write `RefreshToken` rows (hashed); rotation links
  tokens through `replaced_by_id`, and replay of a revoked token revokes the set.
- **Profile read**: `GET /users/me` loads the authenticated user with
  `selectinload(profile)` and returns a camelCase Pydantic response.
- **Catalog read**: `GET /courses` lists published courses with a published
  lesson count (one grouped query); `GET /courses/{slug}` and `GET /lessons/{slug}`
  scope every query to `is_published` rows, so drafts and unpublished parents are
  never returned. Seed content comes from `app/db/seed.py`.
- **Exercise submission**: `POST /lessons/{slug}/submit` upserts the caller's
  `ExerciseSubmission` (unique per user+exercise), grades objective types, awards
  XP once (conditional `UPDATE` on `xp_awarded`), recomputes lesson completion
  from persisted submissions and — on the single `in_progress → completed`
  transition — bumps `Progress.lessons_completed` / `study_minutes`, all in one
  transaction. Ownership comes from the token; an exercise of another lesson is
  reported as `404`.
- **Gamification**: daily LearningActivity and deterministic achievements update
  in the submission transaction. A separate XP ledger remains future scope.

## 7. Open questions

- Soft-delete policy for `User` (GDPR-style deletion vs. anonymisation).
- Whether analytics events live in Postgres, a separate store, or both.

## Learning and AI schema extension — revision 20261018_1200

This additive revision extends `20261011_1400`; existing users, catalog,
submissions, XP and progress are retained. It adds `profiles.english_level`
(default A1) and `profiles.preferred_language` (default English). Existing numeric
`level` remains a separate gamification attribute.

| Table              | Key / relationships                                                     | Purpose                                                                                |
| ------------------ | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| vocabulary_items   | UUID; user FK cascade, nullable lesson FK set-null; unique (user, word) | normalized word, translation/example, learned, due/created timestamps                  |
| vocabulary_reviews | UUID; item FK cascade                                                   | remembered flag and timestamp                                                          |
| learning_activity  | UUID; user FK cascade; unique (user, day)                               | server-policy calendar learning days                                                   |
| achievements       | code primary key                                                        | immutable code/title/metric/threshold definitions                                      |
| user_achievements  | composite (user, achievement code); user FK cascade                     | once-only awarded timestamp                                                            |
| password_resets    | UUID; user FK cascade; unique token hash                                | SHA-256 opaque-token hash, expiry and consumption timestamps                           |
| request_limits     | composite (key, window)                                                 | shared persistent fixed-window request counters and global AI reservation lock         |
| ai_conversations   | UUID; user FK cascade                                                   | selected model, creation timestamp                                                     |
| ai_messages        | UUID; conversation FK cascade; role check user/assistant                | content, model, allowlisted optional usage, timestamp                                  |
| ai_usage           | UUID; user FK cascade                                                   | per-request conservative token reservation, model/status, optional usage and timestamp |

Lookup foreign keys are indexed. Migration inserts the five achievement
definitions. It does not seed demo users/content, backfill invented streak days,
or replace any existing schema. Full chain SQL can be emitted offline with
`alembic upgrade head --sql`; only an actual PostgreSQL migration run validates
DDL execution. An opt-in test applies the full chain and checks metadata drift
in a unique PostgreSQL schema (`TEST_DATABASE_URL`).

Activity uniqueness and learner locks protect duplicates. Achievement and learning
updates use one transaction. Complete AI turns are inserted atomically; failures
retain only usage reservations, never half a conversation turn. Active-request
leases are bounded by timeout + 60 seconds. Usage cleanup retains 30 days;
request-window cleanup retains two days (the capacity lock row is retained).
Conversation/message caps prevent unbounded tutoring history. Users can delete
their conversations. No provider key, raw refresh token or raw password-reset
token is stored in these tables.

The database was unavailable during implementation: migrations have **not** been
applied to a live PostgreSQL instance here. See development.md for recovery and
real integration instructions. Downgrading removes extension data and must never
be used as a routine development setup command.
