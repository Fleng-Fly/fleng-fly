# Testing Plan

> Strategy: `docs/testing.md`. Legend: ✅ done · ⬜ next · 🔴 planned.

## Stage 0 — Foundation ✅

- [x] Define the testing strategy and critical flows.
- [x] pytest (backend) and Vitest (frontend) configured.

## Stage 1 — Bootstrap ✅

- [x] Backend API tests for `/health` and `/users/me` (dependency overrides; no
      database required).
- [x] Frontend unit tests for the API client.
- [x] `pnpm test` runs both suites.

## Stage 2 — Database integration ⬜

- [ ] Integration tests against a test PostgreSQL database (apply Alembic
      migrations before the run).
- [ ] Factories for `User`/`Profile`.
- [ ] CI service container for PostgreSQL.

## Stage 3 — Auth ⬜

- [ ] Unit: password hashing/verification, token issue/rotation, reuse detection.
- [ ] API: register → login → refresh → logout; forgot/reset; validation errors.
- [ ] Authorization: cross-user access denied.

## Stage 4 — Learning ⬜

- [ ] Unit: exercise grading per type; progress transitions.
- [ ] Integration: lesson completion updates progress/XP/streak.
- [ ] API: course/lesson/exercise flows.

## Stage 5 — Frontend e2e ⬜

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
