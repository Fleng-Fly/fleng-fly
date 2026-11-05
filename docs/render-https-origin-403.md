# Render HTTPS Origin 403 — 2026-11-05

## Proven cause and scope

The supplied Render log records Origin `https://fleng-fly.onrender.com`, Host
`fleng-fly.onrender.com`, ASGI scheme `http` and rejected register/refresh POSTs.
The auth guard constructs `http://fleng-fly.onrender.com`; it cannot equal the
HTTPS Origin. Since either an exact allowlist match or same-origin match passes,
a rejection also proves the HTTPS Origin is absent from the effective allowlist.
The previous public matrix in `render-registration-origin-403.md` independently
established that Netlify was allowed and Render was excluded. This is before
throttling/session writes, not a SQLite failure. The production example already
contains both origins, but editing a reference file does not configure Render.
The exact current dashboard variable contents/proxy peer IP are unavailable.

`backend/run.py` calls Uvicorn with proxy_headers=bool(TRUSTED_PROXY_IPS) and
forwarded_allow_ips=TRUSTED_PROXY_IPS. The default is empty. Thus forwarding is
explicitly disabled by default, including on Render, which sets the Python
FORWARDED_ALLOW_IPS environment variable to `*`. When enabled, the installed
Uvicorn middleware applies X-Forwarded-Proto only for trusted immediate peers;
it accepts recognized protocol values, ignores invalid values and does not
rewrite Host from X-Forwarded-Host or Forwarded. Tests assert actual ASGI scheme
and Host for trusted/untrusted peers. The log's HTTP scheme proves effective
scheme reconstruction did not occur, but cannot establish which proxy header
or peer address was actually received on the live service.

## Minimal fix

Settings now reads Render's server-provided RENDER_EXTERNAL_URL, validates a
nonempty value as an exact HTTPS origin (no wildcard, credentials, path, query
or fragment), and adds it once to cors_origins. Both CORSMiddleware and the
existing auth guard already use this property. Netlify stays explicitly
configured via CORS_ORIGIN. No per-request forwarding header enters the allowlist.
Auth guard, launcher proxy trust, cookies, JWT, SQLite, AI and learning logic
are unchanged; no dependency, migration or frontend change is needed.

CORS_ORIGIN accepts one string of comma-separated origins, strips surrounding
entry whitespace and drops empty entries. It is not a JSON list. Production
requires exact HTTPS origins without trailing slashes/paths. The recommended
explicit setting remains both public origins, even though Render's own URL
is now also obtained from its runtime environment.

Sources: [Render default environment variables](https://render.com/docs/environment-variables),
[Uvicorn HTTP/proxy settings](https://uvicorn.dev/settings/). Local installed
middleware source and regression tests supply the implementation evidence.

## Render checks after deploying the commit

- Start Command: `cd backend && python run.py` from repository root, or
  `python run.py` if the configured Root Directory is already backend.
- APP_ENV=production; retain the existing JWT_ACCESS_SECRET and DATABASE_URL.
- CORS_ORIGIN=`https://fleng-fly.onrender.com,https://fleng.netlify.app`.
- Confirm automatic RENDER_EXTERNAL_URL=`https://fleng-fly.onrender.com`.
- COOKIE_SECURE=true, COOKIE_SAMESITE=lax; let Render supply PORT.
- TRUSTED_PROXY_IPS may stay empty for this fix. To reconstruct scheme/client IP,
  use only verified immediate ingress IPs/networks, restrict upstream access and
  ensure ingress overwrites forwarding headers. Do not copy platform wildcard
  FORWARDED_ALLOW_IPS into TRUSTED_PROXY_IPS. No actual peer IP is assumed here.
- Deploy/restart (Settings is cached); verify the deployed commit, anonymous
  Render registration, login and refresh rotation over HTTPS. Check both exact
  origins' preflights succeed and unrelated/null/lookalike origins are rejected.

No deployment/push or dashboard mutation was performed. Local production smoke
checks use actual Uvicorn HTTP behind modeled TLS termination and temporary
SQLite, with explicit Secure cookie transmission; they do not establish live
HTTPS browser behavior. Netlify UI API proxy configuration remains a separate
existing deployment requirement; accepting its Origin does not enable that proxy.

## Review and verification

Separate self-review checked the trust boundary, shared CORS/CSRF settings,
validation, deduplication, absence of header-derived allowlisting, no database
changes and regression coverage against the actual Uvicorn middleware. Rejected
origins remain 403 before writes. The real production smoke uses Netlify-only
CORS plus automatic Render URL and the platform wildcard environment default,
with launcher proxy processing still disabled. Both trusted origins register;
Render login/refresh, protected Dashboard/Lessons, once-only XP and persistence
across process restarts pass.

The first full run had 288 passed, 15 skipped and one AI capacity test
failure (MissingGreenlet on lazy user.profile access). The isolated test passed
on both HEAD and the modified code. A repeat full run reproduced the failure;
its test setup now explicitly eager-loads the profile, matching the production
auth dependency. No production AI behavior was changed. This avoids depending
on an ORM relationship surviving in the identity map. Final results follow below. The restricted
aiosqlite run stalled and was interrupted; SQLite tests and HTTP smoke were run
with approved execution outside the sandbox, as in the existing project reports.
The pre-existing untracked CSS.star4life directory is untouched.

## Changed files

- `backend/app/core/config.py`: validated runtime Render origin and shared merge.
- `backend/tests/test_auth_origins.py`: both configuration modes, session flows,
  preflight/rejection and real Uvicorn proxy regressions.
- `backend/tests/test_production.py`: Render URL validation, config parsing and
  launcher trust overriding the platform wildcard default.
- `backend/tests/test_ai_security.py`: explicit profile load in capacity test setup.
- `scripts/backend-stabilization-smoke.py`: actual launcher with Render runtime env.
- `.env.production.example`: automatic Render URL behavior explained.
- `docs/authentication.md`, `docs/deployment.md`, this report and the previous
  Origin report: effective allowlist, evidence and deployment instructions.
- `project-map/data-flow.md`, `plans/roadmap.md`, `plans/milestones.md`: current
  config flow, local completion and pending public deployment validation.

## Final check results

- Full `.venv/bin/pytest -q`: **289 passed, 15 skipped**, 95.70 seconds.
  PostgreSQL-only cases skip without TEST_DATABASE_URL; the existing
  Starlette/httpx deprecation warning remains. An earlier rerun was interrupted
  after reproducing the AI setup failure, before its explicit-profile-load fix.
- Targeted origin/production suite before the AI setup fix: **48 passed**.
- Ruff (`app`, `tests`, `run.py`), changed Python formatting and
  `git diff --check`: passed.
- mypy (`app run.py`): passed, **66 source files**.
- `python3 scripts/backend-stabilization-smoke.py`: passed, including the real
  production launcher, both origins, login/refresh, Secure/HttpOnly cookie,
  readiness, learning/leaderboard APIs and restart persistence on temporary DB.
- Public post-deploy Render HTTPS/browser validation: pending deployment.
