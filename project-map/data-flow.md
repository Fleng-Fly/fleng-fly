# Project Map — Data Flow

> Status: M2/M3 implemented. Details: `docs/architecture.md §5`, `docs/api.md`,
> `docs/database.md`.

## Flow 1 — Frontend loads backend status (implemented)

```
Browser loads index.html → js/home.js
  → mountBackendStatus() → getHealth() → apiFetch('/health')
  → GET /api/v1/health  (same origin as the page)
  → FastAPI router → get_health(db) → `SELECT 1` in try/except
  → 200 { status, service, timestamp, database: up|down }
  → badge shows "Backend ● Online · db up|down" or "● Offline" on error
```

Refetches every 15s. When the backend is unreachable, the client throws
`ApiError(status 0, NETWORK_ERROR)` and the UI shows Offline — it never crashes.

## Flow 2 — Authentication & session (implemented)

```
Register/Login form (register.html / login.html + js/*.js)
  → login() → apiFetch('/auth/login')
  → POST /api/v1/auth/login {email,password}
  → auth service: argon2id verify → access JWT + opaque refresh token
  → refresh token stored SHA-256-hashed; raw value set as HttpOnly cookie
  → 200 { accessToken, user } → access token kept in memory (js/api.js)

Reload / expired access token
  → GET /users/me returns 401
  → client POSTs /auth/refresh (cookie) → server rotates the token
  → 200 { accessToken } → original request retried once

Reuse of a revoked refresh token
  → all of the user's active refresh tokens are revoked → 401 REFRESH_TOKEN_REUSED
```

## Flow 3 — Authenticated profile & progress (implemented)

```
/dashboard.html loads → js/dashboard.js main()
  → requireSession({ throwOnUnavailable: true }): js/session.js
  → GET /api/v1/users/me (Authorization: Bearer)
      → on 401, api.js refreshes once from the HttpOnly cookie and retries
      → no session → redirect to /login.html
  → get_current_user verifies the JWT → loads User + Profile
  → 200 { id, email, displayName, level, xp, createdAt }
  → GET /api/v1/progress/me, /streaks/me, /vocabulary/stats
  → progress service reads aggregate plus published course lesson counts
  → streak service reads activity days; vocabulary stats counts own learned words
  → UI shows name/level/XP, lesson completion ratio, estimated time,
    current course, streak and learned-word count; no fake data
  → API error → unavailable metric/error card + retry
  → search submits → GET /courses then /courses/{slug} for each published course
    → matching published courses/lessons shown as navigable results
```

Identity always comes from the access token subject; a user can only ever read
their own profile and progress.

## Flow 4 — Catalog read (implemented)

```
courses.html → js/courses.js → listCourses() → GET /api/v1/courses
  → catalog service: published courses + published-lesson counts, ordered → 200
  → cards (title, CEFR level, description, lesson count)

course.html?slug=... → getCourse(slug) → GET /api/v1/courses/{slug}
  → published course + published lessons (ordered) → 200 CourseDetail
  → missing/unpublished → 404 NOT_FOUND → friendly "not found" state

lesson.html?slug=... → getLesson(slug) → GET /api/v1/lessons/{slug}
  → published lesson of a published course → 200 LessonDetail
    (theory + public exercises, never answer keys)
  → theory rendered with textContent (headings / lists / paragraphs only)
```

Content is read-only and seeded by `backend/app/db/seed.py` (courses, lessons and
exercises).

## Flow 5 — Lesson start, submission and completion (implemented)

```
lesson.html?slug=... → startLesson(slug) → POST /api/v1/lessons/{slug}/start
  → get-or-create LessonProgress (in_progress) + Progress.lessons_started += 1
  → 200 LessonProgress (per-exercise state) → progress summary rendered

Answer an exercise → submitAnswer(slug, {exerciseId, answer, selfAssessment?})
  → POST /api/v1/lessons/{slug}/submit
  → exercises module: resolve lesson+exercise (404 if not the lesson's exercise)
  → validate answer shape (422 INVALID_ANSWER if malformed)
  → grade single_choice / text; record self-assessment for self_check
  → upsert ExerciseSubmission; award XP once (conditional UPDATE on xp_awarded)
  → recompute lesson completion; on first completion:
        LessonProgress -> completed
        Progress.lessons_completed += 1, study_minutes += estimatedMinutes
  → 200 SubmissionResult (correctness, +XP, revealed answer, explanation, lesson)
  → frontend updates the result area and the progress summary

GET /api/v1/progress/me
  → aggregate + derived exercisesCompleted + xp + per-course progress
```

