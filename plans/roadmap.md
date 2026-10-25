# Roadmap

> Status: **active**. Update after every stage. Current status board:
> `plans/milestones.md`.

Current frontend phase (2026-10-22): Dashboard and Lessons have been implemented
on the existing static frontend and SQLite local workflow. Lessons now has a
shared workspace, Theory/Practice/Test/Vocabulary tabs, real grading and
resume, and responsive layouts. Exact Figma comparison awaits the target
screen reference; Login/Sign Up is the next requested UI phase. The historical
stage descriptions below record earlier architecture decisions.

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
