# Fleng 1.0 security/stability

Email confirmation, coordinated refresh and retired-PWA contracts are described
in [authentication](authentication.md#fleng-10-securitystability--2026-11-16).

Independent self-review checked identity-lock ordering, stale login issuance,
password/reset invalidation, token replay/expiry, address uniqueness at commit,
SMTP failure, request throttling and absence of raw secrets in stored records.
Login now rechecks both verified email and password hash under the identity lock,
so credentials checked against the old email cannot issue a session after a
concurrent email change. Learning logic and CSS are unchanged.

Verification:

- Final full `npm run backend:test -- -q`: **495 passed, 24 skipped**,
  72 Alembic deprecation warnings, 215.62 seconds. PostgreSQL-dependent tests
  skip without TEST_DATABASE_URL. pytest-asyncio also reports its existing
  unset fixture-loop-scope deprecation warning.
- `git diff --check`: passed.

- `npm run frontend:test`: six test files passed, including refresh with valid
  access/no Web Locks, unavailable/denied locks and coordinated refresh.
- `npm run test:pwa`: both scripts passed, preserving selective legacy worker
  and cache cleanup without bringing back installation.
- `npm run backend:lint`: passed; `npm run backend:typecheck`: passed (83 files).
- Email-change targeted regressions and SQLite migration round trip passed.
- Independent-connection email tests passed; PostgreSQL cases skip without
  TEST_DATABASE_URL.

The first full run caught a pre-existing timing-dependent AI-budget test:
its 200 ms sleep could release the provider reservation before slow competitors
arrived, legitimately freeing unused budget. It now keeps the mocked provider
blocked until competitors finish; budget assertions remain strict. Migration-head
expectations were updated for the new revision. No paid provider was contacted.

Real SMTP, public HTTPS/browser delivery and live PostgreSQL are not exercised.
Existing access JWTs expire normally rather than being immediately revoked.

No commit, push, deployment or paid API request was performed.
