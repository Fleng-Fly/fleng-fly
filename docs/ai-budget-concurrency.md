# AI budget concurrency investigation — 2026-11-16

## Scope and confirmed cause

Branch `fix/ai-budget-concurrency` starts at main/origin/main
`ba6a4ec321d8eeda71d91470a54ab311b00fc789` (fetched before work).
Only AI tests and this investigation's documentation change. No runtime code,
limits, timeout settings, schema, migrations or dependencies change.

`test_parallel_users_cannot_overspend_nearly_exhausted_budget` assumed that
`asyncio.sleep(0.2)` let all five requests attempt reservation before releasing
the fake provider. That assumption depends on SQLite lock contention and task
scheduling. The provider settles an $0.80 hold at $0.0001. With $0.15 already
charged, a competitor arriving after settlement can legally reserve another
$0.80: $0.1501 + $0.80 = $0.9501, within the $1 budget. Exactly one successful
request is therefore only required while the original hold remains open.

The original test failed 17/20 ordinary repetitions and 37/40 loaded repetitions.
Load used four independent pytest processes sharing two CPU cores, ten repetitions
per process, each with fresh function-scoped SQLite databases. All observed
failures were the success-count assertion. A separate five-repeat diagnostic
produced two failures; both had three completed ledger rows with charges
150000, 100 and 100 microdollars: total $0.1502, not an overspend.
No cross-test database leakage or production budget race was demonstrated.
All provider calls were fake; no paid API was used.

## Reservation review

- `modules/ai/service.py:reserve` locks the learner and global capacity row,
  sums `COALESCE(cost_microusd, reserved_microusd)` for the UTC day, checks the
  proposed hold against the budget and commits the hold before provider calls.
- `core/limits.py:lock_ai_capacity` uses a persistent sentinel row: a SQLite
  write transaction serializes writers; PostgreSQL uses row locking. Independent
  workers cannot rely on a Python-local lock for this protection.
- Settlement replaces a reservation with the actual charge. Smaller actual
  charges intentionally free capacity; unknown charges retain the reservation.
- Expired running leases still count toward the monetary budget.

The invariant is settled charges plus outstanding reservations, not the number
of successful requests. Reservation enforcement assumes actual provider charges
stay within the configured tariff/token bound, as documented in [ai.md](ai.md).
An upstream charge above its reservation is intentionally recorded honestly;
this investigation does not claim to bound arbitrary provider overbilling or
validate live PostgreSQL behavior.

## Test correction and regression coverage

The provider stays blocked until all four competitors return HTTP 429 with
`AI_BUDGET_LIMIT`. The existing five-second failure deadline remains; no sleep
or larger timeout substitutes for synchronization. Before release, the ledger
must contain one settled charge and one outstanding hold totaling exactly
$0.95. After release all rows must be completed, totaling $0.1501. A late retry
must succeed and produce $0.1502, explicitly covering the legitimate schedule
that previously caused false failures. All totals must remain below $1.

The test runs for both chat and streaming, with simultaneous contenders and
with the final contender deliberately held until three rejections complete.
A `finally` block releases gates and drains every task even after a failed
assertion, avoiding contamination of later tests. Existing multi-process SQLite
budget tests additionally exercise real OS workers and persistent reservations.

## Validation

- Final ordinary repetitions: **80 passed** (20 repetitions of each of the four
  route/schedule combinations).
- Final loaded repetitions: **160 passed** (four pytest processes on two shared
  CPU cores, 40 cases per process); the five-second deadline was unchanged.
- `cd backend && .venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_ai_limits.py tests/test_ai_sqlite_audit.py`: **68 passed**, including
  the existing OS-process global-budget checks and populated SQLite migration
  check. Only pre-existing pytest-asyncio/Alembic deprecation warnings appeared.
- `cd backend && .venv/bin/ruff check app tests`: passed.
- `cd backend && .venv/bin/ruff format --check tests/test_ai_limits.py`: passed.
- `cd backend && .venv/bin/mypy app`: passed, 82 source files; existing note about
  untyped function bodies remains.
- `git diff --check`: passed. Scope and secret-pattern/manual review: only the
  intended AI test and three related documentation files; no secrets found.

Repeated runs used a temporary pytest plugin with a parametrized autouse fixture
and fresh function-scoped databases (20 repeats normally; 10 per loaded worker).
The plugin, stress runner and diagnostic ledger logs stayed outside the repository
in `/tmp/fleng-ai-budget-investigation` and `/tmp/fleng_budget_*.py`.
For a simple independent repeat without that plugin, run the targeted node
`tests/test_ai_limits.py::test_parallel_users_cannot_overspend_nearly_exhausted_budget`
repeatedly with the backend's existing pytest command; all four combinations run.

Independent self-review checked synchronization under both arrival schedules,
error/timeout cleanup, SSE success/error handling, exact integer monetary units,
active-hold versus settled-cost assertions and scope isolation. No production
change is justified by these results. No migration is required.
