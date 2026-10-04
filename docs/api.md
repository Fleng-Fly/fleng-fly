# API

> Status: **M1 implemented** for `GET /api/v1/health` and `GET /api/v1/users/me`
> (the latter via a development-only auth stub). All other endpoints below are
> designed but not built. Base path: `/api/v1`.

## 1. Conventions

- **Base path**: all endpoints under `/api/v1`; breaking changes bump the
  version.
- **Content type**: `application/json`.
- **Naming**: plural nouns for collections; `camelCase` fields.
- **Pagination**: cursor-based for large/live collections
  (`?cursor=...&limit=...`); response `{ items, nextCursor }`.
- **Filtering/sorting**: explicit query params, whitelisted.
- **Timestamps**: ISO 8601 UTC.
- **IDs**: UUID strings.

### Success envelope

Resource endpoints return the resource directly (including a wrapper only where
pagination/metadata is needed):

```json
{ "id": "...", "title": "..." }
```

```json
{ "items": [ ... ], "nextCursor": "..." }
```

### Error envelope

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable summary",
    "details": [{ "field": "email", "issue": "must be an email" }],
    "requestId": "..."
  }
}
```

Common status codes: `400` validation, `401` unauthenticated, `403` forbidden,
`404` not found, `409` conflict, `429` rate limited, `500` internal.

## 2. Endpoint map

Legend: ✅ implemented · ⬜ planned.

### 2.0 Health — `/api/v1/health`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/health` | Service + database status | none | — | `200 { status, service, timestamp, database }` |

`status` is always `"ok"` when the API is reachable. `database` is `"up"` or
`"down"`; the endpoint returns `200` even when the database is down so clients
can distinguish "API down" from "database down".

### 2.1 Auth — `/api/v1/auth` ⬜ not implemented

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| POST | `/register` | Create account | none | `{ email, password, displayName }` | `201 { user, accessToken }` + refresh cookie |
| POST | `/login` | Authenticate | none | `{ email, password }` | `200 { user, accessToken }` + refresh cookie |
| POST | `/refresh` | Rotate session | refresh cookie | — | `200 { accessToken }` + rotated cookie |
| POST | `/logout` | Revoke session | refresh cookie | — | `204` |
| POST | `/verify-email` | Confirm email | token | `{ token }` | `204` |
| POST | `/forgot-password` | Start reset | none | `{ email }` | `202` (always, to avoid enumeration) |
| POST | `/reset-password` | Complete reset | token | `{ token, password }` | `204` |
| GET | `/me` | Current identity | bearer | — | `200 { id, email, role, profile }` |

Errors: `401 INVALID_CREDENTIALS`, `409 EMAIL_TAKEN`, `429 TOO_MANY_ATTEMPTS`,
`400 VALIDATION_FAILED`.

### 2.2 Users & profiles — `/api/v1/users`

`GET /users/me` is implemented. It is protected by the **development-only**
`DevAuthGuard`, which attaches a fixed user id (`DEV_USER_ID`) when
`APP_ENV !== production` and returns `401` in production. Real authentication is
not implemented.

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/me` | Read own profile | dev stub | — | `200 { id, email, displayName, level, xp, createdAt }` |
| PATCH ⬜ | `/me` | Update own profile | bearer | partial profile | `200 Profile` |
| DELETE | `/me` | Delete/anonymise account | bearer | — | `204` |
| GET | `/:id` | Public profile (limited) | bearer | — | `200 PublicProfile` |
| GET | `/me/settings` | Read settings | bearer | — | `200 Settings` |
| PATCH | `/me/settings` | Update settings | bearer | partial settings | `200 Settings` |

### 2.3 Courses — `/api/v1/courses`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/` | List published courses | optional | `?level&cursor&limit` | `200 { items, nextCursor }` |
| GET | `/:idOrSlug` | Course detail + lessons | optional | — | `200 Course` |
| POST | `/` | Create course | admin | course body | `201 Course` |
| PATCH | `/:id` | Update course | admin | partial | `200 Course` |
| DELETE | `/:id` | Archive course | admin | — | `204` |

