# Testing Plan

> Strategy: `docs/testing.md`. This plan sequences test adoption.

## Stage 0 — Foundation

- [x] Define the testing strategy and critical flows (this document + docs).
- [ ] Choose and document exact tool config when packages are created.

## Stage 1 — Backend bootstrap

- [ ] Vitest configured per package; `pnpm test` runs unit + integration.
- [ ] Test Postgres via docker compose; migrate before integration runs.
- [ ] Factories for `User`/`Profile`; first API e2e for `/health`.

## Stage 2 — Auth & users

- [ ] Unit: password hashing/verification, token issue/rotation, reuse detection.
- [ ] API e2e: register → login → refresh → logout; forgot/reset; validation errors.
- [ ] Authorization tests: cross-user access denied.

## Stage 3 — Learning

- [ ] Unit: exercise grading per type; progress transitions.
- [ ] Integration: lesson completion transaction updates progress/XP/streak.
- [ ] API e2e: course/lesson/exercise flows.

## Stage 4 — Vocabulary & gamification

- [ ] Unit: SRS scheduling; XP → level; achievement idempotency.
- [ ] Integration: review recording + scheduling update in one transaction.

## Stage 5 — Frontend & e2e

- [ ] Playwright: auth, lesson completion, vocabulary review, AI tutor turn.
- [ ] Accessibility checks (axe) on key screens.
- [ ] Visual smoke on desktop + mobile viewports.

## Stage 6 — AI

- [ ] All AI tests use the `mock` provider.
- [ ] Unit: prompt builders, output-schema validation, error normalisation.
- [ ] Security: prompt-injection adversarial cases.

## Cross-cutting

- [ ] CI runs lint + typecheck + test on every change.
- [ ] Coverage reported but not gated.
- [ ] Flaky tests are fixed or removed, never ignored.

## Risks / watch-items

- Tests coupled to implementation slow refactors — assert behaviour/contracts.
- Integration tests need a real database; keep them isolated and fast enough.
- Avoid over-testing trivial getters; focus on rules and boundaries.
