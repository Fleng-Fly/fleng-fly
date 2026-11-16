# Fleng AI assistant integration — 2026-11-01

## Before this change

The existing FastAPI AI module already implemented an async OpenRouter adapter,
ordinary chat, SSE, explanations, generated practice, owned conversation history
and deletion. `AIConversation`, `AIMessage` and `AIUsage` already existed.
Authentication used the existing JWT dependency. Published lesson theory, profile
CEFR/language and bounded learning analytics formed the prompt. Persistent request,
daily-token and concurrency limits, deadlines and sanitized provider errors were
already present. The frontend did not expose a working floating assistant.

There is no `backend/app/modules/lessons/` directory in this repository. Catalog
reads are in `modules/catalog`; lesson start/submit/progress and grading are in
`modules/exercises`, with aggregates in `modules/progress`. These were audited and
reused; no duplicate lesson or AI module was introduced.

## Result and API path

Authenticated Dashboard/Lessons mount one shared compact Fleng AI widget.
`GET /api/v1/ai/status` reports configuration readiness without calling OpenRouter.
`GET /ai/conversations` and `GET /ai/conversations/{id}` load user-owned history.
`POST /ai/chat/stream` runs the actual backend/OpenRouter path; `/ai/chat` remains
available for non-streaming consumers. The first successful turn creates its
conversation; subsequent turns supply `conversationId`. No invented model answers
or frontend provider credentials are used.

Lessons sends only the current `lessonId` and, in Practice/Test, `exerciseId`.
The backend loads publication-checked lesson/course data, bounded theory, lesson
level and the JWT user's progress status. Exercise type/prompt are loaded only
when the exercise belongs to that published lesson. Unknown or unavailable chat
context is omitted. No answer keys/model answers, arbitrary frontend context,
other users' private records, names, email or auth data enter this context.
Structured explanations retain strict published-lesson validation.

The persona gives clear English-learning explanations in the learner's preferred
language, adapts to CEFR, starts exercise help with hints and acknowledges
uncertainty. Only existing grading manages XP and official progress; AI has no
mutation tools.

## Streaming, persistence and lifecycle

The existing OpenRouter transport yields SSE deltas. Backend emits UTF-8
`delta`, then atomically saves a complete user/assistant pair and emits `done`.
Failures emit sanitized `error`; partial responses never become saved history.
Malformed provider response shapes now also return controlled errors.

The browser uses authenticated fetch and an incremental UTF-8 SSE decoder that
handles arbitrary byte/chunk boundaries, CRLF and multiline data. Text uses
`textContent`. `done` replaces provisional text with the saved response, avoiding
double appends. History is paginated and conversations can be selected or started
fresh. Local storage holds only a user-scoped selected conversation ID.

Close/minimize hides the panel while an active request keeps running on the
current page. Reopening preserves its current state. Sending/history changes are
blocked during a request. Navigation/reload disconnects the stream; backend
cancels the provider and cleans up the active lease. A completed pair committed
just before a lost connection can be recovered from history. Ambiguous errors
block further sending until Reload/history recovery or an explicit new chat.

Optional `requestId` is reserved in existing AIUsage before provider I/O. Migration
`20261101_1200` adds a nullable UUID and a per-user unique index. Replays across
ordinary/streaming routes return `409 AI_REQUEST_DUPLICATE`, including previously
failed identified requests, without another provider call. This protection lasts
for the 30-day usage retention window. Clients that omit the field retain the old
contract. No automatic network/provider retry was introduced; the existing single
401 refresh occurs before authorized generation.

The dark/purple widget includes new chat, conversation selector, Reload, composer,
loading/generating/error/unavailable indicators, minimize and close. Enter sends,
Shift+Enter adds a line, Escape closes, focus stays visible. CSS supports compact
desktop and small screens; visualViewport adjusts for keyboard height and hides
secondary controls when screen space contracts. Reduced motion is respected.
Actual browser and mobile layout validation remains pending.

