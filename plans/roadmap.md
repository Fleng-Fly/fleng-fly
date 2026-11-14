# Roadmap

> Status: **active**. Update after every stage. Current status board:
> `plans/milestones.md`.

Current frontend phase (2026-10-22): Dashboard and Lessons have been implemented
on the existing static frontend and SQLite local workflow. Lessons now has a
shared workspace, Theory/Practice/Test/Vocabulary tabs, real grading and
resume, and responsive layouts. Exact Figma comparison awaits the target
screen reference; Login/Sign Up is the next requested UI phase. The historical
stage descriptions below record earlier architecture decisions.

## Learning interactions — 2026-11-11

- **Completed:** automatic next question, delayed retries, letter tiles and fixed
  short answers with server-side grading and once-only XP. Self-check incorrect
  assessments remain incomplete.
- **Completed:** tzdata dependency and Windows start instructions/launcher.
- **Completed 2026-11-14:** integrated into `fleng-fly`, preserving newer curriculum
  and flashcard work. The copied development database was migrated and seeded.
  See `docs/projectenglich-integration.md`.

## Netlify publication boundary — 2026-11-04

- **Completed locally:** root `netlify.toml` uses `base = "frontend"` and
  `publish = "."` to publish only `frontend/` and avoid root pnpm installation,
  with no build step or SPA fallback; future `/api/*` HTTPS proxy is commented out.
  Netlify local artifacts are ignored. Only the confirmed trailing empty YAML
  document was removed from the existing pnpm lockfile; no dependency update.
- **Pending:** user push and corrected Netlify deployment, deploy-file inspection
  and public HTTP checks from `docs/deployment.md`. The previous deployment's
  repository exposure is not resolved publicly by a local commit.
- **Blocked on external configuration:** FastAPI is not hosted; authentication,
  catalog/user APIs, progress and AI cannot work on static hosting alone.
- **Next:** provision Python hosting and persistent PostgreSQL, supply backend
  secrets (OpenRouter key stays backend-only), run migrations, activate the real
  proxy and verify HTTPS sessions, readiness, persistence and optional SSE.
- **Separate follow-up:** reconcile the lockfile's missing root `prettier`
  devDependency before depending on frozen pnpm installation; no package
  installation or version change is part of this deployment fix.

## MVP definition

A signed-in learner can:

1. Register, log in, log out, and keep a session.
2. Browse a published course and its lessons.
3. Complete lessons with graded exercises and resume progress.
4. Build and review a personal vocabulary list (basic SRS).
5. See progress, XP, level and a daily streak.
6. Ask an AI tutor a question and get an answer.

Everything else (speaking feedback, challenges, billing, notifications,
analytics) is post-MVP but the architecture leaves room for it.

## Stages

### Stage 0 — Foundation ✅ completed

Engineering groundwork only: repository structure, AGENTS rules, architecture
docs, project map, plans, design language, README, gitignore.

**Exit criteria:** docs consistent with each other; project map present; no
application code; clean commit.

### Stage 1 — Minimal Frontend + Backend ✅ completed

pnpm workspace + Python/FastAPI backend; SQLAlchemy async `User` + `Profile`
with an Alembic migration; health + users (dev auth stub) endpoints; Next.js
landing/learn/login with a live backend-status indicator.

**Exit criteria met:** `pnpm lint`, `typecheck`, `test`, `build` pass; the
frontend calls the real API; the database workflow is documented.

### Stage 1b — Backend core: authentication & progress ✅ completed

Email/password authentication (`POST /auth/register`, `/login`, `/refresh`,
`/logout`) with argon2id hashing, short-lived access JWTs and rotating refresh
tokens stored hashed (reuse detection). `GET /users/me` is read-only and
authenticated; `GET /progress/me` returns aggregate progress. Refresh tokens and
progress are persisted with an Alembic migration. The dev auth stub is removed.

**Exit criteria met:** auth and progress are exercised by an automated test suite
(register/login/refresh/rotation/reuse/logout/protected/cross-user isolation).

**Settings follow-up completed:** own profile and email editing (`PATCH
/users/me`), language preference and authenticated password changes. Email
verification and rate limiting remain separate follow-ups (see
`plans/security-plan.md`).

### Stage 1c — Static frontend served by FastAPI ✅ completed

The Next.js/React/TypeScript frontend was replaced by plain **HTML/CSS/vanilla
JavaScript** served from the backend (`frontend/`, no build step). One server
(FastAPI) serves both `/api/v1` and the UI on the same origin; the CSRF origin
check accepts same-origin requests. Landing, register, login, logout, a
protected dashboard (profile + progress) and a profile/settings view are wired
to the existing auth/progress API.

