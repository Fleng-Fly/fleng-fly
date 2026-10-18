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
| `catalog` | 🟢 | read-only courses & lessons (`GET /courses`, `/courses/{slug}`, `/lessons/{slug}`) | db |
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
| `app/main.py` | 🟢 | app factory + `StaticFiles` mount serving `frontend/` |
| `frontend/` | 🟢 | static HTML/CSS/JS UI (no build step) |

### Current dependency direction (allowed)

```
health   ──► db
auth     ──► db, users.service
users    ──► db, auth.security
progress ──► db, auth (dependency)
catalog  ──► db
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

## Frontend (static HTML / CSS / vanilla JavaScript)

Served by FastAPI from `frontend/`; no framework and no build step. HTTP goes
through `frontend/js/api.js`; protected pages use `requireSession()`.

| Area | Page | Status | Notes |
| ---- | ---- | ------ | ----- |
| Landing | `/index.html` | 🟢 | hero + live backend status |
| Login | `/login.html` | 🟢 | real session |
| Register | `/register.html` | 🟢 | account creation |
| Dashboard | `/dashboard.html` | 🟢 | protected; profile + progress from the API |
| Courses | `/courses.html` | 🟢 | protected; catalog list (`GET /courses`) |
| Course | `/course.html?slug=` | 🟢 | protected; course detail + lesson list |
| Lesson | `/lesson.html?slug=` | 🟢 | protected; theory (`GET /lessons/{slug}`) |
| Settings | `/settings.html` | 🟢 | protected; profile display |
| Lesson player (quiz) | — | 🔴 | needs exercises + grading |
| Vocabulary / Practice / Challenges / Progress / AI Tutor | — | 🔴 | |

## AI layer

Not built (Python, inside the backend). Planned: provider protocol, `mock`
provider, `registry`, `prompts/*`, `safety`. See `plans/ai-plan.md`.


`frontend/css/star4life.css` adapts the `CSS.star4life/CSS/` visual reference for the static pages; FastAPI serves it at `/css/star4life.css` alongside `/api/v1`.
