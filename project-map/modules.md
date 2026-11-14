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
| Settings                                                 | `/settings.html`     | 🟢     | protected; profile/email editing, language preference, password change, logout                                    |
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
lesson tabs, questions, submission UI and preview. Practice and Test share
the same automatic advance and retry order. `frontend/js/letter-tiles.js` renders
the letter bank and slots for configured text exercises. The lesson page calls the existing
`catalog`, `exercises` and `vocabulary` APIs through `frontend/js/api.js`.
`exercises` now returns the caller's latest answer in lesson progress, and
`vocabulary` can filter owned words by `lessonId`. Migration `20261114_1200` adds
optional letter-tile configuration to exercises.

## Windows local launcher (2026-11-11)

`START-WINDOWS.cmd` runs the existing setup and dev scripts from its own folder.
The backend dependency `tzdata` supplies IANA time zones on Windows. The setup
instructions are in `ЗАПУСК-У-WINDOWS.md`; developer integration notes are in
`docs/learning-handoff.md`.

## SQLite database preparation

`app/db/prepare.py` checks SQLite write access, upgrades through Alembic, validates
tables/columns and seeds an empty catalog before `scripts/dev.mjs` or the
production launcher `backend/run.py` starts the server. `core/config.py` resolves env
files and SQLite paths independently of cwd; `db/session.py` creates the data
directory and configures every SQLite connection. Preparation runs once in the
launcher, outside ASGI workers; errors stop startup. PostgreSQL requires explicit
migration commands; there is no fallback. Free Render storage is ephemeral.

## Backend stabilization — 2026-10-28

- `auth/security.password_work`: shared AnyIO four-worker budget for async Argon2 paths.
- `auth/router`: persistent peer-IP/email throttling via `core/limits` before hashing.
- `auth/service`: conditional refresh claims, rollback, locked issuance and shared
  `invalidate_password_sessions` used by `users` and `password_reset`.
- `gamification.lock_learner`: PostgreSQL row lock / SQLite no-op write lock;
  auth/password/learning transactions use the same identity lock order.
- `tests/test_stabilization.py`: isolated file-SQLite concurrency suite, optional
  isolated PostgreSQL schemas; no application database used.
- `scripts/backend-stabilization-smoke.py`: temporary SQLite dev-server/API/restart checks.

No new modules/tables or migration. Settings only clears auth state and redirects
after password change. Live PostgreSQL/OpenRouter/SMTP remain unverified here.


## Fleng AI widget — 2026-11-01

- `frontend/js/ai-assistant.js`: shared authenticated Dashboard/Lessons floating
  chat, history selection/reload, composer, visibility and request states.
- `frontend/js/ai-stream.js`: bounded UTF-8 SSE reader; no build/dependency.
- `frontend/css/ai-assistant.css`: dark compact responsive window/focus styling.
- Existing `modules/ai`: authenticated configuration status, validated lesson/
  exercise context and request-ID deduplication using existing AIUsage.
- `20261101_1200_ai_request_id.py`: nullable request UUID + per-user unique index.
- `scripts/test-ai-stream.mjs`: standalone Node tests of stream framing/failures.

- `scripts/test-ai-api.mjs`: auth-refresh/raw-stream and no-retry client regressions.


## Leaderboard and hosting preparation — 2026-11-04

- Existing `gamification` router/service/schemas now own the authenticated
  all-time ranking. Window functions rank Profile XP with a stable UUID tie-break;
  Progress supplies completed lessons and batched LearningActivity supplies streaks.
  No new table, migration, package or service.
- `frontend/leaderboard.html`, `js/leaderboard.js`, `css/leaderboard.css` use the
  existing workspace sidebar/header and API/session helpers. Dashboard and sidebar
  link to the screen. Top 100 and own global position come from `/leaderboard`.
- `backend/run.py` + root `Procfile`: production uvicorn process without reload,
  Settings-based port and explicit proxy trust. `health/ready`: DB readiness.
