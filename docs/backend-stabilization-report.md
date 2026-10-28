# Backend stabilization — 2026-10-28

## Scope and Git safety

Work is limited to backend stabilization on the existing FastAPI modular monolith.
No product features, schema changes, migrations, frontend redesign or database
replacement were introduced. The only UI behavior change is signing out the
current Settings page after a successful password change.

Initial `git status --short` was empty and `git diff --check` passed. No user
changes were reset. During execution, `CSS.star4life/CSS/main` became modified;
this unrelated change was not made, formatted or reverted during stabilization.
It is committed separately under the subsequent request to commit all changes.
The development database `backend/data/fleng.db` was not used by tests/smoke,
deleted or recreated. Existing environment/credentials were not changed.
At the stabilization handoff, no commits or pushes had been created, following
the task's explicit instruction. The subsequent user request authorizes committing
the completed stabilization, refreshed README and all current working-tree changes.
No push was requested.

## Confirmed problems and fixes

| Finding | Evidence | Resolution |
| --- | --- | --- |
| Refresh rotation could issue two successors | Loading only HEAD's original rotation into the test process produced two HTTP 200 responses on independent file-SQLite connections | Conditional UPDATE claim, shared identity lock, single transaction and rollback |
| Login/register lacked throttling | Router/service inspection | Existing persistent limiter reused before password work |
| Argon2 blocked async login/register | Direct synchronous hash/verify/dummy calls in async services | Shared AnyIO worker limiter, maximum four concurrent password workers per event loop |
| Ordinary password change left refresh sessions valid | Password route inspection | Shared invalidation service for ordinary change and reset |
| SQLite learner locking was ineffective | Existing FOR UPDATE is unsupported by SQLite | SQLite no-op write acquires its writer lock; PostgreSQL retains row locking |
| Documentation contradicted existing modules | AGENTS/backend/auth/security/plans had obsolete states | Targeted status, auth policy, map and plan updates |
| Pytest hung in restricted execution | Minimal aiosqlite SELECT 1 reproduces independently of pytest | Run in an environment permitting the driver/event-loop wake-up path; no application workaround |

Password change and reset already offloaded hashing with `asyncio.to_thread`;
those paths were moved to the same explicitly bounded budget. No existing
password-rehash/upgrade flow was present; none was introduced. Argon2id and its
parameters are unchanged. AnyIO was already installed through the FastAPI stack;
it is now declared as a direct dependency because the code imports it directly.

## Atomic refresh rotation

1. Resolve the token hash's owner without treating that read as authorization.
2. Acquire the same learner identity lock used by password mutations and issuance.
3. Claim with `UPDATE refresh_tokens SET revoked_at = ... WHERE token_hash = ...
   AND revoked_at IS NULL AND expires_at > ... RETURNING id`.
4. Only the claimant creates a successor and links `replaced_by_id`.
5. Revocation, insertion and link commit together. Exceptions roll back the claim
   and uncommitted successor; tests inject both a unique-constraint insert failure
   and a pre-commit failure, then prove the old token still works.

Concurrent replay receives `401 REFRESH_TOKEN_REUSED`. The full refresh-session
set, including the winner's successor, is durably revoked. Thus two concurrent
requests return 200/401 and the winning cookie can already be invalidated by
strict reuse detection. This deliberately preserves existing policy.
Unknown and expired tokens return `401 INVALID_REFRESH_TOKEN` without creating
sessions. Logout now uses a conditional UPDATE as well.

The identity lock is a no-op UPDATE preserving `updated_at` on SQLite and a
`SELECT FOR UPDATE` on PostgreSQL. It orders password changes, reset, rotation,
login issuance and learning writes consistently. SQLite retains its existing
30-second connection busy timeout; no retry loop or silent fallback was added.

## Login/register rate limiting

Existing `request_limits` storage and dialect-specific upsert are reused.
Conditional increments prevent concurrent requests from exceeding a quota.
No migration is needed.

| Setting | Default |
| --- | --- |
| AUTH_LOGIN_IP_PER_MINUTE | 20 attempts per peer IP per UTC minute |
| AUTH_LOGIN_EMAIL_PER_MINUTE | 10 attempts per normalized email per UTC minute, shared across IPs |
| AUTH_REGISTER_IP_PER_HOUR | 10 attempts per peer IP per UTC hour |

IP accounting commits before the email check; rejected credentials and exhausted
email windows cannot erase the IP attempt. Keys store SHA-256 digests, not raw
IP/email. `429 RATE_LIMITED` is generic for known and unknown accounts.
`Retry-After` is the positive rounded-up time to the fixed-window boundary.
The existing `409 EMAIL_TAKEN` registration contract is preserved; duplicate
registration still reveals an existing address, and this is explicitly documented.

The app ignores raw forwarding headers and reads only ASGI `request.client.host`.
Local launch commands now disable Uvicorn proxy-header processing. A production
proxy must have explicit trusted addresses, overwrite forwarding headers and
restrict direct backend access. Trusting arbitrary proxies is not supported.

## Password changes and session lifecycle

Normal change keeps the existing **POST** `/api/v1/users/me/password` route and
204 response. Both change and reset now use shared invalidation of all refresh
sessions and outstanding reset tokens in the password transaction. Password
verification is refreshed under the identity lock. Login issuance rechecks the
verified password hash under the same lock, rejecting credentials checked before
a concurrent password mutation. Failed password transactions preserve the old
password, refresh sessions and reset token state after request-session rollback.

