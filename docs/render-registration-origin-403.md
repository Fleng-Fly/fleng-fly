# Render registration Origin 403 — 2026-11-04

## Confirmed cause

Public HTTP checks at approximately 19:36–19:37 UTC against
`https://fleng-fly.onrender.com` establish an origin configuration mismatch.
`_assert_trusted_origin()` in `backend/app/modules/auth/router.py` throws
`ApiError(403, "FORBIDDEN", "Origin not allowed")` for the Render HTTPS Origin.
That origin is absent from the effective CORS allowlist; the ASGI same-origin
fallback also fails to match it. Netlify's HTTPS Origin is allowed. This is
confirmed on the actual registration endpoint, not inferred from a database error.

| Origin sent | Host sent | Register POST | CORS preflight | POST allow-origin |
| --- | --- | --- | --- | --- |
| `https://fleng-fly.onrender.com` | `fleng-fly.onrender.com` | 403 `Origin not allowed` | 400 | absent |
| `https://fleng.netlify.app` | `fleng-fly.onrender.com` | 201 | 200 | Netlify origin |
| `https://untrusted.example` | `fleng-fly.onrender.com` | 403 `Origin not allowed` | 400 | absent |

Tests sent valid registration payloads without Authorization or cookies; one
synthetic smoke account was created for the successful Netlify-origin probe.
Tokens, passwords and account identifiers were not printed. The public health
endpoint returned 200 with database=up. SQLite was not inspected or changed by
this fix; the successful registration demonstrates that the rejected request's
403 does not require a database repair.

The frontend served at both addresses uses `API_BASE='/api/v1'`. A registration
from the Render page therefore targets Render with Origin
`https://fleng-fly.onrender.com` and Host `fleng-fly.onrender.com`. Netlify's
`/api/v1/health` currently returns a Netlify HTML 404, since the API proxy is
not enabled. The successful Netlify-origin probe above targets Render directly;
it does not establish working registration through the Netlify UI.

These are client-side request headers and public responses. Render Dashboard,
actual environment variable text, original user browser trace, and server ingress
logs were unavailable. The HTTP behavior proves the effective allowlist excludes
Render and includes Netlify, but does not enumerate other entries. ASGI's exact
scheme/Host cannot be read through public HTTP. The launcher disables proxy
headers with empty TRUSTED_PROXY_IPS; HTTP behind TLS termination reproduces this
failure locally. A rewritten upstream Host could also break the same-origin
fallback. Neither possibility matters once both HTTPS origins are explicit.

## Request trace

1. Uvicorn applies forwarding headers only from configured trusted proxy peers.
   `backend/run.py` disables them by default. Origin remains the browser's HTTPS
   origin even when the upstream ASGI URL uses HTTP.
2. `create_app()` installs BodyLimit outside CORSMiddleware. BodyLimit can return
   413. CORS preflight can return 400 for an origin mismatch; CORS does not reject
   actual POSTs with 403, it simply omits allow-origin for disallowed origins.
3. The API router includes the auth router without auth dependencies.
   Registration resolves get_db/settings and validates RegisterRequest; opening
   the session does not execute registration SQL. Payload errors return 422.
4. `register()` first calls `_assert_trusted_origin()`. Missing Origin remains
   allowed for non-browser clients. Otherwise the exact Origin must equal the
   ASGI scheme+netloc or a configured CORS origin. The failing branch raises the
   precise observed 403; the ApiError handler preserves its JSON envelope.
5. Only after that guard does throttle consume/commit the hashed peer-IP quota.
   Limit exhaustion returns 429 with Retry-After, never this 403.
6. Registration creates User/Profile, hashes the password, and creates the session.
   Duplicate email returns 409; database failures map to 503, not this 403.
   There is no bearer authentication requirement for public registration.

## Fix and deployment

The production environment example now contains:

