# Security Plan

> Baseline: `docs/security.md`. This plan sequences the work.

## Stage 1 — Foundations (with backend bootstrap)

- [ ] Validated configuration; secrets only from env; fail fast in production.
- [ ] `helmet`, strict CORS, request size limits.
- [ ] Global `ValidationPipe` (whitelist + forbid unknown).
- [ ] Standard error envelope that never leaks internals; `requestId`.
- [ ] Structured logging with redaction of secrets/tokens.
- [ ] `.env.example` only; `.gitignore` covers env/key files.

## Stage 2 — Auth hardening (with auth module)

- [ ] Argon2id password hashing; password policy.
- [ ] Access JWT + rotating refresh tokens stored hashed.
- [ ] Refresh reuse detection revokes the token chain.
- [ ] Rate limiting on login/register/refresh/forgot-password.
- [ ] No account enumeration (generic responses, timing-consistent login).
- [ ] Cookies: httpOnly, Secure, SameSite, scoped path.

## Stage 3 — Authorization

- [ ] Default-deny dependencies; `require_role(...)` for admin routes.
- [ ] Ownership enforced in queries; `404` over `403` where sensitive.
- [ ] Tests that user A cannot read/modify user B's resources.

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
