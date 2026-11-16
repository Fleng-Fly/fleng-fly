# Testing Plan

> Strategy: `docs/testing.md`. Legend: ✅ done · ⬜ next · 🔴 planned.

## Stage 0 — Foundation ✅

- [x] Define the testing strategy and critical flows.
- [x] pytest (backend) configured; the static frontend is tested via ASGI.

## Stage 1 — Bootstrap ✅

- [x] Backend API tests for `/health` and `/users/me` (dependency overrides; no
      database required).
- [x] Static frontend serving tests (pages/assets served, API on the same origin).
- [x] `pnpm test` runs the suite.

## Stage 2 — Database integration ⬜

- [x] In-memory SQLite fixture exercising models, constraints and transactions
      (no server needed; `backend/tests/conftest.py`).
- [ ] Integration tests against a test PostgreSQL database (apply Alembic
      migrations before the run).
- [ ] Factories for `User`/`Profile`.
- [ ] CI service container for PostgreSQL.

## Stage 3 — Auth ✅

- [x] Unit: password hashing/verification, token issue/rotation, reuse detection.
- [x] API: register → login → refresh → logout; wrong password; validation.
- [x] Authorization: cross-user access denied.
- [ ] Forgot/reset password flows (endpoints not implemented yet).

## Stage 4 — Learning 🚧

- [x] Unit/API: exercise grading per type; answer-key secrecy; completion rules.
- [x] API: lesson start/submit/progress; progress ownership + isolation.
- [x] Integration (SQLite): lesson completion updates progress/XP idempotently.
- [ ] Streak / achievement updates (gamification not built).

## Stage 5 — Browser e2e ⬜

- [x] Static frontend served and asserted over the ASGI app
      (`backend/tests/test_frontend.py`); same-origin CSRF origin behaviour.
- [ ] Playwright: auth, lesson completion, vocabulary review, AI tutor turn.
- [ ] Accessibility checks (axe) on key screens.

## Stage 6 — AI 🔴

- [ ] All AI tests use the `mock` provider.
- [ ] Unit: prompt builders, output-schema validation, error normalisation.
- [ ] Security: prompt-injection adversarial cases.

## Cross-cutting

- [ ] CI runs lint + typecheck + test on every change.
- [ ] Coverage reported but not gated.
- [ ] Flaky tests fixed or removed, never ignored.

## Risks / watch-items

- Tests coupled to implementation slow refactors — assert behaviour/contracts.
- Integration tests need a real database; keep them isolated and fast enough.
- Avoid over-testing trivial getters; focus on rules and boundaries.

## Backend extension verification — 2026-10-18

Completed: 121 automated tests pass; 1 opt-in PostgreSQL migration/drift test is
skipped without TEST_DATABASE_URL. Ruff and mypy pass. This includes the original
64 regressions and 57 new mocked/provider/ORM/API tests. Explicit stream-disconnect
cleanup, malformed generations, ownership, quota limits, reset expiry/reuse and
learning-to-achievement hooks are covered. No paid AI calls are used.

Blocked: real PostgreSQL integration (local server unavailable) and manual
OpenRouter test (no live configured credentials/database). Next: use the native or
Docker database setup, run the full TEST_DATABASE_URL suite, then follow docs/ai.md
manual integration instructions. Do not treat SQLite fixtures as PostgreSQL proof.

## Backend stabilization — 2026-10-28

Completed: independent-connection temporary SQLite refresh/password/quota/XP
concurrency, rollback and constraint tests; worker-bound/event-loop regression;
`npm run dev` auth/Dashboard/Lessons smoke with restart persistence.
The observed sandbox aiosqlite hang reproduces outside pytest and disappears
with unrestricted execution. No tests are disabled to hide it.
Next: run the opt-in PostgreSQL tests using a dedicated TEST_DATABASE_URL.
Live PostgreSQL is NOT VERIFIED. Results: `docs/backend-stabilization-report.md`.
