# Security Plan

> Baseline: `docs/security.md`. This plan sequences the work.

## Stage 1 — Foundations (with backend bootstrap)

- [x] Validated configuration; secrets only from env; fail fast in production
      (`JWT_ACCESS_SECRET`).
- [x] Strict CORS (explicit origins with credentials).
- [ ] Security headers, request size limits.
- [ ] Global Pydantic validation that rejects unknown fields.
- [x] Standard error envelope that never leaks internals (`requestId` pending).
- [ ] Structured logging with redaction of secrets/tokens.
- [x] `.env.example` only; `.gitignore` covers env/key files.

## Stage 2 — Auth hardening (with auth module)

- [x] Argon2id password hashing; minimum password length (8) enforced.
- [x] Access JWT + rotating refresh tokens stored hashed (SHA-256).
- [x] Refresh reuse detection revokes the whole session set.
- [x] Persistent rate limiting on login/register/password reset.
- [ ] Rate limiting on refresh.
- [x] Atomic refresh claims and password-change/reset refresh-session invalidation.
- [x] Bounded Argon2 workers; SQLite/PostgreSQL learner lock strategy.
- [x] No account enumeration (generic errors, timing-consistent login).
- [x] Cookies: HttpOnly, Secure, SameSite, scoped path; Origin check on
      cookie-backed endpoints.

## Stage 3 — Authorization

- [x] Authenticated-user dependency; `/users/me` and `/progress/me` are default
      protected.
- [x] Ownership enforced by scoping queries to the authenticated user id.
- [x] Tests that user A cannot read user B's data.
- [ ] `require_role(...)` for admin routes (no admin routes yet).

## Stage 4 — AI security

- [x] Server-owned system prompts; user content delimited as data.
- [x] JSON-schema validation of model output; no execution of output.
- [x] Per-user + global rate limits and token budgets.
- [ ] Prompt-injection tests with adversarial inputs.
- [x] No full prompt/response logging by default.

## Stage 5 — Pre-launch

- [ ] Dependency audit; remove unused deps.
- [ ] Secret rotation runbook (`JWT_*`, `AI_API_KEY`).
- [ ] HTTPS/HSTS enforced; CORS verified in production config.
- [ ] Data deletion/anonymisation policy implemented.
- [ ] Security checklist (`docs/security.md §12`) applied to every endpoint.

## Risks / watch-items

- Rate limits already use shared database windows; reassess storage only with
  measured contention. No Redis is needed for current correctness.
- Prompt injection is an open area; treat as ongoing, test continuously.
- Avoid "security theatre": controls must map to the threat model.


## Fleng 1.0 security/stability — 2026-11-16

- Completed: password-authorized SMTP email confirmation, 30-minute one-use
  tokens, refresh revocation, migration and regression coverage.
- Completed: Web Locks required only at refresh time; no automatic fallback;
  strict server reuse detection preserved.
- Completed: retired-PWA backend contracts aligned; worker/cache cleanup retained.
- Next/external: public HTTPS EMAIL_CHANGE_URL/SMTP delivery and live PostgreSQL
  verification. No paid provider calls, commit or push in this stage.
- Verification details: docs/security-stability-1.0.md.

## Fleng 1.0 confirmed findings — 2026-11-16

- Implemented, verification in progress: uniform AI admission order and portable
  refusal settlement; public-header Logout error/retry; Login password-reset
  request and reset confirmation page with regression tests.
- Awaiting user contract approval: password + new-address verification before an
  email change, and fail-closed refresh behavior in browsers without Web Locks.
- Next: complete the approved contracts, full pytest/frontend/PWA/Ruff/mypy/docs
  checks, independent review. No commit/push or paid provider requests authorized.

Verification of the implemented subset: targeted backend 186 passed; full backend
489 passed / 22 skipped / 2 failed (pre-existing test_pwa.py expectations for the
retired installation manifest). Frontend 6 test files and legacy-PWA retirement
checks pass; Ruff/mypy/docs contracts and diff whitespace checks pass. Web Locks
coordination is implemented/tested for supporting same-origin browsers. Email
change and unsupported-browser refresh policy remain awaiting user approval.