Settings clears its in-memory access token, tells the user to sign in again and
redirects to login. No new token-version field or migration was needed.
Already issued access JWTs remain valid until configured expiry, default
15 minutes. This residual lifetime also applies to reset, logout and reuse;
other tabs/devices may retain access during it. Immediate access-token revocation
is not claimed.

## Pytest hang diagnosis

A minimal `asyncio.run` + `aiosqlite.connect(':memory:')` + `SELECT 1` hung inside
the sandbox with no FastAPI, SQLAlchemy fixtures, HTTP client, pool, network DB
or background application task involved. A timed faulthandler dump showed the
aiosqlite worker in its queue loop and the main event loop waiting in its selector.
The identical program outside the sandbox returned `(1,)` immediately.

This isolates the observed failure to the restricted environment's cross-thread
asyncio wake-up path. It does not establish an OS-level mechanism. The complete
application suite runs to completion with the required permissions. No tests
were disabled and no timeouts were increased to conceal a failure.

## Verification

- **VERIFIED:** full pytest: **156 passed, 15 skipped**, one existing
  Starlette/httpx TestClient deprecation warning. All skips require PostgreSQL.
- **VERIFIED:** Ruff lint; mypy over 64 app source files; formatting of touched
  Python files; JavaScript syntax for Settings/dev launcher; `git diff --check`.
- **VERIFIED:** original rotation reproduction returned 200/200; corrected
  implementation's concurrency regression returns 200/401 and revokes the set.
- **VERIFIED:** isolated file-SQLite independent-connection tests cover quota
  concurrency, expiry/invalid/reuse, rollback, foreign keys/uniqueness, ordinary
  change/reset against refresh, multi-device revocation, stale login issuance,
  once-only XP and lesson completion/attempt counters, worker bounds and errors.
- **VERIFIED:** `python3 scripts/backend-stabilization-smoke.py` starts
  `npm run dev` against temporary SQLite, applies all migrations, checks health,
  register/login/rotation/reuse/password/logout, Dashboard and Lessons APIs,
  once-only XP, then restarts and proves account/progress persistence.
- **VERIFIED:** Alembic history has one linear chain of five migrations and head
  `20261018_1200`; complete PostgreSQL offline migration SQL compiles.
- **PARTIALLY VERIFIED:** PostgreSQL compatibility has SQL/type/static checks and
  opt-in independent-schema tests; no real PostgreSQL execution is claimed.
- **PARTIALLY VERIFIED:** Settings reauthentication behavior has syntax/static
  checks; the HTTP password/session contract is exercised, but no new browser
  automation run was performed for the notification/redirect.
- **NOT VERIFIED:** live PostgreSQL migrations, schema drift and concurrent writes
  (`TEST_DATABASE_URL` not configured), real SMTP/OpenRouter and production proxy
  deployment. No server was installed or started to fill these gaps.

The smoke runner uses a temporary directory/database/port, terminates only its
own process group and removes only its own temporary files. It can be rerun from
the repository root without touching local learner data. The test module also
supports isolated PostgreSQL schemas when a dedicated TEST_DATABASE_URL is set.

## Independent self-review and remaining risks

Self-review checked transaction boundaries, lock ordering, stale ORM state,
exception/rollback behavior, quota persistence, secret/error handling, ownership,
API contracts, dependency direction and documentation. It found and corrected
profile expiration after an overly broad ORM refresh, unified password/reset
invalidation, and removed a timing assumption in the thread-budget test.
No schema change or extra infrastructure was needed.

Remaining limitations: short access-JWT residual lifetime; strict reuse can
sign out legitimate concurrent callers; fixed windows allow boundary bursts and
email quotas can be used to temporarily throttle a target; SQLite serializes
writers and may return 503 after its bounded busy timeout under heavy contention.
This phase verifies correctness for the tested concurrency, not production load.
Refresh-specific throttling is still deferred. Real PostgreSQL and production
proxy behavior require their own runtime verification. Existing duplicate-email
registration disclosure is retained to preserve the API contract. The existing
TestClient deprecation warning remains.

## Changed files

Runtime/configuration:

- `backend/app/core/config.py`, `backend/app/core/limits.py`
- `backend/app/modules/auth/router.py`, `security.py`, `service.py`
- `backend/app/modules/gamification/service.py`
- `backend/app/modules/password_reset/service.py`
- `backend/app/modules/users/router.py`
- `backend/pyproject.toml`, `.env.example`
- `scripts/dev.mjs`, `package.json`
- `frontend/js/settings.js` (session handling only)

Verification:

- `backend/tests/test_stabilization.py`
- `scripts/backend-stabilization-smoke.py`

Documentation and plans:

- `AGENTS.md`, `README.md`, `backend/README.md`
- `docs/api.md`, `authentication.md`, `backend.md`, `development.md`,
  `security.md`, `testing.md`, `backend-stabilization-report.md`
- `project-map/api-map.md`, `data-flow.md`, `modules.md`
- `plans/backend-plan.md`, `milestones.md`, `roadmap.md`, `security-plan.md`,
  `testing-plan.md`

`CSS.star4life/CSS/main` contains an unrelated two-line trailing-whitespace
cleanup. It is preserved in a separate nested-repository commit under the follow-up
request to commit all changes, then referenced by the parent repository. No local
database or real credential file is in the change set.