```dotenv
APP_ENV=production
CORS_ORIGIN=https://fleng-fly.onrender.com,https://fleng.netlify.app
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

Set that exact CORS_ORIGIN value in Render's environment and restart/redeploy.
Keep the existing DATABASE_URL and JWT_ACCESS_SECRET. The template is not loaded
automatically and process settings are cached. No wildcard, CSRF bypass, special
Render hostname trust, forwarded-header trust expansion or cookie weakening was
added. No push or deployment is part of this change. Until the environment is
updated, the public Render registration will continue to fail for its own Origin.

Origin rejections now log method/path, bounded repr-escaped Origin and Host, and
ASGI scheme. This supplies the actual incoming values on the next deployed
failure without logging request bodies, Authorization, cookies, tokens or secrets.
The rejection response remains unchanged. To verify the deployment, submit a
fresh anonymous registration from the Render UI and match any rejection log;
repeat the HTTP matrix with both allowed origins (201) and an untrusted one (403).
Verify preflights (200/200/400). Netlify UI verification separately requires its
existing documented same-origin `/api/*` proxy to be configured and deployed.

## Regression coverage and independent review

`backend/tests/test_auth_origins.py` reads the actual production example with an
isolated test secret/database and creates the real app/middleware with an HTTP
ASGI URL and Render Host. Nine cases cover both allowed anonymous registrations,
Secure/HttpOnly cookies, login/refresh/logout, protected API remaining 401,
preflights, untrusted/null/lookalike/wrong-port origins, spoofed forwarding
headers, rejection before user/quota writes and body-secret omission from logs.
The old example's placeholder origin fails this regression fixture.

The existing HTTP smoke now registers anonymously for each public origin against
the real production launcher over HTTP, rejects an unrelated origin and checks
secure cookies/session rotation. All local DB operations use temporary databases.

Separate self-review confirmed the fix addresses the measured configuration
mismatch, CORS and CSRF use the same settings, no production trust logic is relaxed,
logging escapes and bounds untrusted header values, and neither a migration nor
an API/client-stack change is necessary. Netlify's independent 404 is documented
without claiming it was repaired. Verification results follow below.

## Verification results

- Full `.venv/bin/pytest -q`: **260 passed, 15 skipped**, 91.07 seconds.
  PostgreSQL-only checks skip without TEST_DATABASE_URL; the existing
  Starlette/httpx deprecation warning remains.
- Targeted origin suite: **9 passed**, 1.83 seconds.
- Ruff (`backend/app`, `backend/tests`, `backend/run.py`): passed.
- mypy (`app run.py` from backend): passed, **66 source files**.
- Changed backend Python formatting and `git diff --check`: passed.
- Expanded `python3 scripts/backend-stabilization-smoke.py`: passed, including
  both production registration origins, rejection, auth/reuse/password/logout,
  learning/leaderboard APIs, once-only XP and persistence across restarts.
- Public HTTP matrix above was measured against the existing live deployment
  before configuration changes. Post-fix public verification remains pending
  application of Render environment settings. No production deploy was performed.

The initial targeted pytest hung in the restricted aiosqlite sandbox and was
interrupted; the targeted/full suites and localhost smoke passed with approved
unrestricted execution. No browser/Dashboard surfaces or Render connector were
available to read/change the live environment or inspect server-side headers.
The unrelated pre-existing untracked `CSS.star4life/` directory is untouched.

## Changed files

- `.env.production.example`: explicit Render and Netlify origin allowlist.
- `backend/app/modules/auth/router.py`: safe origin rejection diagnostics only;
  trust decisions and response contract are unchanged.
- `backend/tests/test_auth_origins.py`: nine production regression cases.
- `scripts/backend-stabilization-smoke.py`: real HTTP registration matrix.
- `docs/deployment.md`: exact deployment environment and remaining Netlify step.
- `docs/render-registration-origin-403.md`: evidence, request trace and verification.
- `project-map/data-flow.md`: middleware/auth/limit flow and origin deployment rule.
- `plans/roadmap.md`, `plans/milestones.md`: completed work and external next steps.
