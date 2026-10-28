# API

> Status: **M2 + catalog + exercises implemented** for `GET /api/v1/health`, the
> auth endpoints (`/auth/register`, `/login`, `/refresh`, `/logout`),
> `GET /api/v1/users/me`, `GET /api/v1/progress/me`, the catalog
> (`GET /courses`, `GET /courses/{slug}`, `GET /lessons/{slug}`) and the
> authenticated lesson flow (`POST /lessons/{slug}/start`,
> `POST /lessons/{slug}/submit`, `GET /lessons/{slug}/progress`). All other
> endpoints below are designed but not built. Base path: `/api/v1`.

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
    "statusCode": 422,
    "timestamp": "2026-10-05T12:00:00+00:00",
    "path": "/api/v1/auth/register",
    "details": [{ "loc": ["body", "email"], "msg": "value is not a valid email address" }]
  }
}
```

`details` is present only for validation errors. Common status codes: `400`
validation, `401` unauthenticated, `403` forbidden, `404` not found, `409`
conflict, `429` rate limited, `500` internal, `503` database/service
unavailable.

## 2. Endpoint map

Legend: ✅ implemented · ⬜ planned.

### 2.0 Health — `/api/v1/health`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/health` | Service + database status | none | — | `200 { status, service, timestamp, database }` |

`status` is always `"ok"` when the API is reachable. `database` is `"up"` or
`"down"`; the endpoint returns `200` even when the database is down so clients
can distinguish "API down" from "database down".

### 2.1 Auth — `/api/v1/auth`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| POST ✅ | `/register` | Create account | none | `{ email, password, displayName }` | `201 { accessToken, tokenType, expiresIn, user }` + refresh cookie |
| POST ✅ | `/login` | Authenticate | none | `{ email, password }` | `200 { accessToken, tokenType, expiresIn, user }` + refresh cookie |
| POST ✅ | `/refresh` | Rotate session | refresh cookie | — | `200 { accessToken, tokenType, expiresIn }` + rotated cookie |
| POST ✅ | `/logout` | Revoke session | refresh cookie | — | `204` |
| POST ⬜ | `/verify-email` | Confirm email | token | `{ token }` | `204` |
| POST ⬜ | `/forgot-password` | Start reset | none | `{ email }` | `202` (always, to avoid enumeration) |
| POST ⬜ | `/reset-password` | Complete reset | token | `{ token, password }` | `204` |

The refresh token is set as an HttpOnly cookie scoped to `/api/v1/auth`; it is
never returned in the response body. Errors: `401 INVALID_CREDENTIALS`,
`401 INVALID_REFRESH_TOKEN`, `401 REFRESH_TOKEN_REUSED`, `409 EMAIL_TAKEN`,
`403 FORBIDDEN` (untrusted Origin), `422 VALIDATION_FAILED`.

### 2.2 Users & profiles — `/api/v1/users`

`GET /users/me` requires a valid Bearer access token (`Authorization: Bearer
<accessToken>`). It is strictly read-only: it never creates a user.

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/me` | Read own profile | bearer | — | `200 { id, email, displayName, level, xp, createdAt }` |
| PATCH ✅ | `/me` | Update own profile and email | bearer | optional `displayName`, `email`, `englishLevel`, `preferredLanguage` | `200 UserResponse`; `409 EMAIL_TAKEN` |
| POST ✅ | `/me/password` | Change own password | bearer | `currentPassword`, `newPassword` (8–128 characters) | `204`; `400 INVALID_PASSWORD` |
| DELETE | `/me` | Delete/anonymise account | bearer | — | `204` |
| GET | `/:id` | Public profile (limited) | bearer | — | `200 PublicProfile` |
| GET | `/me/settings` | Read settings | bearer | — | `200 Settings` |
| PATCH | `/me/settings` | Update settings | bearer | partial settings | `200 Settings` |

### 2.3 Courses — `/api/v1/courses`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/` | List published courses (ordered by position) | none | — | `200 CourseSummary[]` |
| GET ✅ | `/{slug}` | Published course + its published lessons | none | — | `200 CourseDetail` |
| POST | `/` | Create course | admin | course body | `201 Course` |
| PATCH | `/{slug}` | Update course | admin | partial | `200 Course` |
| DELETE | `/{slug}` | Archive course | admin | — | `204` |

