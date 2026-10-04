# Project Map — Data Flow

> Status: 🔴 documented only. Details in `docs/architecture.md §5`,
> `docs/database.md §5`.

## Flow 1 — Authenticated request

```
Browser (access token in memory)
  → GET /api/v1/... (Authorization: Bearer)
  → CORS → ValidationPipe → JwtAuthGuard → RolesGuard
  → Controller → Service → Repository → Prisma → PostgreSQL
  → Interceptor (logging) → Response DTO → Browser
```

On `401`: browser calls `POST /auth/refresh` (httpOnly cookie) → server rotates
refresh token → returns new access token → original request retried once.

## Flow 2 — Register / login

```
Browser → POST /auth/register|login
  → validate DTO → auth.service
  → (register) hash password (argon2id) → create User + Profile
  → issue access JWT + refresh token → persist refresh hash
  → set refresh cookie → 201/200 { user, accessToken }
```

## Flow 3 — Lesson completion (cross-module writes)

```
Browser → POST /lessons/:id/complete
  → exercises.service grades submissions
  → progress.service records LessonProgress (transaction)
  → gamification.service updates XpEvent, Streak, achievements
  → analytics.service records event (best-effort)
  → response: { progress, xp, streak, newAchievements }
```

Owner of the transaction: `progress` orchestrates, calling the other services.
If a downstream step is non-critical (analytics), it must not fail the request.

## Flow 4 — Vocabulary review (SRS)

```
Browser → POST /vocabulary/reviews { userVocabularyId, rating }
  → vocabulary.service validates ownership
  → compute next scheduling (ease/interval/dueAt)
  → transaction: append FlashcardReview + update UserVocabulary
  → response: updated UserVocabulary
```

## Flow 5 — AI tutor turn

```
Browser → POST /ai/conversations/:id/messages { content }
  → ai module: ownership check
  → assemble context (recent messages + learner summary)
  → safety guardrails + token budget
  → @fleng/ai: build prompt → provider.complete()
  → validate output → persist AIMessage(user) + AIMessage(assistant)
  → response: { userMessage, assistantMessage }
```

`@fleng/ai` never touches the database; the `ai` module owns persistence.

## Flow 6 — Dashboard load

```
Browser → GET /progress/summary
  → progress.service aggregates: lesson progress, XP/level, streak,
    next recommendation (cached where safe)
  → response: single summary DTO (avoid N requests from the client)
```

## Data ownership summary

| Data | Writer | Reader |
| ---- | ------ | ------ |
| Credentials, tokens | auth | auth |
| Profile/settings | users | users, others (limited) |
| Catalog/content | catalog/content (admin) | all users |
| Submissions | exercises | exercises, progress |
| Progress | progress | progress, recommendations, analytics |
| XP/streak/achievements | gamification | progress, challenges |
| Vocabulary/SRS | vocabulary | vocabulary, recommendations |
| AI conversations | ai | ai |
| Notifications | notifications | notifications |