**Exit criteria met:** the app runs from one `uvicorn` process; the auth journey
works; static-serving, same-origin and existing auth/progress tests pass.

### Stage 2 — Learning MVP ✅ completed

Courses, lessons, exercises, submissions, grading; lesson start/complete;
progress recording.

- ✅ `Course`/`Lesson` models + migration `20261011_1200_catalog`; idempotent seed.
- ✅ Read-only catalog API (`GET /courses`, `/courses/{slug}`, `/lessons/{slug}`),
  published-only, with tests.
- ✅ Frontend catalog, course detail and lesson-theory pages.
- ✅ `Exercise`/`ExerciseSubmission`/`LessonProgress` + migration
  `20261011_1400_exercises`; `single_choice`, `text` and `self_check` types.
- ✅ Lesson start/submit/progress endpoints with server-side grading; answer keys
  never exposed before submission.
- ✅ Once-only XP and server-derived lesson/course progress on `/progress/me`.
- ✅ Lesson page and dashboard render real persisted data.

**Exit criteria met:** the lesson flow works from the API with tests; progress is
queryable per course.

### Stage 3 — Vocabulary & gamification

Vocabulary words, user vocabulary, flashcards/SRS reviews; XP ledger, levels,
streaks, achievements.

**Exit criteria:** review flow updates scheduling; completing lessons updates
XP/streak/achievements idempotently.

### Stage 4 — Frontend MVP

Dashboard visual/integration code is in the working tree: responsive
sidebar, catalog search, real course/progress/streak/learned-word metrics.
Standalone Lessons redesign, auth redesign and AI assistant UI remain later
phases. Dashboard Firefox checks at 360/768/desktop passed on local SQLite
(2026-10-22); exact Figma comparison and live PostgreSQL checks remain pending.

Static pages for dashboard, learn/lessons, quizzes, vocabulary, progress and the
AI tutor; shared layout and design tokens; critical Playwright flows.

**Exit criteria:** the MVP definition above is usable in a browser on desktop
and mobile.

### Stage 5 — AI tutor

Python AI layer with a `mock` + one real provider; tutor conversations; writing
correction; recommendations; guardrails and rate limits.

**Exit criteria:** AI features tested with the mock provider; provider is
swappable by configuration; prompt-injection mitigations documented and tested.

### Stage 6 — Polish & launch

Speaking/listening/reading/writing practice depth, challenges, notifications,
analytics, accessibility pass, performance pass, deployment, monitoring.

**Exit criteria:** production deployment with backups and monitoring; launch
checklist from `docs/deployment.md` and `docs/security.md` satisfied.

## Sequencing rules

- Database schema lands with the module that owns it, not all upfront.
- Backend endpoints land with tests and the security checklist.
- Frontend consumes only documented API contracts.
- Do not start a stage until the previous stage's exit criteria are met, unless
  the work is explicitly independent (e.g. design docs).

## Out of scope (explicitly deferred)

Microservices, message broker, GraphQL, native mobile apps, MFA, OAuth, real-time
features, custom model training, multi-region. Each requires a written
justification before adoption (see `AGENTS.md` rules 2/9).

## Backend completion update — 2026-10-18

Vocabulary/reviews, streaks/achievements, profile updates, password reset and
OpenRouter tutoring APIs are implemented and tested with mocked AI and ORM
fixtures. Adaptive recommendations and SSE are included. Live PostgreSQL and paid
OpenRouter validation remain blocked; do not label deployment integration as
complete. See [ai-plan.md](ai-plan.md) for completed/blocked/next details. New API
frontend wiring is outside this backend task. No commits were made, per request.

## Local development update — 2026-10-22

SQLite is the local default. `npm run dev` prepares the persistent file with
Alembic and an initial catalog, then runs the existing FastAPI/static frontend.
PostgreSQL remains an explicit deployment option. Lessons UI and AI scope are
unchanged. Dashboard Firefox scenarios passed; Figma comparison and live PostgreSQL
checks remain separate.

## Backend stabilization — 2026-10-28

Completed: atomic refresh rotation, login/register throttling, bounded password
workers, password/reset refresh-session revocation and SQLite concurrent-write
regressions. Existing learning/UI contracts are preserved; Settings signs out
after changing the password. No new product features or schema changes.
Next: live PostgreSQL migration/concurrency verification and SMTP/OpenRouter
integration. Current runtime evidence: `docs/backend-stabilization-report.md`.


