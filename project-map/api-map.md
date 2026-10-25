# Project Map — API Map

> Status: M2/M3 implemented. Full contracts: `docs/api.md`. Keep this summary in
> sync when endpoints are added/changed.
> Legend: ✅ implemented · ⬜ planned.

Base: `/api/v1` · Auth: `Bearer` access token unless noted · Errors: standard
envelope (`docs/api.md §1`).

## Health

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/health` | public | ✅ |

Response: `{ status: "ok", service: "backend", timestamp, database: "up" | "down" }`.

## Auth

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| POST | `/auth/register` | public | ✅ |
| POST | `/auth/login` | public | ✅ |
| POST | `/auth/refresh` | refresh cookie | ✅ |
| POST | `/auth/logout` | refresh cookie | ✅ |
| POST | `/auth/verify-email` | token | ⬜ |
| POST | `/auth/forgot-password` | public | ⬜ |
| POST | `/auth/reset-password` | token | ⬜ |
| GET | `/auth/me` | bearer | ⬜ (use `/users/me`) |

## Users

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/users/me` | bearer | ✅ |
| PATCH | `/users/me` | bearer | ✅ |
| POST | `/users/me/password` | bearer | ✅ |
| DELETE | `/users/me` | bearer | ⬜ |
| GET | `/users/:id` | bearer (limited) | ⬜ |
| GET | `/users/me/settings` | bearer | ⬜ |
| PATCH | `/users/me/settings` | bearer | ⬜ |

## Courses

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/courses` | public | ✅ |
| GET | `/courses/{slug}` | public | ✅ |
| POST | `/courses` | admin | ⬜ |
| PATCH | `/courses/{slug}` | admin | ⬜ |
| DELETE | `/courses/{slug}` | admin | ⬜ |

List returns `CourseSummary[]` ordered by position; detail returns the course and
its published lessons. Drafts and unpublished lessons are invisible (`404`).

## Lessons

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/lessons/{slug}` | public | ✅ |
| POST | `/lessons/{slug}/start` | bearer | ✅ |
| POST | `/lessons/{slug}/submit` | bearer | ✅ |
| GET | `/lessons/{slug}/progress` | bearer | ✅ |

`GET /lessons/{slug}` returns theory + course context + public exercises (never
answer keys). Lesson slugs are globally unique. `/start` is idempotent;
`/submit` takes `{ exerciseId, answer, selfAssessment? }` and returns the grading
result + lesson progress.
`GET /lessons/{slug}/progress` includes each exercise's latest answer for the
authenticated caller; no answer keys are exposed by this read endpoint.

## Exercises

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/exercises/:id` | bearer |
| POST | `/exercises/:id/submit` | bearer |
| GET | `/exercises/submissions` | bearer |

## Vocabulary

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/vocabulary/words` | bearer |
| GET | `/vocabulary/me` | bearer |
| POST | `/vocabulary/me` | bearer |
| PATCH | `/vocabulary/me/:id` | bearer |
| DELETE | `/vocabulary/me/:id` | bearer |
| GET | `/vocabulary/reviews/due` | bearer |
| POST | `/vocabulary/reviews` | bearer |

## Progress

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/progress/me` | bearer | ✅ |
| GET | `/progress/summary` | bearer | ⬜ |
| GET | `/progress/courses/:courseId` | bearer | ⬜ |
| GET | `/progress/skills` | bearer | ⬜ |
| GET | `/progress/activity` | bearer | ⬜ |

`/progress/me` also returns `exercisesCompleted`, `xp` and a `courses[]`
breakdown with `lessonsStarted` and `lessonsCompleted` per course (additive).

## Challenges

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/challenges` | bearer |
| GET | `/challenges/:id` | bearer |
| POST | `/challenges/:id/join` | bearer |
| GET | `/challenges/:id/leaderboard` | bearer |

## AI

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/ai/conversations` | bearer |
| POST | `/ai/conversations` | bearer |
| GET | `/ai/conversations/:id` | bearer |
| POST | `/ai/conversations/:id/messages` | bearer |
| POST | `/ai/writing/correct` | bearer |
| POST | `/ai/grammar/explain` | bearer |
| GET | `/ai/recommendations` | bearer |

## Notifications

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/notifications` | bearer |
| POST | `/notifications/:id/read` | bearer |
| POST | `/notifications/read-all` | bearer |

## Internal

| Method | Path | Auth |
| ------ | ---- | ---- |
| GET | `/health` | public |

## Authorization rules

- `USER`: own resources only (`userId` scoping enforced in queries).
- `ADMIN`: manage catalog/content.
- Ownership violations return `404` where existence is sensitive.

## Implemented extensions — 2026-10-18

All prefixed `/api/v1`; see docs/api.md for request/response contracts:

- `PATCH /users/me` (Bearer; own profile, email, preferred language).
- `POST /users/me/password` (Bearer; verifies current password and hashes the replacement).
- `GET|POST /vocabulary`, `PATCH|DELETE /vocabulary/{id}` (Bearer, own rows).
- `GET /vocabulary?lessonId=<uuid>` filters the caller's words to one lesson.
- `POST /vocabulary/{id}/review`, `GET /vocabulary/{id}/reviews` (Bearer).
- `GET /vocabulary/stats` (Bearer) returns the caller's learned-word count.
- `GET /streaks/me`, `GET /achievements/me` (Bearer; no client award route).
- `POST /auth/password-reset/request|confirm` (public, rate-limited).
- `POST /ai/chat`, `POST /ai/chat/stream` (Bearer).
- `GET /ai/conversations`, `GET|DELETE /ai/conversations/{id}` (Bearer, own rows).
- `POST /ai/explain`, `POST /ai/generate-exercise` (Bearer, no official XP/grading).
- `GET /ai/recommendations` (Bearer, deterministic, works without provider).

These actual routes supersede earlier proposed AI/vocabulary route names above.
