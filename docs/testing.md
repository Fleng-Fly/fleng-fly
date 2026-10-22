# Testing

> Status: **auth + progress tested**. Backend auth/progress flows run against an
> in-memory SQLite database; the static frontend is served and asserted over the
> ASGI app. Integration tests against real PostgreSQL and browser e2e tests are
> planned. Rollout order: `plans/testing-plan.md`.

## 1. Principles

- Tests ship with the feature, not in a later phase.
- No real external network calls (AI providers, email) in tests.
- Tests are deterministic and do not require a running database unless they are
  explicitly integration tests.
- Test behaviour and contracts, not implementation details.

## 2. Tooling

| Level          | Tool                          | Scope | Status |
| -------------- | ----------------------------- | ----- | ------ |
| Backend unit/API | pytest + httpx ASGI client | routers, services, dependencies | ✅ |
| Database-backed API | pytest + in-memory SQLite | auth/users/progress flows, constraints | ✅ |
| Static frontend | pytest + httpx ASGI client | pages/assets served, same-origin API access | ✅ |
| Integration    | pytest + test PostgreSQL      | migrations, SQLAlchemy models/repositories | ⬜ |
| Browser e2e    | Playwright                    | critical user journeys | ⬜ |

Backend database tests override `get_db` with a SQLite engine (see
`backend/tests/conftest.py`), so the suite needs no PostgreSQL server. PostgreSQL
integration tests remain a separate, explicit task.

## 3. Current tests

Backend (`backend/tests/`):

- `test_health.py` — reports `database: up/down`, never fails the request.
- `test_auth.py` — register, duplicate email, argon2id hashing, login, wrong
  password, refresh rotation, reuse detection, logout, protected endpoints and
  cross-user isolation.
- `test_users.py` — `/users/me` is authenticated and read-only.
- `test_progress.py` — `/progress/me` requires auth and starts at zero.
- `test_catalog.py` — published-only listing, ordering, course detail, lesson
  theory, missing/unpublished 404s and seed idempotency.
- `test_exercises.py` — public exercises never leak answer keys; single-choice
  correct/incorrect/invalid; text normalisation and rejection; self-check
  requires a self-assessment and reveals the model answer; cross-lesson and
  unknown exercise `404`s; lesson completion rules; XP/completion idempotency;
  per-user isolation; backward-compatible `/progress/me`; seed idempotency.

Static frontend (`backend/tests/test_frontend.py`):

- pages (`/`, `/login.html`, `/dashboard.html`, `/courses.html`, `/course.html`,
  `/lesson.html`, `/settings.html`) and JS assets are served with the expected
  content types;
- `/api/v1/health` is reachable alongside the frontend on the same origin;
- `test_auth.py` additionally asserts same-origin requests are accepted and
  untrusted origins are rejected (CSRF origin check).

## 4. Critical flows

Covered now: register → login → refresh → logout; protected requests; a user
cannot read another user's data; catalog reads; start a lesson → answer
exercises → grading → lesson completion → progress/XP update (streaks are not
implemented yet). Still to cover as features land:

1. Streak / achievement updates on lesson completion (gamification not built).
2. Vocabulary review updates SRS scheduling.
3. AI tutor turn with the mock provider.
4. Run the app against a real database (PostgreSQL integration).

## 5. Commands

```bash
pnpm test             # pytest (backend; also covers static frontend serving)
pnpm backend:test     # pytest
```

## 6. CI expectations (when CI exists)

- `lint`, `typecheck`, `test` on every change; `build` on PRs targeting main.
- A failing test blocks the change.
- Coverage is a signal, not a gate.

## Backend extension verification (2026-10-18)

Full suite: **121 passed, 1 skipped** (PostgreSQL migration/drift test skipped
without TEST_DATABASE_URL). Ruff and mypy pass. Existing 64 regression tests pass;
57 new tests cover provider HTTP errors/timeouts/configuration/structured outputs,
SSE framing and truncation, auth/ownership/persistence, malformed practice output,
prompt trust roles, explanation answer-key exclusion, quotas/budgets/concurrency,
vocabulary review/ownership, streak dates, deterministic achievements, profile
validation, password-reset hashing/expiry/reuse/session revocation and body/error
redaction. No paid provider requests are used.

Default database fixtures are SQLite, **not PostgreSQL integration evidence**.
To rerun all API/ORM tests against PostgreSQL and check the complete migration
chain in isolated schemas, set TEST_DATABASE_URL as described in development.md.
The implementation environment had no Docker/PostgreSQL tools, and localhost:5432
refused IPv4/IPv6 connections. Offline migration SQL compiled; actual Alembic
upgrade failed before applying anything. Live AI testing also remains pending.
One existing Starlette/httpx TestClient deprecation warning is unrelated to these
changes; no new test-only dependency was added to suppress it.
