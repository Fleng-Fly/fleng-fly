# Threat model

| Threat | Existing mitigation | Remaining limitation |
| --- | --- | --- |
| Account takeover | Argon2id, bounded workers, auth quotas, generic failed login | No MFA/email verification; registration reveals duplicates |
| Token theft/replay | In-memory JWT, HttpOnly Secure refresh, hashed storage, atomic rotation | Stolen access JWT valid until expiry; XSS/browser compromise remains |
| Unauthorized data | JWT identity, owner-scoped queries, foreign-ID 404 | New handlers must preserve filters; no general admin RBAC |
| Cross-origin abuse | Exact CORS, Origin guard, SameSite | No-Origin requests accepted; ingress/TLS needs live verification |
| Flooding | Body cap, auth/reset limits, bounded password/AI work | No complete edge/DDoS defense or refresh quota |
| Provider key exposure | Backend-only transport, private configuration | Accidental logging/static publication remains operational risk |
| Privilege escalation | No client owner override; draft/reviewer authorization | Preview must never be tunneled/deployed |
| Malicious payloads | Pydantic, bound queries, safe text rendering | Extras not globally forbidden; no full CSP policy |
| AI manipulation | Server prompts, bounded context, output schemas | Incorrect teaching/prompt injection not solved |
| Data loss | Migrations/FKs/conflict refusal | Ephemeral disks lose data; backups not automatic |

Assets: identity/password hashes, sessions, progress, vocabulary, chat, draft keys and provider credentials. Boundaries: browser/API, API/DB, API/provider/SMTP and operator/preview. Tests verify selected mechanisms, not a complete penetration test.

[Section index](README.md) · [Documentation home](../README.md)
