# Fleng

Fleng is a web platform for learning English: structured courses, interactive
exercises, spaced-repetition vocabulary, practice, gamified progress, and an AI
tutor.

This repository currently contains an **M2 authentication vertical slice**: a
plain HTML/CSS/JavaScript frontend served by a **Python / FastAPI** backend,
backed by local SQLite (or PostgreSQL via `DATABASE_URL`) through SQLAlchemy and
Alembic. Email/password authentication,
user profiles, the course/lesson catalog and a graded learning flow
(exercises, submissions, XP and progress) are implemented. Backend vocabulary,
streaks, achievements, profile updates, password reset and OpenRouter tutoring
APIs are also implemented. Live PostgreSQL/AI integration verification remains
blocked in this execution environment; see `docs/development.md` and `docs/ai.md`.

## What works today

- `npm run dev` prepares local SQLite and starts a single FastAPI server on port
  3001 that serves both the API and the static frontend.
- The landing page (`/`) calls the API and shows a live **Backend ● Online /
  Offline** indicator.
- **Authentication**: `POST /api/v1/auth/register`, `/login`, `/refresh` and
  `/logout` — argon2id hashing, short-lived access JWTs and rotating refresh
  tokens in an HttpOnly cookie (with reuse detection).
- `GET /api/v1/users/me` returns the authenticated learner's profile; `GET
/api/v1/progress/me` returns their progress. Both require a Bearer token.
- `login.html` and `register.html` create a real session; `dashboard.html` shows
  the signed-in learner's name, level, XP and progress from the API;
  `settings.html` manages account details, language preference and password. These pages redirect to login when there is
  no session.
- **Catalog**: `GET /api/v1/courses` lists published courses,
  `GET /api/v1/courses/{slug}` returns a course with its published lessons and
  `GET /api/v1/lessons/{slug}` returns a lesson's theory plus public exercises
  (never the answer keys). `courses.html`, `course.html` and `lesson.html`
  render them; demo content is loaded with the idempotent seed (`pnpm db:seed`).
- **Graded lessons**: `POST /api/v1/lessons/{slug}/start|submit` and
  `GET /api/v1/lessons/{slug}/progress`. Exercises come in three types
  (`single_choice`, `text`, `self_check`), answers are graded server-side, and
  the correct answer / model answer is revealed only after submission. XP is
  awarded once per exercise; `GET /api/v1/progress/me` returns the aggregate,
  `exercisesCompleted`, `xp` and per-course progress. The lesson page and the
  dashboard show this persisted data.

## Vision

Make serious English practice feel premium and focused: a dark, calm interface;
short daily sessions; measurable progress; and an AI tutor that explains,
corrects and adapts to the learner instead of replacing them.

## Features (target scope)

- **Auth & accounts** — email/password, sessions, profiles, settings.
- **Learning** — courses → lessons → exercises, with grammar, reading, listening,
  writing and speaking practice.
- **Vocabulary** — word lists, personal vocabulary, flashcards, review scheduling.
- **Progress** — per-skill tracking, streaks, XP, levels, achievements.
- **Challenges** — time-boxed goals and leaderboards.
- **AI Tutor** — grammar explanations, writing correction, conversation practice,
  speaking feedback, personalised recommendations.
- **Platform** — subscriptions, notifications, analytics.

See `plans/roadmap.md` for the staged rollout and `plans/milestones.md` for the
current status board.

## Architecture

Fleng is a **modular monolith** — not microservices.

```
Browser
   ↓  HTTPS
FastAPI (Python)  — one deployable on :3001
   ├── serves the static frontend (frontend/: HTML, CSS, vanilla JS) at /
   ├── serves the REST API at /api/v1
   ↓  SQLAlchemy 2 (async) + aiosqlite / asyncpg
