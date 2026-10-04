# Fleng

Fleng is a web platform for learning English: structured courses, interactive
exercises, spaced-repetition vocabulary, practice, gamified progress, and an AI
tutor.

This repository currently contains the **M1 vertical slice**: a real Next.js
frontend talking to a real **Python / FastAPI** backend, backed by PostgreSQL via
SQLAlchemy and Alembic. It is an engineering foundation, not a finished product —
authentication, the learning catalog and AI are not implemented yet.

## What works today

- `pnpm install` + `pnpm setup` + `pnpm dev` starts the frontend (3000) and backend (3001).
- `GET /api/v1/health` returns service + database status.
- The landing page calls the API and shows a live **Backend ● Online / Offline**
  indicator.
- `GET /api/v1/users/me` returns a learner profile from PostgreSQL (through a
  development-only auth stub; see `docs/backend.md`).
- `/learn` shows the learner's level/XP from the API; `/login` is a UI scaffold
  (no auth yet).

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
   ↓
Next.js frontend (App Router)          frontend/            (TypeScript)
   ↓  fetch via typed API client        frontend/src/lib/api
REST API  /api/v1                      backend/             (Python)
   ↓
FastAPI app (health, users)            backend/app
   ↓  SQLAlchemy 2 (async) + asyncpg
PostgreSQL                             docker-compose.yml
```

- One frontend deployable and one backend deployable.
- The backend owns all data decisions; the frontend contains no business rules.
- The AI layer (`ai/`) will be a Python library consumed by the backend, not a
  separate service.

Details: `docs/architecture.md` and `project-map/architecture.md`.

## Repository structure

```
/
├── frontend/          # @fleng/frontend — Next.js (App Router)
│   └── src/
│       ├── app/       # routes: /, /learn, /login
│       ├── components/# app shell, status, UI primitives
│       ├── config/    # navigation
│       └── lib/api/   # typed API client + endpoints
├── backend/           # FastAPI API (Python)
│   ├── app/
│   │   ├── core/      # config, error handlers, shared schemas
│   │   ├── db/        # SQLAlchemy base, models, session
│   │   ├── api/       # aggregate router + dependencies
│   │   └── modules/   # health/, users/
│   ├── alembic/       # migrations
│   ├── tests/         # pytest
│   └── pyproject.toml
├── ai/                # future Python AI layer (docs only)
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

| Area       | Choice                                                              |
| ---------- | ------------------------------------------------------------------- |
| Frontend   | Next.js (App Router), React, Tailwind CSS v4, TanStack Query, Framer Motion |
| Backend    | Python 3.11+, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic       |
| Database   | PostgreSQL (asyncpg driver)                                         |
| Frontend tests | Vitest                                                          |
| Backend tests  | pytest                                                          |
| Backend lint/type | Ruff (lint + format), mypy                                  |
| Tooling    | pnpm workspace (frontend), Python virtualenv (backend), Docker (database only) |

Rationale and deliberate omissions: `docs/development.md`.

## Getting started

Prerequisites: Node.js >= 20, pnpm >= 9, Python >= 3.11, and either Docker or a
local PostgreSQL.

```bash
pnpm install          # install frontend dependencies
pnpm setup            # create backend/.venv and install Python dependencies

docker compose up -d db   # start PostgreSQL (or set DATABASE_URL)
cp .env.example .env      # optional; sensible development defaults exist
pnpm db:migrate           # apply Alembic migrations

pnpm dev              # frontend :3000, backend :3001
```

Then open http://localhost:3000. The backend is at http://localhost:3001, with
all routes under `/api/v1`.

> `pnpm dev` starts even without PostgreSQL: `/api/v1/health` reports
> `database: "down"`, and `/api/v1/users/me` returns `503`. `DATABASE_URL` is
> required in production.

## Scripts

| Script                 | Effect |
| ---------------------- | ------ |
| `pnpm setup`           | Create the backend venv and install Python dependencies |
| `pnpm dev`             | Run frontend + backend (auto-runs setup if needed) |
| `pnpm build`           | Build the frontend |
| `pnpm lint`            | ESLint (frontend) + Ruff (backend) |
| `pnpm typecheck`       | `tsc` (frontend) + mypy (backend) |
| `pnpm test`            | Vitest (frontend) + pytest (backend) |
| `pnpm format`          | Prettier (frontend) + Ruff format (backend) |
| `pnpm db:migrate`      | Apply Alembic migrations |
| `pnpm db:sql`          | Emit migration SQL without a database |

## Roadmap

High level (details in `plans/roadmap.md`):

1. **Foundation** — structure, docs, project map, design system. *(done)*
2. **M1 — Frontend + FastAPI backend** — workspace, health/users API, database. *(current)*
3. **Authentication** — real register/login/refresh/logout, replacing the dev stub.
4. **Learning MVP** — courses, lessons, exercises, progress.
5. **Vocabulary & gamification** — flashcards, streaks, XP, achievements.
6. **Frontend MVP** — full app shell and screens.
7. **AI tutor** — Python AI layer, explanations, writing feedback.
8. **Polish & launch** — speaking practice, notifications, analytics, billing.

## Current status

M1. `pnpm lint`, `pnpm typecheck`, `pnpm test` and `pnpm build` all pass. See
`plans/milestones.md` for the live status board and known limitations.

## Contributing

Read `AGENTS.md` first. Work in small logical commits, keep `docs/`,
`project-map/` and `plans/` in sync with the code, and perform an independent
self-review before declaring anything done.
