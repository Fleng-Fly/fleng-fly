# Backend completion report — 2026-10-18

## Architecture audit

Existing FastAPI modular monolith, SQLAlchemy 2 async/asyncpg, Alembic, Pydantic,
argon2/JWT authentication and static HTML/CSS/JS serving are preserved. Router,
service and schema conventions are reused. Git history and existing docs/models/
tests were inspected before implementation. The incoming working tree already
contained catalog/exercise/progress/frontend changes and an untracked exercise
migration/module/tests; these remain intact. No commits or pushes were created.

The original four migrations form one chain. Docker/psql/pg_isready are absent;
PostgreSQL refuses localhost:5432 connections on both IPv4 and IPv6. Actual
`alembic upgrade head` failed before applying migrations. No data was destroyed
or application database replaced with SQLite.

## Implemented functionality

- Personal vocabulary with translation/example, optional published lesson,
  learned/review state, due flashcards, ownership and review history.
- Server-timezone calendar activity, current/longest streak and duplicate protection.
- Migration-owned deterministic achievement definitions/once-only awards.
- Own profile display-name/CEFR/language updates with validation.
- Hashed, cryptographically random, expiring, one-use reset tokens; IP/email limits,
  configurable SMTP delivery, generic responses and refresh-session revocation.
- Async OpenRouter transport, configurable model, sanitized provider errors,
  timeout/output limits and opt-in JSON Schema support.
- Level/language/lesson-aware tutor with optional grammar correction, persisted
  complete conversation turns, ownership/history/deletion and bounded context.
- Grammar explanation and Pydantic-validated practice exercise generation without
  official XP or grading authority.
- Deterministic recommendations that work while AI is disabled or unavailable.
- Incremental SSE, incomplete-stream rejection, immediate generator closing on
  disconnect, and non-streaming fallback.
- Persistent per-user rate/day/token reservations and global/per-user concurrency,
  bounded API bodies, usage accounting and validation input redaction.

## Added/modified files

Added:

- `backend/app/modules/ai/{__init__,router,schemas,service,provider,prompts,context}.py`
- `backend/app/modules/vocabulary/{__init__,router,schemas,service}.py`
- `backend/app/modules/gamification/{__init__,router,schemas,service}.py`
- `backend/app/modules/password_reset/{__init__,router,schemas,service}.py`
- `backend/app/core/{body_limit,limits}.py`
- `backend/alembic/versions/20261018_1200_learning_ai.py`
- `backend/tests/test_ai.py`, `test_ai_provider.py`, `test_learning_extensions.py`,
  `test_postgres_migrations.py`
- `scripts/check-db.py` and this report.

Extended existing files:

- `backend/app/db/models.py`, `seed.py`, `api/router.py`, `main.py`,
  `core/config.py`, `core/errors.py`, users router/schemas/service,
  and the incoming exercises service (learner locking/activity hooks).
- `backend/pyproject.toml` (httpx runtime), `alembic/env.py` (safe URL interpolation
  and injected connection for isolated migration tests), `tests/conftest.py`
  (opt-in PostgreSQL fixtures), root `.env.example`, `docker-compose.yml`.
- README, `ai/README.md`, docs AI/backend/API/database/development/security/testing/
  architecture, plans AI/backend/database/testing/roadmap/milestones, and project
  map modules/API/data-flow/architecture/dependencies.

No frontend design or CSS changes were made by this implementation. Existing
uncommitted frontend files and CSS.star4life assets were preserved.

## Database migrations

New additive revision **20261018_1200**, down revision **20261011_1400**:

- Adds profile CEFR/language defaults.
- Adds vocabulary_items, vocabulary_reviews, learning_activity, achievements,
  user_achievements, password_resets, request_limits, ai_conversations, ai_messages,
  ai_usage with foreign keys/indexes/uniqueness/role checks.
- Inserts five deterministic achievement definitions.
- Leaves existing users/catalog/progress data intact; does not invent past activity.

