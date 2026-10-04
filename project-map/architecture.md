# Project Map — Architecture

> Status: 🔴 documented only. Canonical detail: `docs/architecture.md`.

## System diagram

```
User
 ↓
Frontend  (Next.js) 🔴
 ↓  HTTPS · REST /api/v1
API       (NestJS controllers) 🔴
 ↓
Backend   (modular monolith) 🔴
 ├── Auth
 ├── Users
 ├── Catalog
 ├── Content
 ├── Exercises
 ├── Vocabulary
 ├── Progress
 ├── Gamification
 ├── Challenges
 ├── Recommendations
 ├── AI
 ├── Notifications
 ├── Subscriptions
 └── Analytics
 ↓  Prisma
Database  (PostgreSQL) 🔴

Backend ↔ AI  (@fleng/ai library) 🔴
```

## Layer boundaries

| From → To | Allowed? | Notes |
| --------- | -------- | ----- |
| Frontend → Backend API | ✅ | HTTP/JSON only |
| Frontend → Database | ❌ | Never |
| Frontend → AI provider | ❌ | Keys are server-side |
| Backend → Database | ✅ | Only via Prisma |
| Backend → `@fleng/ai` | ✅ | In-process import |
| `@fleng/ai` → Database | ❌ | Library is persistence-free |
| Module → other module's service | ✅ | Via exported service only |
| Module → other module's repository | ❌ | Forbidden |

## Deployment units (target)

1. `frontend` — Next.js app.
2. `backend` — NestJS API.
3. `@fleng/ai` — library, bundled into the backend (not deployed separately).

## Trust boundaries

- Browser is untrusted: validate everything at the API edge.
- AI provider output is untrusted: validate against a schema before use.
- The database is trusted but access is least-privilege.

## Evolution rules

- Keep the monolith until evidence justifies extraction (`docs/architecture.md §8`).
- Any new top-level directory must be added to this map and to `README.md`.
