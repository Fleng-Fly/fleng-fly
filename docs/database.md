# Database

> Status: **M1 implemented** for `User` + `Profile`. Other entities below are
> designed, not built. Engine: PostgreSQL. Access: SQLAlchemy 2 (async) from the
> backend only; migrations via Alembic.

## 0. Implemented in M1

Only identity/profile tables exist so far (SQLAlchemy models in
`backend/app/db/models.py`):

- **`User`** (`users`) — `id` (UUID PK), `email` (unique), `password_hash`,
  `created_at`, `updated_at`.
- **`Profile`** (`profiles`) — `id` (UUID PK), `user_id` (unique FK → `users`,
  `ON DELETE CASCADE`), `display_name`, `level` (int, default 1), `xp` (int,
  default 0), `created_at`, `updated_at`.
- Relation: `User 1──1 Profile` (SQLAlchemy `relationship`, cascade delete).
- Initial migration:
  `backend/alembic/versions/20261004_1200_init.py`.

`password_hash` is currently only populated by the development auth stub with a
non-login placeholder value; real hashing arrives with authentication.

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
| `User` | auth | `id`, `email` (unique), `passwordHash`, `role`, `emailVerifiedAt`, `createdAt` | 🟡 partial (no `role`/`emailVerifiedAt` yet) |
| `Profile` | users | `id`, `userId` (unique FK), `displayName`, `level`, `xp`, `avatarUrl`, `nativeLanguage`, `targetLevel`, `timezone`, `dailyGoalMinutes`, `locale` | 🟡 partial (`displayName`, `level`, `xp`) |
| `RefreshToken` | auth | `id`, `userId` FK, `tokenHash` (unique), `expiresAt`, `revokedAt`, `replacedById`, `userAgent`, `ip` | 🔴 planned |

### Catalog and content

| Entity | Owner | Key fields | Status |
| ------ | ----- | ---------- | ------ |
| `Course` | catalog | `id`, `slug` (unique), `title`, `description`, `level` (`A1`–`C2`), `position`, `isPublished` | 🔴 |
| `Lesson` | catalog | `id`, `courseId` FK, `slug`, `title`, `summary`, `type`, `position`, `estimatedMinutes`, `isPublished` | 🔴 |
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
| `LessonProgress` | progress | `id`, `userId` FK, `lessonId` FK, `status`, `score`, `completedAt` | 🔴 |
| `XpEvent` | gamification | `id`, `userId` FK, `amount`, `source`, `sourceId`, `createdAt` | 🔴 |
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
User 1──* RefreshToken
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

## 4. Indexes (target)

Implemented: unique `users.email`, unique `profiles.user_id`.

Planned: `refresh_tokens.token_hash`; `courses.slug`; unique `(course_id, slug)`
on lessons; `user_vocabulary` unique `(user_id, word_id)` and `(user_id, due_at)`;
`lesson_progress` unique `(user_id, lesson_id)`; `xp_events (user_id, created_at)`;
`user_achievements` unique `(user_id, achievement_id)`;
`challenge_participants` unique `(challenge_id, user_id)`; `ai_messages
(conversation_id, created_at)`; `notifications (user_id, read_at, created_at)`.

## 5. Migrations

- Managed by **Alembic**; migration files live in `backend/alembic/versions/`
  and are committed.
- The initial migration was hand-written (no live database was required) and its
  SQL is verified with `pnpm db:sql` (offline mode).
- Apply migrations with `pnpm db:migrate` (`alembic upgrade head`); this needs a
  running PostgreSQL.
- Never edit an applied migration; add a new one.

## 6. Data flow highlights

- **Health**: `SELECT 1` in a try/except; never fails the request.
- **Profile read**: `get_or_create_user` upserts the dev user + profile and
  returns a camelCase DTO.
- **Lesson completion** (planned): submissions, then `LessonProgress`, `XpEvent`,
  `Streak`, achievements — ideally in one transaction.

## 7. Open questions

- Soft-delete policy for `User` (GDPR-style deletion vs. anonymisation).
- Whether analytics events live in Postgres, a separate store, or both.
