# Global Fleng AI and OpenRouter audit — 2026-11-04

## Result

One existing assistant is mounted by `workspace.setWorkspaceUser()` after session
resolution on Dashboard, Courses Catalog, Course Details, Lessons, Leaderboard
and Settings. No other protected HTML pages exist in this checkout. Dashboard
and Lessons no longer mount their own copy. Lessons registers an ID-only context
callback; other pages use general mode. Course IDs are not sent because the AI
contract does not support course context.

Landing, Login and Register do not initialize the assistant. There is no password
reset frontend page in this checkout; its existing authenticated/guest API paths
were not changed and no public AI endpoint was introduced.

## Findings and fixes

1. Widget lifecycle did not explicitly clear private state on logout/account
   switch. Destruction now empties messages/drafts, clears the current user's
   selected conversation ID on session termination, aborts streaming and removes
   listeners/UI/styles. Logout sends a storage notification to other tabs. A
   different user gets a fresh instance. Navigation destroys UI while retaining
   only the user-scoped selected conversation ID; backend-owned history restores
   it on the next page. Cached documents revalidate the session before restoring AI.
2. AI request models silently ignored extra fields. Chat, explain and generation
   now reject extra fields (422), including user IDs, models, arbitrary context,
   system prompts and message arrays. Normal user text remains untrusted model
   input, not a system-role message. Prompt injection cannot be ruled out by a
   persona alone; the model has no tools or permission to mutate learning state.
3. Assembled prompts had character/history/daily-budget bounds but no independent
   per-request input-token ceiling. `AI_MAX_INPUT_TOKENS=24000` now limits a
   conservative UTF-8 byte upper bound plus message framing, before provider I/O.
4. Unexpected transport exceptions could reach the generic traceback logger.
   The OpenRouter adapter now converts them to a generic unavailable error.
   Provider HTTP bodies and exception strings never enter responses. SSE also
   enforces output length before forwarding each delta.
5. OpenRouter URL validation now rejects password-bearing userinfo even when
   the username is empty. Provider URLs require HTTPS, without query/fragment;
   redirects remain disabled.

## VERIFIED

- Full pytest: **228 passed, 15 skipped**; one existing Starlette/httpx warning.
  The 44 new security cases use mock OpenRouter; no paid requests.
- Ruff and mypy pass (64 application source files). All frontend JS syntax
  checks and `git diff --check` pass.
- JS/DOM tests: **10 widget + 6 course + 7 SSE parser + 3 API client = 26 passed**.
  Widget tests execute production widget and workspace initialization with a
  minimal DOM, including singleton behavior for all six page scripts, open/
  minimize/close, streaming, history restore, XSS strings, logout cancellation,
  subsequent-account isolation, disabled AI and network errors without retries.
- Artificial secret-marker tests cover normal JSON, SSE, status, saved history,
  usage filtering, provider HTTP bodies, unexpected exceptions and captured logs.
  Authorization is added only to server-to-provider requests. Usage is numeric
  allowlisted data; the frontend calls same-origin `/api/v1` only.
- `scripts/audit-ai-secrets.py`: no concrete OpenRouter key findings across
  tracked working files, Git index, frontend files and discovered application log
  files. It compares known local environment-file values in memory and checks a
  key-format pattern, printing locations/counts only. Empty env examples contain
  no key values. Docker Compose runs only local PostgreSQL; Procfile uses Python.
- All AI route families require JWT: status, chat, streaming, conversations/list/
  history/delete, explain, generate-exercise and recommendations. Existing and
  new tests verify owner isolation for reads/writes/deletion, request deduplication,
  safe published lesson context and absence of official answer keys.
- Existing persistent limits are retained: 10 requests/minute, 100/day,
  100000 reserved tokens/day, one active generation per user and four globally
  across workers. Reservations coordinate via existing database locks/rows.
  Defaults also bound messages (4000 chars), output (800 tokens / 16000 chars),
  history (20 messages / 16000 chars), conversations (50/user), conversation size
  (200 messages), history pages (100 maximum) and request time (30 seconds).
  Failed/cancelled requests retain budget reservations; duplicate request IDs
  cannot be charged again during the 30-day usage-retention window. Closing or
  minimizing keeps an on-page generation running; logout/navigation cancels it.
- Cancellation/timeout/lease cleanup tests and shared chat/stream quota tests pass.
  No frontend disabled button is relied upon as the security boundary.
- `npm run dev` and real HTTP smoke pass with isolated SQLite: courses/assets,
  auth, read-only progress, lesson submissions, once-only XP, restart persistence,
  production launcher, Secure/HttpOnly cookies and origin checks. Existing local
  SQLite is not deleted or reset.
- Production config requires exact HTTPS CORS origins, a strong JWT secret and
  Secure cookies. Refresh cookies are HttpOnly, host-only, SameSite=Lax by default.
  Proxy trust defaults to disabled; deployments must supply actual ingress IPs,
  never a wildcard. These existing production safeguards were not weakened.

## NOT VERIFIED / deployment decision

Computer-use inventory has no browser or apps. Actual rendering/interaction at
360/768/desktop, drawer overlap, virtual keyboards, browser cache transitions and
cross-tab storage behavior are NOT VERIFIED beyond DOM/static checks.

Live OpenRouter streaming/billing/model compatibility, production logs, HTTPS
termination/proxy buffering/trust, hosted CORS/cookie behavior and live PostgreSQL
multi-worker contention are NOT VERIFIED. Fifteen PostgreSQL tests skip without
a configured TEST_DATABASE_URL. Local log scanning and mocked captured logs do
not establish anything about external hosting logs.

Existing access JWTs can remain valid until expiry (default 15 minutes) after
logout/password changes; refresh sessions are revoked. This audit improves UI
cleanup and does not add access-token revocation infrastructure. User-scoped
conversation IDs are not message caches or authorization credentials; backend
ownership checks remain mandatory even if storage is modified by the client.

The implementation is ready for review and deployment preparation, but public
AI deployment is not certified ready until host/database/browser checks and an
explicitly authorized real-provider smoke are completed. Keep AI disabled until
server secrets, chosen model, limits and provider spending caps are configured.

## Independent self-review

Rechecked auth ownership filters, request schemas, lesson publication checks,
reservation/cleanup paths, SSE framing, secret-error paths, safe DOM text rendering,
account-switch races, user-scoped storage, unchanged guest pages and existing
course/lesson flows. Incoming course changes were preserved. No new backend,
framework, billing subsystem, database schema or migration was introduced.