- `.env.production.example` and `docs/deployment.md`: single-service HTTPS release
  with explicit migrations, optional initial catalog and managed PostgreSQL.

## Course surfaces — 2026-11-04

- `frontend/courses.html` + `js/courses.js`: published course catalog with local
  title/description search + CEFR filter; real course progress from `/progress/me`.
- `frontend/course.html` + `js/course.js`: slug-based course hero and ordered
  published lesson list; individual statuses from `/lessons/{slug}/progress`.
- Both reuse `js/workspace.js`, `css/dashboard.css`, shared `js/catalog-ui.js`
  state/progress rendering and scoped `css/courses.css`. No new backend module.
- `scripts/test-courses.mjs`: DOM regression coverage; real HTTP coverage in
  `scripts/backend-stabilization-smoke.py`. Browser/Stitch QA remains pending.

## Global assistant and security — 2026-11-04

`workspace.setWorkspaceUser()` owns initialization on all six protected pages.
`ai-assistant.js` owns singleton UI, selected-conversation restoration and destruction;
`api.js` signals session termination/cross-tab logout and accepts stream abort signals.
Lessons registers only lesson/exercise context IDs. Backend AI request schemas reject
extra fields; existing reservations now also enforce assembled input-token bounds.
Evidence: `docs/ai-security-audit.md`, `backend/tests/test_ai_security.py`,
`scripts/test-ai-widget.mjs`, `scripts/audit-ai-secrets.py`.

## SQLite runtime diagnostics — 2026-11-04

`backend/app/db/diagnostics.py` provides allowlisted SQLite exception categories,
post-migration and production FastAPI connection snapshots, and an existing-file
inspection CLI (`python -m app.db.diagnostics`). It reports schema/configuration
metadata only; no SQL parameters, connection URL, private rows or raw exceptions.
Alembic preserves existing application loggers. Preparation additionally checks
foreign keys, now() and SQLite RETURNING support; schema/write checks remain.
See `docs/render-sqlite-registration-diagnostics.md` for the live Render procedure
and the distinction between local success and unconfirmed live causation.


## Vocabulary flashcards — 2026-11-10

Vocabulary now includes flashcards.py: curated CourseVocabularyItem reads, owned FlashcardSession snapshots and completed-set handoff helper. No grading/XP changes.


## A0–B2 curriculum — 2026-11-10

`core/levels.py` centralizes Fleng A0 + CEFR A1–C2. `db/curriculum.py` validates packaged `db/content/curriculum-a0-b2.json` and preflights explicit draft/reviewed imports into existing models. No provider calls or test engine. Migration 20261110_1400 extends Course CHECK.

## Curriculum verification — 2026-11-11

`services/curriculum_validation/` audits the existing draft JSON through importer
schemas and the real objective grader; it never opens a DB or imports/publishes.
Local licensed evidence adapters, provenance/issue reports, SHA-guarded separate
draft normalization and opt-in bounded existing OpenRouter transport are owned
here. Entry points: `scripts/validate_curriculum.py` and
`scripts/prepare_curriculum_sources.py`. No new endpoint/table/frontend dependency.
See `docs/curriculum-validator.md`, source licenses and generated quality report.

## Local curriculum visual preview — 2026-11-11

`app/preview.py` is a separate development-only app factory over private prepared
SQLite + marker, with loopback/Host guards and normal JWT authentication restricted
to one reviewer UUID. `scripts/preview_curriculum.py` exclusively prepares/starts
that database through existing migrations/seed/draft import. Catalog, lesson
resolution, progress reads and course-word selection accept an internal
`include_drafts=False` keyword; only preview wrappers opt in. Standard routes and
publication flags remain unchanged; grading/XP services are reused.
`review_curriculum_browser.py` provides optional real Firefox BiDi screenshots.
See `docs/curriculum-visual-review.md` and `reports/curriculum-preview/`.
## Cross-platform backend commands

`scripts/backend.mjs` runs Python modules from `backend/` using the existing
virtualenv. npm database, demo and quality commands use it on all platforms.
It forwards arguments and exit codes and supports paths containing spaces.

