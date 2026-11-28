# Testing Plan

> Strategy: `docs/testing.md`. Legend: ✅ done · ⬜ next · 🔴 planned.

- [x] Cover the return of browser-only Reading in the backend static-serving test and preserve
      checks that the legacy article routes and API are unavailable.
- [ ] Verify all seven checks on the GitHub Actions Ubuntu runner after the local CI fix is pushed.

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
- [x] Playwright (`e2e/`, `npm run test:e2e`): register/login/logout, catalog, course → lesson,
      correct/incorrect answers, saved progress, once-only XP, private-page protection.
      See `docs/qa/e2e.md`. Not yet in CI.
- [ ] Playwright: vocabulary review, AI tutor turn.
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

## Draft curriculum quality — 2026-11-16

- Completed: separate editorial candidate repairs 500 missing examples, answer
  positioning, all 145 confirmed practice copies (+5 non-gap copies) and all 83
  audit vocabulary-context omissions (+40 stricter-detection gaps).
- Completed: four repaired strict xfails converted to regular candidate regressions;
  all keys checked through the existing grader, published source/approval preserved.
- Completed: explicit candidate validator, runtime-source validator and targeted
  curriculum/import/grading tests; details in docs/qa/draft-curriculum-fixes.md.
- Next: teacher/translator review and a separately authorized version/publication
  strategy. Human review and broader audit findings remain open; no deployment.

## CI/CD and developer experience sprint — 2026-11-17

- Completed: existing workflow split into independent SQLite, quality, frontend,
  E2E, PostgreSQL and workflow-validation jobs; all feed the stable required gate.
- Completed: constrained/frozen installs, pip/npm/pnpm caching, E2E-only browser,
  duplicate database pytest invocations removed; no production operations.
- Completed: fail-fast isolated check:all, dependency verification and disposable
  Alembic smoke; explicit Web Locks fixture for Node 22 regression compatibility.
- Completed: full check:all exit 0; backend 2373 passed / 24 skipped, frontend
  63 passed, E2E 9 passed; Ruff/mypy/docs/migrations/dependencies/workflow checks passed.
- In progress / external: hosted execution is unverified until an authorized push.
- Next: separately authorized hosted push/PR to validate actual runner behavior,
  caches, PostgreSQL service and branch enforcement; no push in this sprint.

[Commands and diagnostics](../docs/10-testing/ci-automation.md).

[Local sprint evidence](../docs/qa/ci-automation-verification.md).

## Lesson exercise flow

- Completed: server-derived FIFO and tab-local cursor restoration, plus a
  read-only preview before self-assessment.
- Covered in Chromium regressions with temporary SQLite: repeat failures,
  reload, answer timers, conflicting submissions and lost responses.
- Next: verify the changed flow in live PostgreSQL CI.
