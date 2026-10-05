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
- [ ] Rate limiting on login/register/refresh/forgot-password.
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

- [ ] Server-owned system prompts; user content delimited as data.
- [ ] JSON-schema validation of model output; no execution of output.
- [ ] Per-user + global rate limits and token budgets.
- [ ] Prompt-injection tests with adversarial inputs.
- [ ] No full prompt/response logging by default.

## Stage 5 — Pre-launch

- [ ] Dependency audit; remove unused deps.
- [ ] Secret rotation runbook (`JWT_*`, `AI_API_KEY`).
- [ ] HTTPS/HSTS enforced; CORS verified in production config.
- [ ] Data deletion/anonymisation policy implemented.
- [ ] Security checklist (`docs/security.md §12`) applied to every endpoint.

## Risks / watch-items

- Rate limiting across multiple instances — revisit storage (Redis) only when
  multi-instance deployment exists.
- Prompt injection is an open area; treat as ongoing, test continuously.
- Avoid "security theatre": controls must map to the threat model.