## Desktop application and integration — 2026-11-14

`desktop/main.py` coordinates the user-data lock, logging and app window.
`desktop/runtime.py` owns the backend subprocess; `desktop/worker.py` prepares
the existing database and serves FastAPI on loopback. `desktop/chromium.py`
uses a dedicated Windows browser profile to observe the app window lifetime.
`desktop/bootstrap.py`, `desktop/diagnostics.py`, `desktop/build_windows.py`
and `desktop/launcher.c` provide source setup, diagnostics and portable builds.
`desktop/tests/` verifies process lifecycle and data persistence.
Local runtime/binaries remain ignored. The private curriculum reviewer requires
POSIX permissions; ordinary desktop learning works on Windows.
See [integration report](../docs/projectenglich-integration.md).


## PWA — 2026-11-13

Оновлено 2026-11-14: пропозиції завантажити/встановити додаток вилучено
з головної сторінки, навігації та offline-екрана; обробники встановлення й
окремі стилі видалено. `/install.html` зберігає лише довідку про доступ і прогрес.
Маніфест, іконки, реєстрація worker та offline fallback збережені;
кеш offline-екрана оновлено до v2. API й дані користувача не кешуються.
Далі: перевірка на фізичних пристроях.
Деталі: `docs/pwa-installation.md` (від кореня проєкту).

## Persistence and CI verification — 2026-11-14

- `app.db.backup`: explicit read-only-source SQLite online backup, integrity checks,
  private new file and overwrite refusal; no startup hook.
- `tests/test_database_pipeline.py`: Alembic-based SQLite/isolated PostgreSQL checks,
  idempotent seeds/imports, learner/card preservation and FK integrity.
- `.github/workflows/database.yml`: mandatory SQLite/application and disposable
  PostgreSQL jobs with an always-running success aggregator; no production access.
- Root npm commands expose the existing isolated draft preview without publication.
- Production target: managed PostgreSQL after an approved/rehearsed data transfer;
  actual hosting settings and data migration remain external manual operations.

## Git integration ? 2026-11-14

Combined desktop/PWA and database persistence work, preserving both sets of
npm commands and ignore rules. Database commands use the cross-platform backend
runner; persistence test counts include the new present-perfect lesson. Backup
permission-bit checks apply on POSIX; Windows backup protection uses inherited ACLs.

## Infrastructure transfer and recovery (2026-11-14)

- `backend/app/db/transfer.py`: explicit snapshot backup → typed schema/FK checks → locked empty PostgreSQL target → transactional import → complete row reconciliation → dry-run rollback or explicit apply. No startup/API hook.
- `backend/tests/test_database_transfer.py`: disposable SQLite refusal/rollback tests and opt-in real asyncpg learner transfer.
- `backend/tests/test_postgres_recovery.py`: pg_dump/pg_restore on two newly created disposable databases, typed comparison and auth/card resume.
- `scripts/check-test-report.py`: mandatory PostgreSQL JUnit gate, rejects missing/skipped/failed evidence.
- `.github/workflows/database.yml`: existing workflow, now includes docs/contracts, actionlint, pinned Ubuntu and PostgreSQL transfer/recovery tests. `.github/main-ruleset.json`: owner-importable main policy, not applied.
- Live observations/runbooks: `docs/09-deployment/final-infrastructure-integration.md`, `docs/05-database/transfer-and-recovery.md`. Hosted settings and new PostgreSQL drills remain pending.

## Default local development curriculum — 2026-11-14

`app/development.py` owns the npm dev-only preparation/factory: back up existing SQLite → existing Alembic preparation → idempotent unpublished curriculum import → loopback-only authenticated draft routes. It reuses `preview_router` with ordinary learner authentication; the separate private reviewer still passes its explicit UUID. `scripts/dev.mjs` starts this factory on 127.0.0.1; production/normal factories remain published-only. Existing users, sessions, XP and lesson data stay in the configured local file.
