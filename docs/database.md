# Database

> Status: **design** (pre-implementation). Engine: PostgreSQL. Access: Prisma
> from the backend only. No tables are created yet — this document defines the
> intended model.

## 1. Principles

- PostgreSQL is the single source of persistent truth.
- Every table has a stable primary key (UUID by default).
- Every mutable table carries `createdAt` / `updatedAt`.
- Ownership is explicit: each entity is owned by exactly one backend module
  (see the owner column), and only that module writes it.
- Enforce integrity in the database (FKs, unique constraints, checks); do not
  rely on application code alone.
- Delete strategy is explicit per entity (`cascade` for dependent content,
  soft-delete only where audit/history requires it).

## 2. Entity list

### Identity and account

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `User` | auth | `id`, `email` (unique), `passwordHash`, `role` (`USER`/`ADMIN`), `emailVerifiedAt`, `createdAt` | Credentials and identity only |
| `Profile` | users | `id`, `userId` (unique FK), `displayName`, `avatarUrl`, `nativeLanguage`, `targetLevel`, `timezone`, `dailyGoalMinutes`, `locale` | 1:1 with `User` |
| `RefreshToken` | auth | `id`, `userId` FK, `tokenHash` (unique), `expiresAt`, `revokedAt`, `replacedById`, `userAgent`, `ip` | Rotation chain; store hash only |

### Catalog and content

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `Course` | catalog | `id`, `slug` (unique), `title`, `description`, `level` (`A1`–`C2`), `position`, `isPublished` | Ordered curriculum |
| `Lesson` | catalog | `id`, `courseId` FK, `slug`, `title`, `summary`, `type`, `position`, `estimatedMinutes`, `isPublished` | Belongs to a course; unique `(courseId, slug)` |
| `Exercise` | exercises | `id`, `lessonId` FK, `type` (`MULTIPLE_CHOICE`/`FILL_BLANK`/`MATCH`/`WRITING`/`SPEAKING`/`LISTENING`/`READING`/`GRAMMAR`), `prompt`, `payload` (JSONB), `answer` (JSONB), `position`, `points` | `payload`/`answer` shape depends on `type` |
| `ExerciseSubmission` | exercises | `id`, `userId` FK, `exerciseId` FK, `answer` (JSONB), `isCorrect`, `score`, `feedback`, `submittedAt` | Append-only history |

### Vocabulary

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `VocabularyWord` | vocabulary | `id`, `lemma`, `language`, `partOfSpeech`, `definition`, `translations` (JSONB), `examples` (JSONB), `level` | Global dictionary; unique `(lemma, language, partOfSpeech)` |
| `UserVocabulary` | vocabulary | `id`, `userId` FK, `wordId` FK, `status` (`NEW`/`LEARNING`/`KNOWN`), `ease`, `intervalDays`, `repetitions`, `dueAt`, `lastReviewedAt` | Spaced repetition state; unique `(userId, wordId)` |
| `FlashcardReview` | vocabulary | `id`, `userVocabularyId` FK, `rating`, `reviewedAt` | Review log for SRS tuning |

### Progress and gamification

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `LessonProgress` | progress | `id`, `userId` FK, `lessonId` FK, `status` (`NOT_STARTED`/`IN_PROGRESS`/`COMPLETED`), `score`, `completedAt` | Unique `(userId, lessonId)` |
| `XpEvent` | gamification | `id`, `userId` FK, `amount`, `source`, `sourceId`, `createdAt` | Append-only ledger; level derived from total |
| `Streak` | gamification | `userId` (PK/FK), `current`, `longest`, `lastActivityDate` | One row per user |
| `Achievement` | gamification | `id`, `code` (unique), `title`, `description`, `criteria` (JSONB), `points` | Definitions |
| `UserAchievement` | gamification | `id`, `userId` FK, `achievementId` FK, `earnedAt` | Unique `(userId, achievementId)` |

### Challenges

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `Challenge` | challenges | `id`, `slug` (unique), `title`, `description`, `goalType`, `goalValue`, `startsAt`, `endsAt`, `isPublished` | Time-boxed |
| `ChallengeParticipant` | challenges | `id`, `challengeId` FK, `userId` FK, `progress`, `completedAt` | Unique `(challengeId, userId)` |

