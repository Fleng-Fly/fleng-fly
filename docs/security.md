# Security

> Status: **partial**. The M1 foundation implements strict CORS (explicit
> origins, credentials), global input validation, a non-leaking error envelope,
> a production-gated dev-auth dependency, and env-only configuration. Auth, rate
> limiting, security headers and AI guardrails are not implemented yet. This
> document defines the baseline every feature must respect.

## 1. Threat model (initial)

Assets worth protecting:

- User credentials and personal data (email, profile, learning history).
- Session tokens (access/refresh).
- AI provider keys and prompt/response data.
- Content and progress integrity (prevent cheating/abuse of gamification).

Primary threats:

- Credential stuffing / brute force on auth endpoints.
- Token theft/replay.
- Broken access control (accessing another user's data).
- Injection: SQL (mitigated by SQLAlchemy parameterised queries), input validation
  bypass, **prompt injection** against the AI tutor.
- Secret leakage via git, logs, error messages, or the frontend bundle.
- Abuse of AI endpoints to run up provider cost.

## 2. Authentication

See `docs/authentication.md`. Summary: argon2id hashing, short-lived access JWT,
rotating refresh tokens stored hashed, reuse detection, session revocation.

## 3. Authorization

- Default deny: every non-public endpoint requires authentication.
- Role checks (`require_role(...)` FastAPI dependency) for admin-only operations.
- **Ownership checks in queries** (`WHERE userId = :currentUser`), not only in
  dependencies. Prefer `404` over `403` when existence itself is sensitive.
- Never trust a `userId` from the request body; derive it from the token.

## 4. Input validation

- Validate every request body/query/param at the edge with Pydantic schemas.
- Reject unexpected fields with strict models
  (`model_config = ConfigDict(extra="forbid")`) and explicit response models.
- Bound list sizes, string lengths and numeric ranges.
- Validate AI structured output against a schema before persisting/using it.

## 5. Injection and data access

- All database access goes through SQLAlchemy (parameterised queries). Raw SQL
  only if unavoidable, always parameterised, and reviewed.
- Escape/sanitise any user content rendered where XSS is possible; rely on React
  escaping and avoid `dangerouslySetInnerHTML` without sanitisation.
- Validate file/uploads (none yet) before use.

## 6. AI / LLM specifics

- **Prompt injection**: treat user input as untrusted data. System instructions
  are server-owned; user text is clearly delimited and never concatenated as
  instructions. Tool/action execution from model output is disallowed at this
  stage.
- **Output handling**: never execute model output; validate and, where rendered,
  treat as untrusted text. Do not render model HTML.
- **Data minimisation**: send only the context needed; do not include secrets,
  other users' data or unrelated PII in prompts.
- **Cost/abuse**: per-user and global rate limits, max token budget, timeouts.
- **Failure modes**: fail closed; return a generic AI error without provider
  internals.
- **Logging**: do not log full prompts/responses by default; log ids, hashes or
  redacted summaries.

## 7. Secrets management

- All secrets via environment variables; `.env` is git-ignored.
- `.env.example` contains only names/placeholders.
- Secrets are validated on startup (fail fast if missing in production).
- Never log secrets; never expose them to the frontend.
- Rotate `JWT_*` and `AI_API_KEY` on suspected compromise.

## 8. Transport and headers

- HTTPS only in production; HSTS.
- Security headers (`X-Content-Type-Options`, `Referrer-Policy`, HSTS, …) via
  Starlette middleware or the reverse proxy; not implemented yet.
- CORS restricted to configured frontend origins; no wildcard with credentials.
- Cookies: `httpOnly`, `Secure`, `SameSite`, scoped path.

## 9. Rate limiting and abuse

| Endpoint class | Limit strategy |
| -------------- | -------------- |
| Auth (login/register/reset) | strict per-IP + per-account |
| AI | per-user + global budget |
| Write endpoints | moderate per-user |
| Reads | generous per-user/IP |

Responses return `429` with `Retry-After`.

## 10. Logging, monitoring, privacy

- Structured logs with correlation ids; no secrets/PII in logs.
- Errors are logged server-side; clients receive a safe error envelope with a
  `requestId` for correlation.
- Personal data: collect the minimum, allow account deletion/anonymisation
  (policy pending — see `docs/database.md` open questions).

## 11. Dependency and supply-chain hygiene

- Keep dependencies current; remove unused ones (also an `AGENTS.md` rule).
- Review new dependencies before adding (necessity + maintenance + license).
- No secrets or credentials in the repository; a leak triggers rotation.

## 12. Checklist for new endpoints

- [ ] Requires auth (or is explicitly public by design).
- [ ] Ownership/role enforced in the query, not only the dependency.
- [ ] Input validated and bounded.
- [ ] Output is a Pydantic response schema (no internal fields leaked).
- [ ] Rate limited if abusable or expensive.
- [ ] Errors use the standard envelope; no internals leaked.
- [ ] No secrets/PII logged.