`CourseSummary` = `{ id, slug, title, description, level, lessonCount }`.
`CourseDetail` = `{ id, slug, title, description, level, lessons: LessonSummary[] }`
where `LessonSummary` = `{ id, slug, title, summary, position, estimatedMinutes }`.
`level` is a CEFR band (`A1`–`C2`). Only `is_published` courses and lessons are
returned; missing and unpublished resources both return `404 NOT_FOUND`.
Pagination is deliberately deferred for the small MVP catalog.

### 2.4 Lessons — `/api/v1/lessons`

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET ✅ | `/{slug}` | Published lesson with theory, course context and public exercises | none | — | `200 LessonDetail` |
| POST ✅ | `/{slug}/start` | Start or resume a lesson (idempotent) | bearer | — | `200 LessonProgress` |
| POST ✅ | `/{slug}/submit` | Grade and persist one answer | bearer | `{ exerciseId, answer, selfAssessment? }` | `200 SubmissionResult` |
| GET ✅ | `/{slug}/progress` | The caller's progress through a lesson | bearer | — | `200 LessonProgress` |

`LessonDetail` = `{ id, slug, title, summary, theory, position, estimatedMinutes,
courseSlug, courseTitle, level, exercises: ExercisePublic[] }`.

`ExercisePublic` = `{ id, slug, position, type, prompt, points, options? }` where
`options` = `[{ id, text }]` and is present only for `single_choice`. Public
payloads **never** contain `correctOptionId`, `acceptedAnswers`, `modelAnswer`
or `explanation`.

`LessonProgress` = `{ lessonSlug, lessonTitle, status ("in_progress"|"completed"),
completed, startedAt, completedAt, exercisesTotal, exercisesCompleted, xpEarned,
exercises: [{ exerciseId, completed, isCorrect, attempts, pointsAwarded, answer }] }`.
`answer` is the authenticated caller's latest submitted answer or `null`.

`SubmissionResult` = `{ exerciseId, type, isCorrect, completed, points,
xpAwarded, feedback, correctOptionId?, acceptedAnswers?, modelAnswer?,
explanation?, lesson: LessonProgress }`. The correct answer / model answer /
explanation are revealed here (and only after submission) so the learner can
review. `theory` is plain text with light markup (see `docs/database.md`). Lesson
slugs are globally unique, so no course context is needed in the path.

`POST /{slug}/submit` validates the answer shape per exercise type and returns
`422 INVALID_ANSWER` for malformed answers (unknown single-choice option, blank
short answer, or a `self_check` submission without a `correct`/`incorrect`
self-assessment). An exerciseId that does not belong to the lesson returns
`404 NOT_FOUND`. See `docs/database.md` for the grading and XP rules.

### 2.5 Exercises — `/api/v1/exercises`

Exercise content is served inside the lesson payload (`GET /lessons/{slug}`) and
graded through `POST /lessons/{slug}/submit`; there is no separate public
exercise resource yet. Exercise types and their answer shapes are documented in
`docs/database.md`. The endpoints below remain designed but not built.

| Method | Path | Purpose | Auth | Request | Response |
| ------ | ---- | ------- | ---- | ------- | -------- |
| GET | `/:id` | Exercise (answer hidden) | bearer | — | `200 Exercise` |
| GET | `/submissions` | Own submission history | bearer | `?exerciseId&cursor` | `200 { items, nextCursor }` |

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
| GET ✅ | `/me` | Own aggregate + per-course progress | bearer | — | `200 Progress` |
| GET | `/summary` | Dashboard summary | bearer | — | `200 { xp, level, streak, skills, recent }` |
| GET | `/skills` | Per-skill breakdown | bearer | `?range` | `200 SkillProgress[]` |
| GET | `/activity` | Activity timeline | bearer | `?range&cursor` | `200 { items, nextCursor }` |

`Progress` = `{ userId, lessonsStarted, lessonsCompleted, exercisesCompleted,
studyMinutes, xp, lastActivityAt, updatedAt, courses: CourseProgress[] }` where
`CourseProgress` = `{ courseId, slug, title, level, lessonsTotal,
lessonsStarted, lessonsCompleted }`. The original fields remain, so the response is
backward-compatible.