### AI

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `AIConversation` | ai | `id`, `userId` FK, `title`, `scenario`, `provider`, `model`, `createdAt`, `updatedAt` | Belongs to a user |
| `AIMessage` | ai | `id`, `conversationId` FK, `role` (`system`/`user`/`assistant`), `content`, `tokenCount`, `metadata` (JSONB), `createdAt` | Ordered by `createdAt` |

### Platform

| Entity | Owner | Key fields | Notes |
| ------ | ----- | ---------- | ----- |
| `Subscription` | subscriptions | `id`, `userId` FK, `plan`, `status`, `provider`, `externalId`, `currentPeriodEnd` | Billing integration deferred |
| `Notification` | notifications | `id`, `userId` FK, `type`, `payload` (JSONB), `readAt`, `createdAt` | Per-user feed |

## 3. Relationships

```
User 1──1 Profile
User 1──* RefreshToken
User 1──* ExerciseSubmission      ExerciseSubmission *──1 Exercise *──1 Lesson *──1 Course
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

Cardinalities, in words:

- A `Course` has many `Lesson`s; a `Lesson` has many `Exercise`s.
- Progress and submissions are per user, never global.
- `VocabularyWord` is global content; `UserVocabulary` is the per-user state and
  is the only place SRS scheduling lives.
- Gamification derives from append-only `XpEvent` plus the single `Streak` row.
- AI conversations are private to their owner.

## 4. Indexes (initial)

| Table | Index | Reason |
| ----- | ----- | ------ |
| `User` | unique `email` | login lookup |
| `RefreshToken` | unique `tokenHash`, btree `userId` | validation, listing/revocation |
| `Course` | unique `slug`, btree `(level, position)` | routing, ordered listing |
| `Lesson` | unique `(courseId, slug)`, btree `(courseId, position)` | routing, ordering |
| `Exercise` | btree `(lessonId, position)` | lesson assembly |
| `ExerciseSubmission` | btree `(userId, submittedAt)`, `(exerciseId)` | history, scoring |
| `VocabularyWord` | unique `(lemma, language, partOfSpeech)`, btree `level` | dedupe, level filtering |
| `UserVocabulary` | unique `(userId, wordId)`, btree `(userId, dueAt)` | SRS due queue |
| `FlashcardReview` | btree `(userVocabularyId, reviewedAt)` | review history |
| `LessonProgress` | unique `(userId, lessonId)`, btree `(userId, status)` | dashboard, resume |
| `XpEvent` | btree `(userId, createdAt)` | totals, timelines |
| `UserAchievement` | unique `(userId, achievementId)` | idempotency |
| `ChallengeParticipant` | unique `(challengeId, userId)`, btree `(userId)` | membership, leaderboards |
| `AIMessage` | btree `(conversationId, createdAt)` | message ordering |
| `Notification` | btree `(userId, readAt, createdAt)` | unread feed |

## 5. Data flow highlights

- **Lesson completion**: `ExerciseSubmission` rows are written, then
  `LessonProgress`, `XpEvent`, `Streak` and possibly `UserAchievement`.
- **Vocabulary review**: a `FlashcardReview` is appended and the corresponding
  `UserVocabulary` scheduling fields are updated in one transaction.
- **AI turn**: `AIConversation`/`AIMessage` are written by the `ai` module;
  provider payloads are not stored, only normalised content + metadata.
- **Leaderboards**: computed from `ChallengeParticipant`/`XpEvent`; an
  optimisation (materialised view) is deferred until measured.

## 6. Migrations and seeding

- Schema managed by Prisma Migrate; migrations are committed and reviewed.
- Seed data (levels, sample course) lives in `prisma/seed.ts` and is idempotent.
- Never edit an applied migration; add a new one.

## 7. Open questions

- Soft-delete policy for `User` (GDPR-style deletion vs. anonymisation).
- Whether analytics events live in Postgres, a separate store, or both.