### 2.4 Lessons — `/api/v1/lessons`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/:idOrSlug` | Lesson + exercises | bearer | — | `200 Lesson` |
| POST | `/:id/start` | Mark in progress | bearer | — | `200 LessonProgress` |
| POST | `/:id/complete` | Submit completion | bearer | `{ answers? }` | `200 { progress, xp, streak, newAchievements }` |
| GET | `/:id/progress` | Progress for lesson | bearer | — | `200 LessonProgress` |

### 2.5 Exercises — `/api/v1/exercises`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/:id` | Exercise (answer hidden) | bearer | — | `200 Exercise` |
| POST | `/:id/submit` | Submit answer | bearer | `{ answer }` | `200 { isCorrect, score, feedback }` |
| GET | `/submissions` | Own submission history | bearer | `?exerciseId&cursor` | `200 { items, nextCursor }` |

Exercise payload/answer shape depends on `type`; documented alongside the
exercise domain in `docs/database.md`.

### 2.6 Vocabulary — `/api/v1/vocabulary`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/words` | Search dictionary | bearer | `?q&level&cursor` | `200 { items, nextCursor }` |
| GET | `/me` | Own vocabulary | bearer | `?status&cursor` | `200 { items, nextCursor }` |
| POST | `/me` | Add word | bearer | `{ wordId }` | `201 UserVocabulary` |
| PATCH | `/me/:id` | Update status | bearer | `{ status }` | `200 UserVocabulary` |
| DELETE | `/me/:id` | Remove word | bearer | — | `204` |
| GET | `/reviews/due` | Due flashcards | bearer | `?limit` | `200 { items }` |
| POST | `/reviews` | Record review | bearer | `{ userVocabularyId, rating }` | `201 FlashcardReview` |

### 2.7 Progress — `/api/v1/progress`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/summary` | Dashboard summary | bearer | — | `200 { xp, level, streak, skills, recent }` |
| GET | `/courses/:courseId` | Progress in a course | bearer | — | `200 { lessons: LessonProgress[] }` |
| GET | `/skills` | Per-skill breakdown | bearer | `?range` | `200 SkillProgress[]` |
| GET | `/activity` | Activity timeline | bearer | `?range&cursor` | `200 { items, nextCursor }` |

### 2.8 Challenges — `/api/v1/challenges`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/` | List active challenges | bearer | `?status&cursor` | `200 { items, nextCursor }` |
| GET | `/:id` | Challenge detail | bearer | — | `200 Challenge` |
| POST | `/:id/join` | Join challenge | bearer | — | `201 ChallengeParticipant` |
| GET | `/:id/leaderboard` | Leaderboard | bearer | `?cursor` | `200 { items, nextCursor }` |

### 2.9 AI — `/api/v1/ai`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/conversations` | List own conversations | bearer | `?cursor` | `200 { items, nextCursor }` |
| POST | `/conversations` | Create conversation | bearer | `{ scenario }` | `201 AIConversation` |
| GET | `/conversations/:id` | Conversation + messages | bearer | `?cursor` | `200 { conversation, messages }` |
| POST | `/conversations/:id/messages` | Send message | bearer | `{ content }` | `201 { userMessage, assistantMessage }` |
| POST | `/writing/correct` | Correct a text | bearer | `{ text, context? }` | `200 CorrectionResult` |
| POST | `/grammar/explain` | Explain a rule | bearer | `{ topic, example? }` | `200 Explanation` |
| GET | `/recommendations` | Personalised next steps | bearer | — | `200 Recommendation[]` |

AI endpoints are rate limited per user; requests are validated and prompts are
built server-side (never trust client-supplied system prompts). See
`docs/ai.md` and `docs/security.md`.

### 2.10 Notifications — `/api/v1/notifications`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/` | List notifications | bearer | `?read&cursor` | `200 { items, nextCursor, unreadCount }` |
| POST | `/:id/read` | Mark read | bearer | — | `200 Notification` |
| POST | `/read-all` | Mark all read | bearer | — | `204` |

## 3. Authorization model

- `USER` may only act on resources they own (`userId` scoping enforced in
  queries, not only in guards).
- `ADMIN` may manage catalog/content definitions.
- Ownership violations return `404` (not `403`) where revealing existence would
  leak data.

## 4. Related documents

- `docs/authentication.md` — token mechanics.
- `docs/security.md` — validation, rate limiting, prompt injection.
- `project-map/api-map.md` — condensed map used for navigation.