Progress is server-derived. There is deliberately no client-writable `PATCH`:
lesson start/completion is recorded by `POST /lessons/{slug}/start` and
`/submit`, and XP is awarded server-side once per exercise (`docs/security.md`,
`docs/database.md`).

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
  queries, not only in dependencies).
- `ADMIN` may manage catalog/content definitions.
- Ownership violations return `404` (not `403`) where revealing existence would
  leak data.

## 4. Related documents

- `docs/authentication.md` — token mechanics.
- `docs/security.md` — validation, rate limiting, prompt injection.
- `project-map/api-map.md` — condensed map used for navigation.

## Implemented extension endpoints (2026-10-18)

All routes below are relative to `/api/v1`. Private endpoints require the existing
Bearer access token. Responses use camelCase; identity always comes from the
access token, never a request userId.

| Method | Route | Input / result |
| --- | --- | --- |
| PATCH | `/users/me` | Optional displayName, email, englishLevel (A1–C2), preferredLanguage → UserResponse |
| GET | `/vocabulary?due=false&limit=50&offset=0&lessonId=<uuid>` | Own words; optional `lessonId` selects words saved for that lesson, `due=true` selects due flashcards |
| GET | `/vocabulary/stats` | Own learned-word count: `{ wordsLearned }` |
| POST | `/vocabulary` | word, translation, optional example and lessonId → item (201) |
| PATCH | `/vocabulary/{id}` | learned: boolean → item |
| DELETE | `/vocabulary/{id}` | Remove own word and reviews (204) |
| POST | `/vocabulary/{id}/review` | remembered: boolean → updated item/dueAt |
| GET | `/vocabulary/{id}/reviews?limit=50&offset=0` | Own review history |
| GET | `/streaks/me` | current, longest, lastActivityDate, timezone |
| GET | `/achievements/me` | Definitions with awardedAt or null |
| POST | `/auth/password-reset/request` | Public: email → generic message |
| POST | `/auth/password-reset/confirm` | Public: token, password → 204; invalid/expired/used → 400 |
| POST | `/ai/chat` | message, optional conversationId/lessonId/correctGrammar → persisted tutor response |
| POST | `/ai/chat/stream` | Same input → SSE delta/done/error events |
| GET | `/ai/conversations?limit=20&offset=0` | Own conversations |
| GET | `/ai/conversations/{id}?limit=50&offset=0` | Own message history |
| DELETE | `/ai/conversations/{id}` | Delete own conversation/messages (204) |
| POST | `/ai/explain` | studentAnswer, optional exerciseId/lessonId/topic → explanation |
| POST | `/ai/generate-exercise` | topic, exerciseType, optional level/difficulty → practice-only material |
| GET | `/ai/recommendations` | Deterministic next lessons, missed topics, vocabulary review |

List limits are capped at 100. Object ownership violations return 404. Duplicate
saved words return 409. Null/blank profile values and invalid CEFR values return
422; XP and numeric level cannot be updated here. Invalid generation returns 502,
missing/disabled AI returns 503, timeout 504, quotas/concurrency 429, oversized API
body 413. Generic reset-request responses do not disclose account existence.
All errors use the existing envelope; input values are excluded from validation
error details. Reset endpoints are independently rate-limited by IP/email hash.

Examples:

```json
{"word":"supportive","translation":"підтримуючий","example":"A supportive tutor helps me learn."}
```

```json
{"displayName":"Alex","englishLevel":"B1","preferredLanguage":"Ukrainian"}
```

Detailed AI request/response examples, limits and streaming fallback:
[ai.md](ai.md). SMTP/reset configuration: [development.md](development.md).

## Auth stabilization — 2026-10-28

Login/register can return `429 RATE_LIMITED` with `Retry-After` seconds until the
fixed window ends. Defaults: login 20/IP/minute and 10/email/minute; register
10/IP/hour. Existing success/error payloads are preserved.
`POST /users/me/password` remains `204`, now atomically revoking refresh sessions
and outstanding reset tokens; clients must sign in again. Existing access JWTs
retain their configured TTL (default 15 minutes). Strict refresh reuse continues
to revoke all user refresh sessions. See `authentication.md` for concurrency and
proxy trust policies.
