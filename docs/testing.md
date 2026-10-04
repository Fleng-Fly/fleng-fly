# Testing

> Status: **design** (pre-implementation). Strategy: unit + integration for the
> backend, API e2e, and browser e2e for critical flows. Rollout order is in
> `plans/testing-plan.md`.

## 1. Principles

- Tests ship with the feature, not in a later phase.
- No real external network calls (AI providers, email) in tests — use the `mock`
  provider and fakes.
- Tests are deterministic: fixed clock/seed where needed, isolated data per run.
- Test behaviour and contracts, not implementation details.

## 2. Test pyramid

| Level | Tool | Scope | Speed |
| ----- | ---- | ----- | ----- |
| Unit | Vitest | pure logic, services (with mocked repos), guards, prompt builders | fast |
| Integration | Vitest + test Postgres | repositories, transactions, migrations | medium |
| API e2e | Supertest | endpoint contracts, auth, validation, error envelope | medium |
| Browser e2e | Playwright | critical user journeys | slow |

Frontend component tests are added only for non-trivial logic; markup is covered
by e2e where it matters.

## 3. Critical flows (must be covered)

1. Register → login → refresh → logout.
2. One user cannot read/modify another user's data (ownership).
3. Complete a lesson → progress, XP and streak update.
4. Vocabulary review updates SRS scheduling.
5. AI tutor turn with the `mock` provider persists conversation/messages.
6. Validation and error envelope behave consistently.

## 4. Test data

- A dedicated test database (docker compose service) migrated before the run.
- Factories/builders for users, courses, lessons, and vocabulary.
- Seed data is idempotent and separate from test fixtures.

## 5. CI expectations (when CI exists)

- `lint`, `typecheck`, `test` on every change; `test:e2e` on PRs targeting main.
- A failing test blocks the change.
- Coverage is a signal, not a gate; do not chase a percentage.

## 6. Commands (intended)

```bash
pnpm test          # unit + integration + API
pnpm test:e2e      # Playwright
pnpm --filter @fleng/backend test --watch
```
