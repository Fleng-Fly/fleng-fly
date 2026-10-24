# Project Map — Modules

Demo preparation: `backend/app/db/demo.py` runs only when explicitly selected in
development/demo with local SQLite. It reuses auth registration and graded lesson
submission services, stores credentials in ignored `backend/data/`, and is invoked
by `npm run demo:prepare`. The normal startup remains `npm run dev`.
`scripts/demo.mjs` is the presentation wrapper: it calls preparation, starts
the existing dev server when needed, then checks HTTP health and demo accounts.
The executable root `start.sh` is the single-command entry point for this flow.

> Status: M2/M3 implemented. Durable design: `docs/backend.md`, `docs/frontend.md`.
> Update when a module is created, renamed or gains a dependency.
> Legend: 🟢 implemented · 🟡 partial · 🔴 documented only.

## Backend (FastAPI / Python)

Feature modules live under `app/modules/<name>/`. A module exposes a service;
other modules import that service, not its internals.

| Module            | Status | Owns                                                                                                      | Depends on                    |
| ----------------- | ------ | --------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `health`          | 🟢     | `/health` status + database check                                                                         | db                            |
| `auth`            | 🟢     | register/login/refresh/logout, credentials, sessions, tokens                                              | db, users                     |
| `users`           | 🟢     | `GET /users/me` profile read                                                                              | db, auth                      |
| `progress`        | 🟢     | `GET /progress/me` aggregate progress                                                                     | db, auth                      |
| `catalog`         | 🟢     | read-only courses & lessons (`GET /courses`, `/courses/{slug}`, `/lessons/{slug}` incl. public exercises) | db, exercises (public schema) |
| `content`         | 🔴     | grammar/reading/listening materials                                                                       | catalog                       |
| `exercises`       | 🟢     | exercises, submissions, grading; lesson start/submit/progress                                             | db, progress                  |
| `vocabulary`      | 🟢     | personal words, due queue, review history, learned-word count                                             | db, auth, gamification        |
| `gamification`    | 🟢     | daily activity, derived streaks, deterministic achievements                                               | db, config                    |
| `challenges`      | 🔴     | challenge definitions, participation                                                                      | progress, gamification        |
| `recommendations` | 🟢     | deterministic analytics in ai/context.py                                                                  | db, progress, vocabulary      |
| `ai`              | 🟢     | provider, tutor/history, explanation, practice, recommendations, SSE                                      | db, auth, core limits         |
| `notifications`   | 🔴     | in-app notification feed                                                                                  | users                         |
| `subscriptions`   | 🔴     | plans, billing state                                                                                      | users                         |
| `analytics`       | 🔴     | event recording                                                                                           | —                             |

### Infrastructure

| Component             | Status | Purpose                                                           |
| --------------------- | ------ | ----------------------------------------------------------------- |
| `app/core/config.py`  | 🟢     | pydantic-settings configuration (+ auth settings)                 |
| `app/core/errors.py`  | 🟢     | `ApiError` + exception handlers → standard envelope               |
| `app/core/schemas.py` | 🟢     | `CamelModel` base                                                 |
| `app/db/models.py`    | 🟢     | SQLAlchemy models (`User`, `Profile`, `RefreshToken`, `Progress`) |
| `app/db/session.py`   | 🟢     | async engine + `get_db` dependency                                |
| `app/api/deps.py`     | 🟢     | `get_current_user` (Bearer access JWT)                            |
| `app/api/router.py`   | 🟢     | aggregate `/api/v1` router                                        |
| `app/main.py`         | 🟢     | app factory + `StaticFiles` mount serving `frontend/`             |
| `frontend/`           | 🟢     | static HTML/CSS/JS UI (no build step)                             |

### Current dependency direction (allowed)

```
health   ──► db
auth     ──► db, users.service
users    ──► db, auth.security
progress ──► db, auth (dependency)
catalog  ──► db, exercises.schemas
exercises ──► db, progress.service
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

| Area                                                     | Page                 | Status | Notes                                                                                                             |
| -------------------------------------------------------- | -------------------- | ------ | ----------------------------------------------------------------------------------------------------------------- |
| Landing                                                  | `/index.html`        | 🟢     | hero + live backend status                                                                                        |
| Login                                                    | `/login.html`        | 🟢     | real session                                                                                                      |
| Register                                                 | `/register.html`     | 🟢     | account creation                                                                                                  |
| Dashboard                                                | `/dashboard.html`    | 🟢     | protected; sidebar, catalog search, current course, profile, progress, streak and learned-word count from the API |
| Courses                                                  | `/courses.html`      | 🟢     | protected; catalog list (`GET /courses`)                                                                          |
| Course                                                   | `/course.html?slug=` | 🟢     | protected; course detail + lesson list                                                                            |
| Lesson                                                   | `/lesson.html?slug=` | 🟢     | protected; Theory/Practice/Test/Vocabulary, grading, progress and saved words                                     |
| Settings                                                 | `/settings.html`     | 🟢     | protected; profile display                                                                                        |
| Lesson player (quiz)                                     | —                    | 🟢     | exercises, submission and grading via the exercises API                                                           |
| Vocabulary / Practice / Challenges / Progress / AI Tutor | —                    | 🔴     |                                                                                                                   |

## AI layer

Implemented inside `app/modules/ai/`: provider protocol, async OpenRouter adapter,
prompts/context, validation, quotas and persistence. Tests inject mocks; production
never silently substitutes a mock. See `plans/ai-plan.md`.

`frontend/css/star4life.css` adapts the `CSS.star4life/CSS/` visual reference for the static pages; FastAPI serves it at `/css/star4life.css` alongside `/api/v1`.

## Backend extension status — 2026-10-18 (supersedes planned rows above)

| Module          | Status                       | Owns / dependencies                                                                                   |
| --------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| vocabulary      | implemented                  | words, due queue, review history; db/auth/gamification                                                |
| gamification    | implemented                  | activity days, streak analytics, deterministic achievements; db/config                                |
| users           | extended                     | own profile PATCH, CEFR level/language; db/auth                                                       |
| password_reset  | implemented                  | reset request/confirm, SMTP; db/auth security/core limits                                             |
| ai              | implemented                  | OpenRouter transport, tutor/history, explanation, practice, recommendations, SSE; db/auth/core limits |
| recommendations | implemented in ai/context.py | deterministic learning analytics, no provider required                                                |

`core/body_limit.py` bounds API bodies; `core/limits.py` stores persistent windows
and serializes global AI reservations. `httpx` is now a runtime dependency.
`exercises/service.py` calls gamification within the learning transaction. AI
receives read-only analytics and never invokes learning mutation services.
`ai/` is a documentation entry point, not a separate Python service/package.
Runtime PostgreSQL/live AI verification remains blocked in this environment.

## Lessons workspace (2026-10-22)

`frontend/js/workspace.js` owns the shared Dashboard/Lessons sidebar, mobile
drawer, catalog search and profile menu. `frontend/js/lesson.js` owns only the
lesson tabs, questions, submission UI and preview. It calls the existing
`catalog`, `exercises` and `vocabulary` APIs through `frontend/js/api.js`.
`exercises` now returns the caller's latest answer in lesson progress, and
`vocabulary` can filter owned words by `lessonId`. No new database tables or
migrations are needed.

## Local database preparation

`app/db/prepare.py` upgrades local SQLite through Alembic and seeds an empty
catalog before `scripts/dev.mjs` starts the server. `core/config.py` resolves env
files and SQLite paths independently of cwd; `db/session.py` creates the data
directory and configures every SQLite connection. PostgreSQL and production
require explicit migration commands; no automatic seeding or fallback is used.
