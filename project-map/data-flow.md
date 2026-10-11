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
  → requireSession(): js/session.js → GET /api/v1/users/me (Authorization: Bearer)
      → on 401, api.js refreshes once from the HttpOnly cookie and retries
      → no session → redirect to /login.html
  → get_current_user verifies the JWT → loads User + Profile
  → 200 { id, email, displayName, level, xp, createdAt }
  → GET /api/v1/progress/me
  → progress service reads the user's aggregate row (scoped to the token subject)
  → 200 { userId, lessonsStarted, lessonsCompleted, studyMinutes, ... }
  → UI shows name/level/XP and the progress counters; no fake data
  → DB down → 503 DATABASE_UNAVAILABLE → error card + retry
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
  → published lesson of a published course → 200 LessonDetail (theory)
  → theory rendered with textContent (headings / lists / paragraphs only)
```

Content is read-only and seeded by `backend/app/db/seed.py`.

## Flow 5 — Lesson completion (planned)

```
POST /lessons/:id/complete
  → exercises grades submissions
  → progress records LessonProgress
  → gamification updates XpEvent, Streak, achievements
  → analytics records event (best-effort)
```

## Flow 6 — AI tutor turn (planned)

```
POST /ai/conversations/:id/messages
  → ai module: ownership check + context assembly + guardrails
  → AI layer builds prompt → provider.complete()
  → validate output → persist AIMessage(user + assistant)
```

## Data ownership summary

| Data | Writer | Reader |
| ---- | ------ | ------ |
| Credentials, sessions/tokens | auth 🟢 | auth 🟢 |
| User / Profile | auth 🟢 (registration) | users 🟢 |
| Progress (aggregate) | server-side / progress 🟢 | progress 🟢 |
| Catalog/content (courses, lessons) | catalog 🟢 (seed) | logged-in users 🟢 |
| XP/vocabulary | gamification/vocabulary 🔴 | dashboards later |
| AI conversations | ai 🔴 | ai 🔴 |
