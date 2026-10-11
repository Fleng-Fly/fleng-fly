# Database

> Status: **M2 implemented** for `User`, `Profile`, `RefreshToken` and `Progress`,
> plus the read-only catalog (`Course`, `Lesson`). Other entities below are
> designed, not built. Engine: PostgreSQL. Access: SQLAlchemy 2 (async) from the
> backend only; migrations via Alembic.

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
- Relations: `User 1──1 Profile`, `User 1──1 Progress`,
  `User 1──* RefreshToken`, `Course 1──* Lesson` (cascade delete).
- Migrations: `20261004_1200_init` (users, profiles),
  `20261005_1000_auth_progress` (refresh_tokens, progress) and
  `20261011_1200_catalog` (courses, lessons).

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
- **Seeding.** `backend/app/db/seed.py` (`pnpm db:seed`) is idempotent: courses
  and lessons are matched by `slug` and updated in place.

`password_hash` stores argon2id hashes only; plaintext passwords are never
persisted. Refresh tokens are stored as SHA-256 hashes; the raw token only ever
lives in the client's HttpOnly cookie.

## 1. Principles

- PostgreSQL is the single source of persistent truth.
- Every table has a stable primary key (UUID by default).
- Every mutable table carries `created_at` / `updated_at`.
- Ownership is explicit: each entity is owned by exactly one backend module.
- Enforce integrity in the database (FKs, unique constraints, checks); do not
  rely on application code alone.
- Delete strategy is explicit per entity (`cascade` for dependent content,
  soft-delete only where audit/history requires it).

## 2. Entity list

### Identity and account

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `User` | auth | `id`, `email` (unique), `passwordHash`, `role`, `emailVerifiedAt`, `createdAt` | 🟢 implemented (no `role`/`emailVerifiedAt` yet) |
| `Profile` | users | `id`, `userId` (unique FK), `displayName`, `level`, `xp`, `avatarUrl`, `nativeLanguage`, `targetLevel`, `timezone`, `dailyGoalMinutes`, `locale` | 🟡 partial (`displayName`, `level`, `xp`) |
| `RefreshToken` | auth | `id`, `userId` FK, `tokenHash` (unique), `expiresAt`, `revokedAt`, `replacedById`, `userAgent`, `ip` | 🟢 implemented (no `userAgent`/`ip` yet) |
| `Progress` | progress | `id`, `userId` (unique FK), `lessonsStarted`, `lessonsCompleted`, `studyMinutes`, `lastActivityAt` | 🟢 implemented |

### Catalog and content

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `Course` | catalog | `id`, `slug` (unique), `title`, `description`, `level` (`A1`–`C2`), `position`, `isPublished` | 🟢 implemented |
| `Lesson` | catalog | `id`, `courseId` FK, `slug` (unique, global), `title`, `summary`, `theory`, `position`, `estimatedMinutes`, `isPublished` | 🟢 implemented |
| `Exercise` | exercises | `id`, `lessonId` FK, `type`, `prompt`, `payload`, `answer`, `position`, `points` | 🔴 |
| `ExerciseSubmission` | exercises | `id`, `userId` FK, `exerciseId` FK, `answer`, `isCorrect`, `score`, `feedback`, `submittedAt` | 🔴 |

### Vocabulary

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `VocabularyWord` | vocabulary | `id`, `lemma`, `language`, `partOfSpeech`, `definition`, `level` | 🔴 |
| `UserVocabulary` | vocabulary | `id`, `userId` FK, `wordId` FK, `status`, `ease`, `intervalDays`, `repetitions`, `dueAt`, `lastReviewedAt` | 🔴 |
| `FlashcardReview` | vocabulary | `id`, `userVocabularyId` FK, `rating`, `reviewedAt` | 🔴 |

### Progress and gamification

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `LessonProgress` | progress | `id`, `userId` FK, `lessonId` FK, `status`, `score`, `completedAt` | 🔴 || `XpEvent` | gamification | `id`, `userId` FK, `amount`, `source`, `sourceId`, `createdAt` | 🔴 |
| `Streak` | gamification | `userId` PK/FK, `current`, `longest`, `lastActivityDate` | 🔴 |
| `Achievement` | gamification | `id`, `code` (unique), `title`, `description`, `criteria`, `points` | 🔴 |
| `UserAchievement` | gamification | `id`, `userId` FK, `achievementId` FK, `earnedAt` | 🔴 |

### Challenges, AI, platform

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `Challenge` | challenges | `id`, `slug` (unique), `title`, `goalType`, `goalValue`, `startsAt`, `endsAt`, `isPublished` | 🔴 |
| `ChallengeParticipant` | challenges | `id`, `challengeId` FK, `userId` FK, `progress`, `completedAt` | 🔴 |
| `AIConversation` | ai | `id`, `userId` FK, `title`, `scenario`, `provider`, `model` | 🔴 |
| `AIMessage` | ai | `id`, `conversationId` FK, `role`, `content`, `tokenCount`, `metadata`, `createdAt` | 🔴 |
| `Subscription` | subscriptions | `id`, `userId` FK, `plan`, `status`, `provider`, `externalId`, `currentPeriodEnd` | 🔴 |
| `Notification` | notifications | `id`, `userId` FK, `type`, `payload`, `readAt`, `createdAt` | 🔴 |

## 3. Relationships (target)

```
User 1──1 Profile                 (implemented)
User 1──1 Progress                (implemented)
User 1──* RefreshToken            (implemented)
Course 1──* Lesson                (implemented)
User 1──* ExerciseSubmission *──1 Exercise *──1 Lesson *──1 Course
User 1──* UserVocabulary *──1 VocabularyWord
User 1──* FlashcardReview *──1 UserVocabulary
User 1──* LessonProgress *──1 Lesson
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
`studyMinutes`, `lastActivityAt`). When lessons exist, per-lesson rows will go in
a separate `LessonProgress` table referencing `lessons(id)`. Splitting now would
mean a `lessonId` FK with no `lessons` table; keeping the aggregate separate means
the per-lesson table can be added later without migrating `progress`.

## 4. Indexes (target)

Implemented: unique `users.email`, unique `profiles.user_id`, unique
`refresh_tokens.token_hash`, index `refresh_tokens.user_id`, unique
`progress.user_id`, unique `courses.slug`, unique `lessons.slug`, index
`lessons.course_id`.

Planned: `user_vocabulary` unique `(user_id, word_id)` and `(user_id, due_at)`;
`lesson_progress` unique `(user_id, lesson_id)`; `xp_events (user_id, created_at)`;
`user_achievements` unique `(user_id, achievement_id)`;
`challenge_participants` unique `(challenge_id, user_id)`; `ai_messages
(conversation_id, created_at)`; `notifications (user_id, read_at, created_at)`.

## 5. Migrations

- Managed by **Alembic**; migration files live in `backend/alembic/versions/`
  and are committed.
- Migrations are hand-written (no live database was required to author them) and
  their SQL is verified with `pnpm db:sql` (offline mode).
- Apply migrations with `pnpm db:migrate` (`alembic upgrade head`); this needs a
  running PostgreSQL.
- The current environment has no PostgreSQL/Docker, so the migrations have been
  verified offline only. Applying them to a real database remains a task in
  `plans/testing-plan.md` and `plans/david-work.md`.
- Never edit an applied migration; add a new one.

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
- **Lesson completion** (planned): submissions, then `LessonProgress`, `XpEvent`,
  `Streak`, achievements — ideally in one transaction.

## 7. Open questions

- Soft-delete policy for `User` (GDPR-style deletion vs. anonymisation).
- Whether analytics events live in Postgres, a separate store, or both.
