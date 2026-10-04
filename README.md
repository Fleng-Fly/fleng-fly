# Fleng

Fleng is a web platform for learning English: structured courses, interactive
exercises, spaced-repetition vocabulary, speaking/listening/reading/writing
practice, gamified progress, and an AI tutor.

This repository is in its **foundation stage**. The current commit establishes
the engineering groundwork — structure, architecture, documentation, plans and
design language. Application code is intentionally not implemented yet.

## Vision

Make serious English practice feel premium and focused: a dark, calm interface;
short daily sessions; measurable progress; and an AI tutor that explains, corrects
and adapts to the learner instead of replacing them.

## Features (target scope)

- **Auth & accounts** — email/password, sessions, profiles, settings.
- **Learning** — courses → lessons → exercises, with grammar, reading, listening,
  writing and speaking practice.
- **Vocabulary** — word lists, personal vocabulary, flashcards and review scheduling.
- **Progress** — per-skill tracking, streaks, XP, levels, achievements.
- **Challenges** — time-boxed goals and leaderboards.
- **AI Tutor** — grammar explanations, writing correction, conversation practice,
  speaking feedback and personalised recommendations.
- **Platform** — subscriptions, notifications, analytics.

See `plans/roadmap.md` for a realistic, staged rollout and
`plans/milestones.md` for current status.

## Architecture

Fleng is a **modular monolith**, not microservices.

```
User
 ↓
Frontend (Next.js)          ← presentational + client state
 ↓  HTTPS / JSON
Backend (NestJS, modular)   ← auth, learning, progress, vocabulary,
 ↓                            challenges, gamification, AI, notifications
PostgreSQL (Prisma)
 ↑
AI layer (@fleng/ai)         ← provider-agnostic; consumed by backend, not public
```

- One backend deployable exposes a versioned REST API under `/api`.
- Modules talk through explicit service interfaces, never by reaching into each
  other's repositories.
- The AI layer is a library, not a service: it is easy to extract later, but a
  network hop is not justified yet.

Full details: `docs/architecture.md` and `project-map/architecture.md`.

## Repository structure

```
/
├── frontend/     # Next.js user interface
├── backend/      # NestJS API (modular monolith)
├── ai/           # @fleng/ai provider-agnostic AI layer
├── docs/         # architecture and engineering documentation
├── plans/        # roadmap, per-area plans, milestones
├── design/       # design system, colors, typography, UX flows
├── project-map/  # living map of modules, data flow and API
├── AGENTS.md     # rules for agents and contributors
└── README.md
```

## Technology stack

| Area       | Choice                                             |
| ---------- | -------------------------------------------------- |
| Language   | TypeScript (everywhere)                            |
| Monorepo   | pnpm workspaces                                    |
| Frontend   | Next.js (App Router), React, Tailwind CSS, Framer Motion |
| Backend    | NestJS, Prisma ORM                                 |
| Database   | PostgreSQL                                         |
| Auth       | JWT access token + rotating refresh token, argon2id |
| AI         | `@fleng/ai` provider abstraction (OpenAI/Anthropic/…) |
| Tests      | Vitest, Supertest, Playwright                      |
| Tooling    | ESLint, Prettier, Docker                           |

Rationale and alternatives: `docs/development.md`.

## Development setup

> Not runnable yet — no package manifests exist. This section describes the
> intended workflow and will be validated when the first modules land.

```bash
git clone <repo>
cd fleng
pnpm install
cp .env.example .env        # fill in secrets locally; never commit .env
pnpm db:migrate             # Prisma
pnpm dev                    # frontend + backend
```

Full setup, environment variables and conventions live in
`docs/development.md`.

## Roadmap

High level (details in `plans/roadmap.md`):

1. **Foundation** — structure, docs, project map, design system. *(current)*
2. **Backend core** — database, auth, users, validation, error handling.
3. **Learning MVP** — courses, lessons, exercises, progress.
4. **Vocabulary & gamification** — flashcards, streaks, XP, achievements.
5. **Frontend MVP** — app shell and core screens consuming the API.
6. **AI tutor** — provider abstraction, explanations, writing feedback.
7. **Polish & launch** — speaking practice, notifications, analytics, billing.

## Current status

Foundation. No application code, no runtime dependencies, no secrets.
See `plans/milestones.md` for the live status board.

## Contributing

Read `AGENTS.md` first. Work in small logical commits, keep `docs/`,
`project-map/` and `plans/` in sync with the code, and perform an independent
self-review before declaring anything done.
