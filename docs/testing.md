# Testing

> Status: **M1 implemented** for unit/API tests. Integration and browser e2e
> tests are planned. Rollout order: `plans/testing-plan.md`.

## 1. Principles

- Tests ship with the feature, not in a later phase.
- No real external network calls (AI providers, email) in tests.
- Tests are deterministic and do not require a running database unless they are
  explicitly integration tests.
- Test behaviour and contracts, not implementation details.

## 2. Tooling

| Level          | Tool                          | Scope | Status |
| -------------- | ----------------------------- | ----- | ------ |
| Backend unit/API | pytest + FastAPI TestClient | routers, services, dependencies | ✅ |
| Frontend unit  | Vitest                        | API client, non-visual logic | ✅ |
| Integration    | pytest + test PostgreSQL      | SQLAlchemy models/repositories | ⬜ |
| Browser e2e    | Playwright                    | critical user journeys | ⬜ |

Backend database access is replaced with FastAPI dependency overrides, so the
test suite runs without PostgreSQL.

## 3. Current tests

Backend (`backend/tests/`):

- `test_health.py` — reports `database: up/down`, never fails the request.
- `test_users.py` — `/users/me` returns a camelCase profile; production rejects
  the dev stub with a `401` envelope.

Frontend (`frontend/src`):

- `lib/api/client.spec.ts` — success, HTTP error with backend `code`, network
  error (`status 0`), invalid response.

## 4. Critical flows (to cover as features land)

1. Register → login → refresh → logout.
2. One user cannot read/modify another user's data.
3. Complete a lesson → progress, XP and streak update.
4. Vocabulary review updates SRS scheduling.
5. AI tutor turn with the mock provider.
6. Run the app against a real database (integration).

## 5. Commands

```bash
pnpm test                       # both packages
pnpm backend:test               # pytest
pnpm --filter @fleng/frontend test   # vitest
```

## 6. CI expectations (when CI exists)

- `lint`, `typecheck`, `test` on every change; `build` on PRs targeting main.
- A failing test blocks the change.
- Coverage is a signal, not a gate.