## Floating assistant integration — 2026-11-01

- **Completed:** Dashboard/Lessons reusable widget, owned history selection/new chat,
  incremental UTF-8 SSE, safe text rendering, minimize/close lifecycle.
- **Completed:** authenticated readiness API, published lesson/exercise context,
  request-ID deduplication on existing AIUsage (migration `20261101_1200`).
- **Completed:** mocked backend/parser regression checks, dev-server SQLite smoke,
  independent self-review; docs and project map updated.
- **Next / unverified:** actual browser QA at 360/768/desktop, virtual keyboards,
  paid OpenRouter with a configured model/key, live PostgreSQL integration.
- **Commits:** not created, per explicit user instruction.

Evidence: `docs/ai-assistant-integration.md`. Standalone AI Tutor page remains deferred.


## Leaderboard + hosting preparation — 2026-11-04

- **Completed:** authenticated all-time XP ranking, top-3 cards, learner table,
  own rank, short/empty/loading/error/retry states and responsive styles.
- **Completed:** production launcher/Procfile, environment template, secure-cookie
  and secret guards, exact HTTPS CORS origins, DB readiness and deployment notes.
- **Next:** choose hosting/managed PostgreSQL and supply production secrets;
  apply migrations and verify public HTTPS auth, proxy trust and optional AI.
- **Not verified:** exact Figma comparison (source not supplied), browser layout
  at 360/768/desktop (browser unavailable), live hosting/PostgreSQL/OpenRouter/SMTP.


## Render SQLite startup fix — 2026-11-04

- **Completed:** production launcher performs SQLite write probe, existing Alembic
  upgrades, mapped-schema validation and empty-catalog seed before single-worker
  Uvicorn. No user-data reset; PostgreSQL release migrations remain explicit.
- **Completed:** regression coverage for fresh production disk, registration,
  login, refresh, Dashboard APIs, XP/session/account persistence on process restart,
  unwritable files/directories, invalid path, memory DB and incorrectly stamped DB.
- **Completed:** existing checks, separate self-review, docs/project-map update.
- **Next / externally blocked:** live Render settings/log and public HTTPS checks
  need the service URL/configuration; live PostgreSQL needs TEST_DATABASE_URL.
- **Limitation:** free Render storage is ephemeral; process-only restart evidence
  with the same SQLite file does not establish persistent hosting storage.

Verification: `docs/render-sqlite-startup.md`. Prepared for deployment; no push.

## Render registration follow-up — 2026-11-04

- **Completed:** safe SQLite failure categories, logger survival through Alembic,
  shared-engine identity/schema snapshots after migrations and at FastAPI startup,
  existing-file diagnostic CLI, foreign-key/now()/RETURNING startup checks.
- **Completed:** fresh production registration/restart and isolated missing-table
  regressions for request_limits/users/profiles/refresh_tokens; redaction checks,
  independent self-review, pytest/Ruff/mypy and local production smoke validation.
- **Next / needs external evidence:** collect the live deploy SHA, actual Start
  Command, both startup snapshots and matching classified registration error.
  Exact current Render causation is not established by generic OperationalError;
  the existing launcher succeeds locally. Do not reset/stamp/delete the live DB.

Evidence and safe procedure: `docs/render-sqlite-registration-diagnostics.md`.

## Render registration Origin 403 — 2026-11-04

- **Completed:** public registration/preflight matrix proves Render HTTPS Origin
  missing from effective allowlist, Netlify Origin allowed; auth guard is the
  exact 403 source before limiter/service/database writes.
- **Completed:** both origins in production template, bounded rejection header
  diagnostics, nine production-origin regressions and expanded HTTP smoke;
  independent self-review and documentation/project-map update.
- **Next / external configuration:** apply the documented CORS_ORIGIN in Render
  and restart; no dashboard access or push/deployment in this task. Recheck public
  registration after configuration. Netlify API proxy still returns 404.
- Evidence and verification: `docs/render-registration-origin-403.md`.

## Render HTTPS Origin follow-up — 2026-11-05

- **Completed:** ASGI HTTP vs browser HTTPS mismatch reproduced; validated
  Render-provided RENDER_EXTERNAL_URL now joins the shared CORS/auth allowlist.
  Netlify remains an explicitly configured CORS_ORIGIN. No proxy-trust expansion.
