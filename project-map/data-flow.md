# Project Map — Data Flow

> Status: M1 implemented. Details: `docs/architecture.md §5`, `docs/api.md`,
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

## Flow 2 — Frontend reads the learner profile (implemented)

```
/learn mounts → TanStack Query ['currentUser'] → getCurrentUser()
  → GET /api/v1/users/me
  → get_current_user_id (APP_ENV != production) returns DEV_USER_ID
  → users router → get_or_create_user(db, user_id)
  → SQLAlchemy select with selectinload(profile) → PostgreSQL
  → 200 { id, email, displayName, level, xp, createdAt } (camelCase)
  → UI shows level/XP; DB down → 503 DATABASE_UNAVAILABLE → error card + retry
```

`get_or_create_user` is a development convenience so the slice returns real rows
without a seed step; it is only reachable behind the dev dependency.

## Flow 3 — Authenticated request (planned)

```
Browser (access token in memory)
  → GET /api/v1/... (Authorization: Bearer)
  → get_current_user dependency verifies JWT → require_role if needed
  → router → service → SQLAlchemy → PostgreSQL
  → Pydantic response model
```

On `401`: browser calls `POST /auth/refresh` (httpOnly cookie) → server rotates
refresh token → returns new access token → original request retried once.

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
| Credentials, tokens | auth 🔴 | auth 🔴 |
| User / Profile | users 🟢 | users 🟢, others later |
| Catalog/content | catalog 🔴 | all users later |
| Progress/XP/vocabulary | progress/gamification/vocabulary 🔴 | dashboards later |
| AI conversations | ai 🔴 | ai 🔴 |
