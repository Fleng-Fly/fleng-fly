# Project Map — Data Flow

> Status: M2/M3 implemented. Details: `docs/architecture.md §5`, `docs/api.md`,
> `docs/database.md`.

## Flow 1 — Frontend loads backend status (implemented)

```
Browser mounts BackendStatus (client component)
  → TanStack Query ['health'] → getHealth() → apiFetch('/health')
  → GET http://localhost:3001/api/v1/health
  → FastAPI router → get_health(db) → `SELECT 1` in try/except
  → 200 { status, service, timestamp, database: up|down }
  → badge shows "Backend ● Online" (with db state) or "● Offline" on error
```

Refetches every 15s. When the backend is unreachable, the client throws
`ApiError(status 0, NETWORK_ERROR)` and the UI shows Offline — it never crashes.

## Flow 2 — Authentication & session (implemented)

```
Register/Login form
  → AuthProvider.login() → apiFetch('/auth/login')
  → POST /api/v1/auth/login {email,password}
  → auth service: argon2id verify → access JWT + opaque refresh token
  → refresh token stored SHA-256-hashed; raw value set as HttpOnly cookie
  → 200 { accessToken, user } → token kept in memory, user in AuthProvider

Reload / expired access token
  → GET /users/me returns 401
  → client POSTs /auth/refresh (cookie) → server rotates the token
  → 200 { accessToken } → original request retried once

Reuse of a revoked refresh token
  → all of the user's active refresh tokens are revoked → 401 REFRESH_TOKEN_REUSED
```

## Flow 3 — Authenticated profile & progress (implemented)

```
/learn mounts → AuthProvider resolved, access token in memory
  → GET /api/v1/users/me   (Authorization: Bearer)
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

## Flow 4 — Lesson completion (planned)

```
POST /lessons/:id/complete
  → exercises grades submissions
  → progress records LessonProgress
  → gamification updates XpEvent, Streak, achievements
  → analytics records event (best-effort)
```

## Flow 5 — AI tutor turn (planned)

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
| Catalog/content | catalog 🔴 | all users later |
| XP/vocabulary | gamification/vocabulary 🔴 | dashboards later |
| AI conversations | ai 🔴 | ai 🔴 |