- **Completed:** regressions for both origins, register/login/refresh, rejected
  origins, real Uvicorn proxy middleware, malformed forwarding headers and
  launcher overriding Render's FORWARDED_ALLOW_IPS=* default; self-review.
- **Next / external:** deploy the local commit, verify Render Start Command and
  environment, then test the actual HTTPS UI. No push/deploy performed here.
- Verification: `docs/render-https-origin-403.md`. SQLite config is unchanged.


## Vocabulary flashcards — 2026-11-10

Vocabulary backend completed: categories, saved sets up to 10, owner completion and test handoff. Frontend integration and Roma testing/XP remain next; shared A0 course support deferred. See docs/vocabulary-flashcards-api.md.


## A0–B2 curriculum — 2026-11-10

Completed: A0 backend + existing-filter button; 50-lesson A0–B2 draft and read-only validation/explicit import. Earlier A0 deferral is resolved. Next: editorial review, audio/production-skill coverage and separately approved release. Draft is not a CEFR certification syllabus; no production seed or publication performed.

## Curriculum verification pipeline — 2026-11-11

- **Completed:** offline validator, real grader probes, per-word review statuses,
  provenance-aware local Wiktextract/Tatoeba adapters, JSON/Markdown reports,
  separate SHA-guarded normalization copies, opt-in bounded AI review, offline tests.
- **Completed:** audit of five drafts (50 lessons / 500 words / 400 exercises).
  Structural success does not mean linguistic verification or publication approval.
- **Needs external evidence:** reviewed source exports and record licensing;
  current run attests/verifies zero words externally. No paid AI or DB writes.
- **Next:** teacher/translator review of all lessons/words and flagged conditional
  items, source-cache enrichment, sense/POS/morphology and productive-skill coverage,
  then separately approved exact-SHA release. No commit/push per user instruction.

## Curriculum visual review — 2026-11-11

- **Completed:** isolated private SQLite preparation through existing draft import;
  reviewer-only loopback preview using existing Courses/Course/Lessons pages;
  ordinary API continues to hide drafts and published flags remain false.
- **Completed:** all five courses / 50 lessons / 500 words / 400 exercises checked
  over HTTP; Firefox desktop/mobile pass, 122 checks and 16 screenshots; full
  pytest 375 passed/15 skipped, final targeted preview 13 passed, DOM 7 passed.
- **Completed:** launch/cleanup instructions and security self-review. No frontend
  redesign, grader/XP change, production write, commit or push.
- **Next:** teacher/translator editorial review and separate release approval.
  Existing UX: Vocabulary tab is personal words, initial tab is Test, floating
  AI launcher can overlap mobile text. See docs/curriculum-visual-review.md.
## Windows command fix — 2026-11-11

- **Completed:** replaced POSIX-only virtualenv paths in npm backend/database
  commands with `scripts/backend.mjs`. Windows selects `Scripts/python.exe`.
- **Completed 2026-11-14:** Windows npm preparation and seed on the copied database.


## PWA — 2026-11-13

Виконано: `/install.html`, маніфест, іконки, спільний `js/pwa.js` на всіх
онлайн-сторінках, захоплення браузерного встановлення, ручні інструкції для
Windows/Linux/Android/iPhone та `sw.js` із публічним offline-екраном.
Дані й автентифікація йдуть до чинного FastAPI; API та сторінки користувача
не кешуються. Навігація: мережа → при мережевому збої `/offline.html`.
Далі: розгорнути оновлення на HTTPS-сервері та перевірити системне встановлення
на фізичних пристроях. Нативні інсталятори не створено.
Деталі: `docs/pwa-installation.md` (від кореня проєкту).

### Database persistence checkpoint — 2026-11-14

Completed locally: populated SQLite audit, backup tooling, draft-preview npm workflow,
Alembic-based database preservation checks and required SQLite/PostgreSQL CI definition.
Production recommendation: managed PostgreSQL; no URL or production content changed.
Next: PostgreSQL CI evidence, staging typed-transfer rehearsal and restore drill.
External pending: branch protection and Render After CI Checks Pass configuration.
See `docs/05-database/persistence-and-recovery.md` and
`docs/09-deployment/database-ci-gate.md`. Final commit and ordinary push separately
authorized after verification; production migration/publication remain separate.

## Git integration ? 2026-11-14

Combined desktop/PWA and database persistence work, preserving both sets of
npm commands and ignore rules. Database commands use the cross-platform backend
runner; persistence test counts include the new present-perfect lesson. Backup
permission-bit checks apply on POSIX; Windows backup protection uses inherited ACLs.
