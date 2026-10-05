# Project Map — Modules

> Status: M2/M3 implemented. Durable design: `docs/backend.md`, `docs/frontend.md`.
> Update when a module is created, renamed or gains a dependency.
> Legend: 🟢 implemented · 🟡 partial · 🔴 documented only.

## Backend (FastAPI / Python)

Feature modules live under `app/modules/<name>/`. A module exposes a service;
other modules import that service, not its internals.

| Module | Status | Owns | Depends on |
| ------ | ------ | ---- | ---------- |
| `health` | 🟢 | `/health` status + database check | db |
| `auth` | 🟢 | register/login/refresh/logout, credentials, sessions, tokens | db, users |
| `users` | 🟢 | `GET /users/me` profile read | db, auth |
| `progress` | 🟢 | `GET /progress/me` aggregate progress | db, auth |
| `catalog` | 🔴 | courses, lessons | — |
| `content` | 🔴 | grammar/reading/listening materials | catalog |
| `exercises` | 🔴 | exercise definitions, submissions, grading | catalog |
| `vocabulary` | 🔴 | words, user vocabulary, flashcards/SRS | users |
| `gamification` | 🔴 | XP, levels, streaks, achievements | progress |
| `challenges` | 🔴 | challenge definitions, participation | progress, gamification |
| `recommendations` | 🔴 | next-step suggestions | progress, vocabulary, ai |
| `ai` | 🔴 | conversations, messages; wraps the AI layer | ai layer, users, progress |
| `notifications` | 🔴 | in-app notification feed | users |
| `subscriptions` | 🔴 | plans, billing state | users |
| `analytics` | 🔴 | event recording | — |

### Infrastructure

| Component | Status | Purpose |
| --------- | ------ | ------- |
| `app/core/config.py` | 🟢 | pydantic-settings configuration (+ auth settings) |
| `app/core/errors.py` | 🟢 | `ApiError` + exception handlers → standard envelope |
| `app/core/schemas.py` | 🟢 | `CamelModel` base |
| `app/db/models.py` | 🟢 | SQLAlchemy models (`User`, `Profile`, `RefreshToken`, `Progress`) |
| `app/db/session.py` | 🟢 | async engine + `get_db` dependency |
| `app/api/deps.py` | 🟢 | `get_current_user` (Bearer access JWT) |
| `app/api/router.py` | 🟢 | aggregate `/api/v1` router |

### Current dependency direction (allowed)

```
health   ──► db
auth     ──► db, users.service
users    ──► db, auth.security
progress ──► db, auth (dependency)
db       ──► core/config
api      ──► core/config, auth.security
```

### Planned direction (do not create cycles)

```
catalog/content ──► db
exercises ──► catalog
progress  ──► gamification
recommendations ──► ai ──► AI layer
challenges ──► progress/gamification
```

## Frontend (Next.js / TypeScript)

| Area | Route | Status | Notes |
| ---- | ----- | ------ | ----- |
| Landing | `/` | 🟢 | hero + live backend status |
| Learn | `/learn` | 🟢 | protected; profile + progress from API |
| Login | `/login` | 🟢 | real session |
| Register | `/register` | 🟢 | account creation |
| Lessons | `/lessons/[id]` | 🔴 | needs catalog + lesson player |
| Vocabulary | `/vocabulary` | 🔴 | |
| Practice (hub, speaking, listening, reading, writing, grammar) | `/practice/*`, `/grammar` | 🔴 | |
| Challenges | `/challenges` | 🔴 | |
| Progress | `/progress` | 🔴 | |
| Profile | `/profile/[id]` | 🔴 | |
| AI Tutor | `/ai-tutor` | 🔴 | |
| Settings | `/settings` | 🔴 | |

## AI layer

Not built (Python, inside the backend). Planned: provider protocol, `mock`
provider, `registry`, `prompts/*`, `safety`. See `plans/ai-plan.md`.
