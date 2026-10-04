# Project Map — Modules

> Status: M1 implemented. Durable design: `docs/backend.md`, `docs/frontend.md`.
> Update when a module is created, renamed or gains a dependency.
> Legend: 🟢 implemented · 🟡 partial · 🔴 documented only.

## Backend (FastAPI / Python)

Feature modules live under `app/modules/<name>/`. A module exposes a service;
other modules import that service, not its internals.

| Module | Status | Owns | Depends on |
| ------ | ------ | ---- | ---------- |
| `health` | 🟢 | `/health` status + database check | db |
| `users` | 🟢 | `/users/me` profile read (dev stub) | db |
| `auth` | 🔴 | credentials, sessions, tokens | users |
| `catalog` | 🔴 | courses, lessons | — |
| `content` | 🔴 | grammar/reading/listening materials | catalog |
| `exercises` | 🔴 | exercise definitions, submissions, grading | catalog |
| `vocabulary` | 🔴 | words, user vocabulary, flashcards/SRS | users |
| `progress` | 🔴 | lesson/course progress | catalog, exercises, gamification |
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
| `app/core/config.py` | 🟢 | pydantic-settings configuration |
| `app/core/errors.py` | 🟢 | exception handlers → standard envelope |
| `app/core/schemas.py` | 🟢 | `CamelModel` base |
| `app/db/models.py` | 🟢 | SQLAlchemy models (`User`, `Profile`) |
| `app/db/session.py` | 🟢 | async engine + `get_db` dependency |
| `app/api/deps.py` | 🟢 | `get_current_user_id` (DEV ONLY) |
| `app/api/router.py` | 🟢 | aggregate `/api/v1` router |

### Current dependency direction (allowed)

```
health ──► db
users  ──► db
db     ──► core/config
api    ──► core/config
```

### Planned direction (do not create cycles)

```
auth ──► users
progress ──► gamification
recommendations ──► ai ──► AI layer
challenges ──► progress/gamification
```

## Frontend (Next.js / TypeScript)

| Area | Route | Status | Notes |
| ---- | ----- | ------ | ----- |
| Landing | `/` | 🟢 | hero + live backend status |
| Learn | `/learn` | 🟢 | profile from API + placeholder lessons |
| Login | `/login` | 🟡 | UI scaffold; no auth |
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