## Changed files

- Runtime/config docs: `.env.example`, `README.md`.
- Backend: `backend/app/db/models.py`,
  `backend/app/modules/ai/{context,prompts,provider,router,schemas,service}.py`.
- Migration: `backend/alembic/versions/20261101_1200_ai_request_id.py`.
- Frontend: `frontend/js/{api,ai-assistant,ai-stream,dashboard,lesson}.js`,
  `frontend/css/ai-assistant.css`.
- Tests: `backend/tests/{test_ai,test_ai_provider,test_sqlite_local,test_postgres_migrations}.py`,
  `scripts/test-ai-stream.mjs`, `scripts/test-ai-api.mjs`.
- Documentation: `docs/{ai,api,database,frontend,ai-assistant-integration}.md`,
  `project-map/{modules,api-map,data-flow}.md`,
  `plans/{ai-plan,roadmap,milestones}.md`.

## Verified

- `npm run backend:test`: **169 passed, 15 skipped**, one existing
  Starlette/httpx deprecation warning. PostgreSQL tests skip without
  `TEST_DATABASE_URL`. SQLite tests required execution outside the restricted
  sandbox because aiosqlite hung inside it, as already documented by this project.
- Mocked provider/API regressions: disabled AI/missing key, ordinary success,
  streaming, timeout, upstream 429/5xx, malformed output, disconnect and task
  cancellation, atomic persistence, isolation/unknown conversations, lesson
  publication/context filtering, rate/budget/history limits and request deduplication.
- `npm run backend:lint`: passed.
- `npm run backend:typecheck`: passed (64 source files).
- Syntax checks for all `frontend/js/*.js`: passed.
- `node scripts/test-ai-stream.mjs`: **7 passed**; UTF-8, CRLF/chunk framing,
  multiline JSON, truncated/error/malformed events.
- `node scripts/test-ai-api.mjs`: **3 passed**; raw streaming after auth refresh,
  no network/provider auto-retry.
- Alembic: one head `20261101_1200`; fresh SQLite preparation and `alembic check`
  show no schema drift; SQLite and PostgreSQL offline upgrade SQL compile.
- `python3 scripts/backend-stabilization-smoke.py`: passed. Starts `npm run dev`
  with temporary SQLite, applies migrations, exercises auth/Dashboard/Lessons APIs,
  once-only XP and persistence across restart. Existing application data is untouched.
- `git diff --check`: passed. Initial working tree was clean; no existing
  uncommitted changes were overwritten. No commits or pushes were created.
- Separate self-review checked ownership, context secrets, paid retries, cleanup,
  stream framing, XSS surfaces and focus behavior. Fixed malformed response shapes,
  ambiguous-response recovery and focus loss/stealing found during that review.

## Not verified / next manual checks

No browsers were available in the computer-use tool inventory. Therefore actual
open/minimize/close/send/reopen/new-chat interaction, XSS behavior in a browser,
visual appearance at **360/768/desktop**, and real virtual-keyboard behavior have
**not** been browser-tested. Backend/static/parser checks are not a substitute.

No paid OpenRouter calls or live PostgreSQL integration were performed. Actual
provider/model availability, billing and production proxy buffering remain manual
integration checks. The code path is real; automated responses come only from
explicit test mocks.

## Enable real OpenRouter

Configure the ignored root or backend `.env` with:

```dotenv
AI_ENABLED=true
OPENROUTER_API_KEY=<real backend-only key>
OPENROUTER_MODEL=<valid provider/model-id>
```

Then run/restart `npm run dev`; local SQLite migrations apply automatically.
For PostgreSQL, migrate explicitly with `npm run db:migrate`. Log in, open Fleng AI
on Dashboard, send a grammar question, then try a lesson hint and reload history.
Confirm incremental text, persistence, provider-error UX and unchanged XP. Test a
second account for isolation. With AI disabled or a missing key/model, the app
still starts and history remains accessible with generation unavailable.