One Alembic head; full PostgreSQL offline upgrade SQL compiles. Live migration and
ORM drift validation remain unverified because PostgreSQL is unavailable.

## New API surface

All under `/api/v1`:

- `PATCH /users/me`
- `GET|POST /vocabulary`, `PATCH|DELETE /vocabulary/{id}`
- `POST /vocabulary/{id}/review`, `GET /vocabulary/{id}/reviews`
- `GET /streaks/me`, `GET /achievements/me`
- Public rate-limited `POST /auth/password-reset/request|confirm`
- `POST /ai/chat`, `POST /ai/chat/stream`
- `GET /ai/conversations`, `GET|DELETE /ai/conversations/{id}`
- `POST /ai/explain`, `POST /ai/generate-exercise`, `GET /ai/recommendations`

Except reset request/confirm, all new routes require Bearer authentication.
Request/response examples: [api.md](api.md), [ai.md](ai.md).

## Environment

For runtime PostgreSQL use DATABASE_URL. Production also requires a real
JWT_ACCESS_SECRET. To enable paid AI configure AI_ENABLED=true,
OPENROUTER_API_KEY, OPENROUTER_MODEL; OPENROUTER_BASE_URL defaults to
https://openrouter.ai/api/v1. AI_MAX_OUTPUT_TOKENS=800 and AI_REQUEST_TIMEOUT=30
are defaults. Other rate/budget/history/concurrency controls are fully listed in
[ai.md](ai.md) and `.env.example`.

LEARNING_TIMEZONE defaults UTC. SMTP delivery requires RESET_DELIVERY=smtp,
SMTP_HOST/PORT/FROM and credentials/TLS as appropriate, plus a trusted RESET_URL.
Reset delivery is disabled by default. TEST_DATABASE_URL is optional for running
isolated real PostgreSQL tests; never use a production database for testing.

## Verification and self-review

- **121 passed, 1 skipped**, no paid AI requests. The skipped test requires PostgreSQL.
- Original 64 regression tests passed; 57 new tests cover the implemented modules.
- Ruff passes; mypy passes for 62 app files; `git diff --check` passes.
- Alembic heads/history and complete offline PostgreSQL SQL generation succeed.
- Actual PostgreSQL connection and Alembic upgrade fail with connection refused.
- One existing Starlette/httpx TestClient deprecation warning remains.

Independent self-review checked auth/ownership, trust roles, data flow, concurrency,
transaction atomicity, cancellation, bounds, secret exposure, schema validation,
existing regression behavior and docs. Fixed timezone-aware bulk comparisons,
stale XP updates via learner serialization, complete-turn atomicity, structured
schema strictness, explicit stream closure, and validation input reflection.

## Remaining limits and launch

Real PostgreSQL migration/auth/lesson/XP/progress integration and live OpenRouter
verification are blocked by infrastructure/credentials. Both have reproducible
manual/automated instructions. SMTP delivery was tested through injection, not a
real mail server. Password-reset UI and new feature UI wiring are outside this
backend implementation. Existing access JWTs survive reset until normal short
expiry. Reviews use a basic 1/7-day policy; mistake analytics use latest exercise
submissions grouped by lesson. Generated content is schema-validated practice,
not guaranteed pedagogically correct. Token reservations are basic cost guards;
set an OpenRouter key credit limit for currency protection.

From repository root, keep any existing `.env`; configure it from `.env.example`
only if absent, then:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e './backend[dev]'
docker compose up -d --wait db
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python ../scripts/check-db.py
.venv/bin/python -m app.db.seed
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload
```

Open http://localhost:3001 and http://localhost:3001/docs. Without Docker, follow
the native PostgreSQL role/database setup in [development.md](development.md),
then run the same migrate/check/seed/server commands. Never delete a database
volume or stamp migrations to work around connectivity. Seed refuses production.
