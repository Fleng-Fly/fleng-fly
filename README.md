# Fleng

Fleng is an English-learning web platform with structured courses, graded
exercises, personal vocabulary, learning progress and an AI tutor API.

The project is a **learning MVP with stabilized backend extensions**. One
Python/FastAPI application serves both the REST API and a plain HTML/CSS/vanilla
JavaScript frontend. SQLite is the local default; PostgreSQL is supported as an
explicit alternative.

## Quick start

Requires **Python 3.11+** with venv and **Node.js 20+** for development scripts.
A separate database server is not needed locally.

```bash
npm run dev
```

The launcher creates the backend virtualenv and installs dependencies if absent,
applies pending SQLite migrations, seeds an empty catalog and starts the server.

- Application: <http://localhost:3001>
- API documentation: <http://localhost:3001/docs>
- Health check: <http://localhost:3001/api/v1/health>

The local database is `backend/data/fleng.db` and is excluded from Git. Restarts
preserve accounts, sessions and progress. Relative SQLite paths resolve against
`backend/`, independently of the shell's working directory.

Optional database commands:

```bash
npm run db:migrate       # apply migrations
npm run db:seed          # update demo catalog in place, without duplicate records
```

For the presentation walkthrough and fictional accounts, see [DEMO.md](DEMO.md).
`./start.sh` prepares and checks the demo using the existing application.

## Implemented functionality

| Area | Current behavior |
| --- | --- |
| Authentication | Register/login/logout, access JWTs, rotating HttpOnly refresh cookies, strict reuse detection |
| Account settings | Own name/email/language/CEFR updates, password change and password reset API |
| Catalog | Published courses, lessons, theory and public exercise descriptions |
| Graded lessons | Start/resume, server-side submissions, single-choice/text/self-check exercises |
| Progress | Once-only exercise XP, lesson completion and per-course progress |
| Vocabulary | Personal words, translations/examples, lesson links, due queue and review history |
| Gamification | Daily activity, current/longest streak and deterministic achievements |
| AI backend | OpenRouter chat/history, explanations, generated practice, SSE and usage limits |
| Recommendations | Deterministic learning suggestions that work without an AI provider |

The frontend connects login/register, Dashboard, courses, Lessons and Settings to
the API. Lessons can save vocabulary; Dashboard displays progress, streaks and
learned-word metrics. Dedicated Vocabulary, Practice, Challenges, Progress and AI
Tutor screens remain future work.

Reviews currently use a basic **1-day retry / 7-day remembered** schedule.
Automatic numeric level progression, adaptive SRS, billing, notifications and
leaderboards are not implemented.

## Architecture and stack

```text
Browser: HTML / CSS / JavaScript ES modules
    │ same-origin fetch
    ▼
FastAPI: static frontend + /api/v1 REST API
    │ SQLAlchemy 2 async
    ▼
SQLite + aiosqlite locally / PostgreSQL + asyncpg optionally
```

- Modular monolith with feature routers, services and Pydantic schemas.
- Alembic manages database migrations.
- Argon2id hashes passwords; PyJWT signs access tokens.
- OpenRouter is called only by the backend; provider credentials stay server-side.
- No frontend framework, TypeScript, bundler or frontend build step.
- Node.js runs repository scripts; the backend is Python.

See [architecture](docs/architecture.md), [backend](docs/backend.md) and
[project map](project-map/modules.md).

```text
frontend/       Static pages, CSS and browser JavaScript
backend/app/    FastAPI, feature modules, configuration and database models
backend/alembic/ Database migrations
backend/tests/  Unit, API, database and concurrency tests
ai/             Documentation entry point for the backend AI integration
docs/           Engineering documentation and verification reports
project-map/    Modules, API and data flows
plans/          Roadmap, milestones and remaining work
scripts/        Development, database, demo and smoke-check tooling
design/         Visual language and UX documentation
```

## Configuration

Settings come from environment variables and optional ignored `.env` files in
the repository root or `backend/`. Use [.env.example](.env.example) as a reference;
preserve any existing configuration and keep real credentials out of Git.

- SQLite works with the development defaults.
- For PostgreSQL, set `DATABASE_URL=postgresql://...` and run migrations explicitly.
  Automatic database preparation is disabled for PostgreSQL and production.
- Production requires a real `JWT_ACCESS_SECRET`.
- AI is disabled by default. Enable it with `AI_ENABLED=true`,
  `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`.
- Reset-email delivery is disabled by default. Configure `RESET_DELIVERY=smtp`
  and SMTP settings to send reset links.

Detailed setup: [development](docs/development.md), [authentication](docs/authentication.md)
and [AI](docs/ai.md).

## Authentication stability

Refresh rotation uses an atomic conditional database update. Revocation of the
old token, successor creation and linking commit together. A replay revokes all
refresh sessions for that user, including a concurrently issued successor.

Password change and reset atomically revoke all refresh sessions and unused
reset tokens. Settings directs the user to sign in again. **Existing access JWTs
remain valid until their configured expiry, default 15 minutes.**

Argon2 work runs outside the event loop with at most four password workers per
event loop. Persistent request limits apply before expensive authentication work:

| Setting | Default |
| --- | --- |
| `AUTH_LOGIN_IP_PER_MINUTE` | 20 attempts per peer IP/minute |
| `AUTH_LOGIN_EMAIL_PER_MINUTE` | 10 attempts per normalized email/minute |
| `AUTH_REGISTER_IP_PER_HOUR` | 10 attempts per peer IP/hour |

Exceeded quotas return `429 RATE_LIMITED` with a window-aligned `Retry-After`.
Local launch commands disable proxy headers. Production reverse proxies require
an explicit trusted-proxy configuration; see [authentication](docs/authentication.md).
The existing duplicate-registration `409 EMAIL_TAKEN` response is preserved.

## Checks

From the repository root:

```bash
npm run backend:test        # pytest
npm run backend:lint        # Ruff
npm run backend:typecheck   # mypy
python3 scripts/backend-stabilization-smoke.py
```

The smoke runner starts `npm run dev` on a temporary port with a temporary SQLite
file. It checks authentication, Dashboard/Lessons APIs, once-only XP and account/
progress persistence after restart. It does not use `backend/data/fleng.db`.

Stabilization verification on **2026-10-28**:

- **VERIFIED:** 156 tests passed; Ruff, mypy and `git diff --check` passed.
- **VERIFIED:** temporary SQLite migrations, concurrency, rollback and dev-server
  smoke checks, including restart persistence.
- **PARTIALLY VERIFIED:** PostgreSQL compatibility; Alembic has one head and its
  PostgreSQL migration SQL compiles offline.
- **NOT VERIFIED:** live PostgreSQL, real SMTP/OpenRouter and production proxy
  deployment. Fifteen PostgreSQL tests skip without `TEST_DATABASE_URL`.

An existing Starlette/httpx deprecation warning remains. In the restricted
execution sandbox, even a minimal aiosqlite query hung; the same query and full
suite completed outside it. See [testing](docs/testing.md) for the diagnosis and
[stabilization report](docs/backend-stabilization-report.md) for evidence,
changed files and remaining risks. These results do not claim production load
or live PostgreSQL integration coverage.

## Contributing

Read [AGENTS.md](AGENTS.md) before making changes. Preserve the existing stack,
work in logical commits, run relevant checks and perform an independent review.
Keep `docs/`, `project-map/` and `plans/` aligned with the implementation.
See [milestones](plans/milestones.md) and [roadmap](plans/roadmap.md) for next steps.
