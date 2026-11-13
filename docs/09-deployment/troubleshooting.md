# Troubleshooting

Auth 403 can come from exact Origin rejection before DB writes. Compare browser HTTPS Origin with configured CORS/Render origin and ASGI scheme. Never enable wildcard forwarding trust as an origin fix. Historical evidence: [registration Origin](../render-registration-origin-403.md), [TLS mismatch](../render-https-origin-403.md).

503 DATABASE_UNAVAILABLE can mean connectivity/permissions/missing schema/runtime SQLite. Review classified logs and after_migrations/fastapi_startup snapshots; readiness can pass with missing tables. From backend/, `python -m app.db.diagnostics` inspects the configured existing SQLite without migrations/user rows. Never print private URLs or stamp/delete DB as repair. [Diagnostic procedure](../render-sqlite-registration-diagnostics.md) retains detail.

Netlify API 404 suggests disabled proxy; static HTML is not integration. AI status is readiness only. Cookie problems require HTTPS/path/SameSite/proxy inspection; cross-site cookie auth is unverified. Data loss after hosting replacement requires backup recovery, not recreating user state with seed tooling.

[Section index](README.md) · [Documentation home](../README.md)