XP is server-side only (never client-supplied) and cannot be farmed by retries.

The Lessons workspace adds a Theory tab from `LessonDetail.theory`, Practice
and Test views over the same exercises and submissions, and a Vocabulary tab.
The player reads `GET /lessons/{slug}/progress` before starting and resumes
from the first incomplete question. Progress includes the caller's latest
submitted answer for page reload; unsent drafts stay in memory. Vocabulary
calls `GET /vocabulary?lessonId=<lesson UUID>&offset=...&limit=30`, which filters
by both authenticated user and lesson. Dashboard reads the same persisted
progress through `GET /progress/me`.

## Flow 6 — Gamification (planned)

```
Lesson completion → XpEvent, Streak, Achievement updates
```

## Flow 7 — AI tutor turn (planned)

```
POST /ai/conversations/:id/messages
  → ai module: ownership check + context assembly + guardrails
  → AI layer builds prompt → provider.complete()
  → validate output → persist AIMessage(user + assistant)
```

## Data ownership summary

| Data                                                   | Writer                           | Reader             |
| ------------------------------------------------------ | -------------------------------- | ------------------ |
| Credentials, sessions/tokens                           | auth 🟢                          | auth 🟢            |
| User / Profile                                         | auth 🟢 (registration)           | users 🟢           |
| Progress (aggregate)                                   | exercises + progress 🟢          | progress 🟢        |
| Catalog/content (courses, lessons, exercises, answers) | catalog/exercises 🟢 (seed)      | logged-in users 🟢 |
| Submissions / lesson progress                          | exercises 🟢                     | progress 🟢        |
| XP                                                     | exercises 🟢 (once per exercise) | dashboard 🟢       |
| Streaks / achievements                                 | gamification 🔴                  | dashboards later   |
| AI conversations                                       | ai 🔴                            | ai 🔴              |

## Implemented extension flows — 2026-10-18

- Graded submission → learner row lock → existing deterministic grading/XP/progress
  → unique timezone-policy activity day → deterministic achievement rules → commit.
- Vocabulary review → ownership + learner lock → review record/due state → daily
  activity/achievement rules → commit. Adding words evaluates vocabulary awards.
- Reset request → shared IP/email hash counters → generic response → hashed expiring
  token and configurable SMTP delivery. Confirm → atomic token claim → password
  hash update + reset-token/refresh-session invalidation → commit.
- AI chat → auth/ownership/input checks → bounded read-only context/history → shared
  rate/budget/concurrency reservation commit → OpenRouter → validate complete output
  → atomic user+assistant pair + usage commit. Failure leaves history untouched.
- AI stream → same checks/reservation → upstream SSE parsing → delta events → only
  complete streams commit; otherwise error event/cancellation and failed accounting.
- Recommendations → latest incorrect exercise submissions grouped by lesson,
  unlearned vocabulary and next published lessons at CEFR level; no provider call.

AI has no privileged mutation tools or hidden official answer keys. Browser only
calls FastAPI. Provider transport is persistence-free and swappable via Protocol.

## Local startup

`npm run dev` → Python `app.db.prepare` → shared config/async engine → SQLite
Alembic upgrade → seed only if the course catalog is empty → uvicorn serves UI
and API. Users, refresh sessions, submissions, XP and progress persist in the
same ignored `backend/data/fleng.db` across restarts. PostgreSQL remains an
explicit DATABASE_URL choice with manual migrations.

## Stabilized auth writes — 2026-10-28

Login/register → persistent IP limit (and normalized-email login limit) → bounded
Argon2 worker → identity lock and credential recheck → session commit.
Refresh → resolve hashed token owner → identity lock → conditional token claim →
successor + link + revocation commit together; replay commits whole-set revocation.
Password change/reset → same identity lock → hash update + refresh/reset token
revocation in one transaction → Settings returns to login (change flow).
Access JWTs retain their configured expiry. SQLite serializes writes through a
no-op UPDATE; PostgreSQL uses a user-row lock. Quota keys are hashed and shared
by workers through the existing database. See `docs/authentication.md`.