SQLite locally / PostgreSQL via DATABASE_URL
```

- One backend deployable serves both the API and the static frontend, so the
  HttpOnly refresh cookie is first-party and no CORS is needed in the browser.
- **FastAPI is the only backend framework.** The frontend is plain HTML/CSS/JS
  with no framework and no build step; there is no TypeScript anywhere.
- The backend owns all data decisions; the frontend contains no business rules.
- AI lives in `backend/app/modules/ai/` inside the monolith; `ai/` is its
  documentation entry point. OpenRouter credentials remain server-only.

Details: `docs/architecture.md` and `project-map/architecture.md`.

## Repository structure

```
/
├── frontend/          # static HTML/CSS/JS UI (served by FastAPI; no build step)
│   ├── *.html
│   ├── css/app.css
│   └── js/            # api.js, session.js, layout.js, page scripts
├── backend/           # FastAPI API (Python) + static file serving
│   ├── app/
│   │   ├── core/      # config, error handlers, shared schemas
│   │   ├── db/        # SQLAlchemy base, models, session
│   │   ├── api/       # aggregate router + dependencies
│   │   ├── modules/   # health/, auth/, users/, progress/
│   │   └── main.py    # app factory + StaticFiles mount
│   ├── alembic/       # migrations
│   ├── tests/         # pytest
│   └── pyproject.toml
├── ai/                # AI documentation entry point
├── docs/              # architecture and engineering docs
├── plans/             # roadmap, per-area plans, milestones
├── design/            # design system and UX docs
├── project-map/       # living map of modules, flows and API
├── scripts/           # dev orchestration + backend setup
├── docker-compose.yml # local PostgreSQL
├── AGENTS.md          # rules for agents and contributors
└── README.md
```

## Technology stack

| Area              | Choice                                                              |
| ----------------- | ------------------------------------------------------------------- |
| Frontend          | Plain HTML5, CSS3 and vanilla JavaScript (ES modules, `fetch`)      |
| Static serving    | FastAPI `StaticFiles` (same origin as the API)                      |
| Backend           | Python 3.11+, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic      |
| Database          | SQLite locally (aiosqlite); optional PostgreSQL (asyncpg)           |
| Backend tests     | pytest                                                              |
| Backend lint/type | Ruff (lint + format), mypy                                          |
| Tooling           | Python virtualenv (backend), Docker (database only), Node (scripts) |

Rationale and deliberate omissions: `docs/development.md`.

## Getting started

For the presentation setup, fictional accounts and walkthrough, see [DEMO.md](DEMO.md).
Run `./start.sh` to prepare local data, start the app if needed, and check
the landing page, database, catalog and demo-account progress.

Prerequisites: Node.js >= 20 and Python >= 3.11 with venv. No database server is
needed for local development.

```bash
npm run dev              # prepares SQLite, then starts FastAPI and the frontend
# If backend/.venv is absent, the existing setup installs Python dependencies.
# Optional explicit database commands:
npm run db:migrate
npm run db:seed
```

Then open http://localhost:3001. The UI is served at `/`; all API routes live
under http://localhost:3001/api/v1.

The default file is `backend/data/fleng.db`, excluded from Git. Relative SQLite
paths always resolve against `backend/`, regardless of the working directory.
Startup applies pending Alembic upgrades and loads the demo catalog only if no
courses exist. Repeated starts preserve users, sessions and progress. Explicit
`db:seed` updates demo content in place without duplicate records.

PostgreSQL remains supported: set `DATABASE_URL=postgresql://...` in the ignored
root `.env` or environment, then apply migrations explicitly. Automatic preparation
is disabled for PostgreSQL and production. Never replace an existing `.env` blindly.

## Scripts

| Script               | Effect                                                  |
| -------------------- | ------------------------------------------------------- |
| `pnpm setup`         | Create the backend venv and install Python dependencies |
| `pnpm dev`           | Run FastAPI (serves the API and the static frontend)    |
| `pnpm lint`          | Ruff (backend)                                          |
| `pnpm typecheck`     | mypy (backend)                                          |
| `pnpm test`          | pytest (backend, incl. static-frontend serving)         |
| `pnpm format`        | Prettier (HTML/CSS/JS/Markdown) + Ruff format (backend) |
| `pnpm db:migrate`    | Apply Alembic migrations                                |
| `npm run db:prepare` | Prepare local SQLite (also called by dev)               |
| `pnpm db:seed`       | Insert/update the demo catalog (idempotent)             |
| `pnpm db:sql`        | Emit migration SQL without a database                   |

## Roadmap

High level (details in `plans/roadmap.md`):

1. **Foundation** — structure, docs, project map, design system. _(done)_
2. **M1 — Frontend + FastAPI backend** — health/users API, database. _(done)_
3. **M2 — Authentication & progress** — register/login/refresh/logout, `/users/me`, `/progress/me`. _(done)_
4. **Phase A — Static frontend** — plain HTML/CSS/JS served by FastAPI. _(done)_
5. **Learning MVP** — courses, lessons, exercises, grading and progress recording. _(done)_
6. **Vocabulary & gamification backend** — implemented; frontend integration remains.
7. **AI tutor backend** — implemented with OpenRouter; live verification pending.
8. **Polish & launch** — speaking practice, notifications, analytics, billing.

## Current status

M2 + Phase A + catalog + graded lesson flow. `pnpm lint`, `pnpm typecheck` and
`pnpm test` all pass (auth/progress, catalog, exercises and static-frontend
tests). See `plans/milestones.md` for the live status board and
`plans/david-work.md` for the storage/login/progress assignment.

## Contributing

Read `AGENTS.md` first. Work in small logical commits, keep `docs/`,
`project-map/` and `plans/` in sync with the code, and perform an independent
self-review before declaring anything done.
