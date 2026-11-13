# Cookies and sessions

Defaults: fleng_refresh, /api/v1/auth path, HttpOnly, host-only, SameSite=lax, 30 days. Secure derives from production unless configured; production refuses false. SameSite=none requires Secure. No cookie domain setting exists.

JWTs are response JSON stored in browser memory. Auth session routes validate supplied Origin against own/configured origins; absent Origin is allowed. No separate CSRF token exists. SameSite/path scoping does not eliminate XSS/compromised-browser risk.

Strict refresh reuse can revoke sessions on stale/concurrent replays. api.js serializes same-tab refresh, not every tab/process. Signing-key rotation invalidates JWT signatures; persistent refresh sessions require a separate revocation decision.

[Section index](README.md) · [Documentation home](../README.md)
