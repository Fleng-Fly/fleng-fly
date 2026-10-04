# Roadmap

> Status: **active**. Update after every stage. Current status board:
> `plans/milestones.md`.

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

### Stage 1b — Backend core (in progress next)

Authentication (register/login/refresh/logout) and profiles, replacing the dev
auth stub; argon2id hashing; rate limiting; integration tests.

**Exit criteria:** auth and profile API tested end-to-end against a test DB;
security checklist applied to every endpoint.

### Stage 2 — Learning MVP

Courses, lessons, exercises, submissions, grading; lesson start/complete;
progress recording.

**Exit criteria:** the lesson flow works from the API with tests; progress is
queryable per course.

### Stage 3 — Vocabulary & gamification

Vocabulary words, user vocabulary, flashcards/SRS reviews; XP ledger, levels,
streaks, achievements.

**Exit criteria:** review flow updates scheduling; completing lessons updates
XP/streak/achievements idempotently.

### Stage 4 — Frontend MVP

Next.js app shell, auth screens, dashboard, learn/lessons, vocabulary, progress,
AI tutor; design system implemented; critical Playwright flows.

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
