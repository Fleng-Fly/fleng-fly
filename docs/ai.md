# AI tutoring backend

Implemented inside the existing FastAPI monolith at `backend/app/modules/ai/`.
`provider.py` owns OpenRouter HTTP calls; `service.py` owns quotas and persistence;
`context.py` builds deterministic learning analytics; `prompts.py` separates trusted
instructions from untrusted learner/catalog/history text. No separate AI service.

## Setup

Set these in the root `.env` (never in frontend code):

```dotenv
AI_ENABLED=true
OPENROUTER_API_KEY=your-server-side-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=provider/model-id
AI_MAX_OUTPUT_TOKENS=800
AI_REQUEST_TIMEOUT=30
```

AI defaults to disabled. Enabling without a key/model returns `503 AI_UNAVAILABLE`.
Use an actual model ID from OpenRouter; model syntax is validated locally, model
availability is checked by the provider at request time. No live/paid requests run
on startup or in tests. Key values use Pydantic SecretStr.

`AI_STRUCTURED_OUTPUTS=false` by default. Enable only for a model/provider that
supports JSON Schema. With it disabled, the system prompt requests JSON and
Pydantic still validates every result. With it enabled, the request also includes
`response_format: json_schema`, all fields required and extra properties forbidden.
No tools, function calling, web access or provider-dependent advanced features
are required. Do not enable automatic model routing to a more expensive model.

References: [OpenRouter streaming](https://openrouter.ai/docs/api/reference/streaming)
and [structured output support](https://openrouter.ai/docs/guides/features/structured-outputs).

## API (all require Bearer authentication)

All paths below use `/api/v1/ai`:

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/chat` | Tutor turn; creates a conversation on first successful response |
| POST | `/chat/stream` | Same input, incremental SSE output |
| GET | `/conversations?limit=20&offset=0` | Own conversations |
| GET | `/conversations/{id}?limit=50&offset=0` | Own messages, chronological |
| DELETE | `/conversations/{id}` | Delete own conversation and messages |
| POST | `/explain` | Grammar help, never changes grading/XP |
| POST | `/generate-exercise` | Validated, untrusted practice exercise; no XP |
| GET | `/recommendations` | Deterministic recommendations; works with AI disabled |

```json
{"message":"I goes to school. Can you help?","correctGrammar":true}
```

Optional chat fields: `conversationId`, `lessonId`. Level and preferred language
come from `PATCH /api/v1/users/me` (`englishLevel`: A1–C2,
`preferredLanguage`: bounded text). Numeric profile `level` remains the existing
gamification level and cannot be set by AI or users.

Chat response:

```json
{"conversationId":"<uuid>","message":{"id":"<uuid>","role":"assistant","content":"Use ‘I go’...","model":"provider/model-id","usage":{"total_tokens":100},"createdAt":"2026-10-18T12:00:00Z"}}
```

Explanation request:

```json
{"exerciseId":"<uuid>","studentAnswer":"She are ready","topic":"subject-verb agreement"}
```

`exerciseId` and `lessonId` are optional; published lesson context is checked.
Official exercise prompts may be sent to the provider; answer keys are excluded.
Response contains `explanation`, `correctExample`, `rule`, `hint`.

Generation request:

```json
{"level":"A2","topic":"present simple","difficulty":"easy","exerciseType":"multiple_choice"}
```

Types: `multiple_choice`, `fill_blank`, `sentence_correction`. Response contains
`type`, `prompt`, `options`, `answer`, `explanation`, `practiceOnly:true`.
Answer must match a unique multiple-choice option; blanks require `___`;
free-text exercises must not contain options. Invalid JSON, incomplete generation
or mismatched types return `502 AI_INVALID_RESPONSE`. Practice answers are visible
for self-study and never inserted into official Exercise/grading tables. Schema
validation cannot establish pedagogical truth: generated content can be wrong.

## Persistence and trust

Only complete user/assistant pairs are saved, atomically after a successful turn.
Failures/disconnections leave the prior conversation intact. History is user-owned;
access to another user's conversation returns 404. Saved roles are constrained to
user/assistant; no caller can create system messages. Learner context excludes
names, email, credentials and official answer keys. Current level, last activity,
last ten completed lessons, up to five missed lesson topics and ten unlearned words
are included. Mistake analytics use the latest persisted submission per exercise,
not a full attempt log; lesson titles serve as topic labels.

All catalog/profile text and saved messages remain untrusted prompt data. Only
static application instructions occupy the system role. This reduces prompt
injection risk, but cannot guarantee model compliance. The model has no database
tools and no privileged mutation path, so tutoring text cannot award XP or alter
profiles, achievements or official learning completion.

## Limits and accounting

**Deprecated variables (ignored since migration `20261116_1200`; the settings
loader drops unknown keys, so old values silently have no effect):**
`AI_MAX_INPUT_CHARS` → `AI_MAX_MESSAGE_LENGTH` (default now 500);
`AI_DAILY_REQUESTS` → `AI_DAILY_USER_LIMIT` (default now 30).


| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_MAX_MESSAGE_LENGTH` | 500 | Learner-authored text per request (chat message, explain answer, topic) |
| `AI_MAX_OUTPUT_TOKENS` | 800 | Sent as `max_tokens`; also the reserved output size |
| `AI_MAX_RESPONSE_CHARS` | 16000 | Response content bound |
| `AI_HISTORY_MESSAGES` | 20 | Recent messages sent upstream |
| `AI_HISTORY_CHARS` | 16000 | Recent-history character budget |
| `AI_MESSAGES_PER_CONVERSATION` | 200 | Stored message cap; start a new conversation |
| `AI_CONVERSATIONS_PER_USER` | 50 | Stored conversation cap; delete old ones |
| `AI_REQUESTS_PER_MINUTE` | 10 | Persistent per-user fixed window |
| `AI_DAILY_USER_LIMIT` | 30 | Per-user requests per UTC day (all AI endpoints); resets 00:00 UTC |
| `AI_MAX_CONCURRENT_REQUESTS` | 1 | Per-user in-flight provider requests, across workers |
| `AI_DAILY_BUDGET_USD` | 1.00 | Global OpenRouter spend per UTC day, across workers |
| `AI_INPUT_PRICE_PER_MTOK_USD` / `AI_OUTPUT_PRICE_PER_MTOK_USD` | unset | Model tariff (USD per million tokens). **Required**: unset keeps AI unavailable |
| `AI_DAILY_TOKEN_BUDGET` | 750000 | Per-user worst-case token reservations per UTC day (30 × 24 800, so it never pre-empts the 30-message quota) |
| `AI_CONCURRENCY` | 4 | Global database reservation limit and per-process bound |
| `HTTP_MAX_BODY_BYTES` | 131072 | API request body bound, including chunked bodies |

### Daily quota and budget (server-enforced)

`reserve()` runs in one transaction holding the learner row lock, then the global
`ai:capacity` row lock, so quotas, the per-user lease and the budget hold across
processes and restarts (state lives in `ai_usage`; PostgreSQL row locks, SQLite
write lock). Checks, in order: duplicate `requestId`, per-user concurrency,
per-user daily count (UTC day), global concurrency, per-minute window, input
size, per-user token budget, then the global budget.

Before the provider call a worst-case cost is held: prompt UTF-8 bytes (+ framing,
+ the JSON schema when structured outputs are on) at the input tariff plus
`AI_MAX_OUTPUT_TOKENS` at the output tariff. Settlement: provider `usage.cost`
(credits = USD) → else provider token counts × tariff → else the hold stays as the
charge. Unsettled holds count toward the budget even after their lease expires.
Settlement states (`cost_source`): `provider`, `tariff`, `reserved` (hold kept),
`released` (cost 0) and `refused`. `released` applies only when nothing reached
OpenRouter: pre-send failure, connection refused, or local capacity rejection.
`refused` (OpenRouter 4xx/429) frees the output part but keeps the prompt cost,
because OpenRouter states that prompt processing may be charged even when no
content is generated. Both are excluded from the learner's daily count. Timeouts,
5xx, broken or cancelled SSE and invalid bodies keep the full hold (only some
providers stop billing on stream cancellation, per OpenRouter's docs).

The request carries `provider.max_price` (tariff, `request: 0`). OpenRouter writes
its example as `<= $1/m` prompt tokens; we read `/m` as USD per million tokens, and
the units of `request` and the error returned when no endpoint matches are not
documented. `usage.cost` is "in credits"; credits = USD is our assumption. The
Chat Completions stream sends `usage` in a final chunk before `[DONE]`; if it is
missing the hold stays as the charge. Reasoning tokens share `max_tokens` on most
providers (not all), so the 800-token output bound is documentation-based. `openrouter/*` auto-routers and `:online`
models are refused: their price cannot be bounded in advance. Learner-facing
errors: `AI_DAILY_LIMIT`, `AI_BUDGET_LIMIT` (no amounts disclosed), `AI_BUSY`,
`AI_INPUT_LIMIT`.

Active leases expire after timeout + 60 seconds if a worker dies. Usage rows
expire after 30 days; fixed-window counters after two days.

The USD budget is bounded by the declared tariff; a wrong tariff breaks the bound.
Also set an OpenRouter key credit limit as a backstop. Cancellation may still
be billed by some providers. No automatic paid retries occur. Upstream 429, HTTP
errors, malformed output and timeouts produce sanitized errors, with no provider
body, key or stack trace exposed. SMTP/AI secrets must not be logged.

## Streaming

Use authenticated `fetch` POST and an SSE parser (EventSource cannot POST with a
Bearer header). Events use `event: <name>\ndata: <JSON>\n\n`:

- `delta`: `{ "content": "..." }` as text arrives.
- `done`: full ChatResponse; persisted turn is complete.
- `error`: sanitized code/message; discard provisional text or allow a retry.

The provider parser ignores comments, handles multiline data frames, checks
finish_reason and requires `[DONE]`. Missing completion, upstream errors, length
truncation, deadline or disconnect never become a completed stored assistant turn.
Client disconnect cancels upstream iteration; accounting cleanup is shielded.
Headers disable proxy buffering and caching. Disable proxy buffering explicitly
when deploying behind a proxy. Ordinary preflight validation uses HTTP errors;
after streaming starts errors are SSE events with HTTP 200. The non-streaming
fallback is `POST /api/v1/ai/chat` with the identical request body.

## Testing and manual verification

```bash
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check app tests
.venv/bin/mypy app
```

Tests mock HTTP and provider responses: no API key or real AI calls required.
SQLite is the local application default and is also used by isolated tests.
For optional live PostgreSQL validation see `docs/development.md`.

Manual paid integration test (requires a running/migrated SQLite or PostgreSQL database and configured
OpenRouter key/model): register/login through `/docs`, copy the returned access
token into Authorize, then call `/api/v1/ai/chat` with `{"message":"Help me practice introductions"}`.
Verify the conversation/history endpoint, send a second turn with its ID, and
try `/explain`, `/generate-exercise` and `/chat/stream`. Verify XP is unchanged,
and verify another account cannot read/delete the conversation. Disable AI and
confirm `/ai/recommendations` still responds. This live check was not performed
in this execution environment: PostgreSQL and live credentials were unavailable.


## Floating learning assistant — 2026-11-01

Dashboard and Lessons mount `frontend/js/ai-assistant.js` after authentication.
The shared component loads `/css/ai-assistant.css`; no frontend build or new
runtime dependency is required. It supports open/minimize/close, new conversation,
conversation selection, paginated chronological history, Reload, and incremental
plain-text responses. Static welcome copy is separate from model messages.

`GET /api/v1/ai/status` requires authentication and returns
`{available, maxInputChars}`. Availability means server configuration is ready;
it does not probe provider health or bill the provider. History remains readable
when generation is disabled. Provider failures update the widget without exposing
configuration details.

Chat accepts optional `exerciseId` and `requestId` UUIDs in addition to `lessonId`
and `conversationId`. Lessons supplies only the loaded lesson/current exercise
identifiers (exercise only in Practice/Test). Backend loads published lesson and
course data, bounded theory, CEFR level and this user's lesson status. Unknown or
unpublished chat lesson context is omitted; general tutoring continues. Exercise
context must belong to that published lesson and contains only type/prompt.
Structured `/explain` retains strict 404 validation for unavailable lessons.
Answer keys, model answers and private data from other learners are excluded.
The tutor is instructed to give hints first and acknowledge uncertainty; it has
no tools or path to change XP, official grading or progress.

The widget sends a fresh `requestId` per explicit submission. `AIUsage.request_id`
and its unique `(user_id, request_id)` index prevent a repeated identified request
from reaching OpenRouter, across both chat routes and worker restarts. Replays
return `409 AI_REQUEST_DUPLICATE`, including failed/unknown requests, to avoid a
second charge. IDs live with usage rows (30-day retention); older API clients may
omit the field. Migration: `20261101_1200`. No second chat table was added.

`apiFetch` returns a raw Response for streaming, retaining the existing single
401 refresh path. It never retries provider/network failures. `ai-stream.js`
uses a streaming UTF-8 decoder, handles byte/chunk/CRLF boundaries and multiline
SSE data, and requires terminal `done` or `error`. Delta text is provisional;
`done` replaces it with the saved response instead of appending it twice.
After ambiguous failure, sending is disabled until history is reloaded or an
explicit new chat is chosen. Only server-confirmed complete pairs are history.

Closing or minimizing keeps the active fetch running on the current page. Opening
again shows its current text; another submission/history switch is disabled until
it finishes. Leaving/reloading the page disconnects and cancels upstream work;
partial turns are not saved. If the server committed just before disconnect,
Reload/history recovers that completed pair. Failed/cancelled accounting retains
the conservative reservation, since provider costs cannot be undone.

Only a user-scoped selected conversation ID is stored locally; message content
and tokens are not. Both user/model output use `textContent`, with no Markdown,
HTML execution or generated links. The nonmodal window has labelled controls,
visible focus, Escape-to-close, 44px buttons, small-screen CSS, visualViewport
keyboard adjustments and reduced-motion support. These layout choices require
browser QA on actual devices; static/parser tests do not establish visual quality.

Checks: `node scripts/test-ai-stream.mjs`, `node scripts/test-ai-api.mjs`,
backend pytest/Ruff/mypy,
JS syntax and Alembic checks. See [integration report](ai-assistant-integration.md)
for evidence and remaining manual validation.

## Admission and settlement correction — 2026-11-16

Chat, streaming, explanation and exercise generation reserve persistent capacity
and budget before entering the process-local provider capacity guard. Database
lock waiters no longer occupy local provider slots. A local admission refusal
releases its reservation without consuming the daily quota or charging a provider
call. Provider uncertainty, actual costs, per-user/global limits and timeouts keep
the existing policy. Refusal settlement uses a portable SQL CASE expression to
subtract the output hold with a zero floor on SQLite and PostgreSQL.

## "I don't understand" exercise help — 2026-11-18

Every lesson exercise has an **I don't understand / Не зрозуміло?** button. It opens the
existing floating Fleng AI panel (no second chatbot) and sends a starter message in the
interface language. The panel shows which question is being discussed and a *Back to the
exercise* button; closing it returns focus to the exercise. The lesson page is not
re-rendered, so the learner's draft answer and progress stay as they were.

Request: the normal `POST /ai/chat` or `/ai/chat/stream` with `lessonId`, `exerciseId` and the
optional `currentAnswer` (the unsent draft; validated against `AI_MAX_MESSAGE_LENGTH` like any
learner text). The browser sends IDs and the draft only; the server builds the context:

| Context | Source |
| ------- | ------ |
| Learner level, preferred language | profile (no name or email) |
| Course id/title, lesson id/title/summary/theory | published catalog only |
| Exercise id, position, type, instruction, prompt, option texts | `exercises` row of *that* lesson |
| Current answer, attempts, last checked answer and result | request draft + own submission; choice ids are turned into option text |

Answer keys (`correct_option_id`, `accepted_answers`, `model_answer`) and the authored
explanation are never included. When an exercise is in context the system prompt adds
teaching rules: explain the task, unknown words and the grammar point, give new examples
and a step-by-step hint, and do not give the final answer in the first reply. An exercise
from another lesson, or an unpublished lesson, falls back to general tutoring.

All existing controls apply unchanged (per-minute and per-day quotas, concurrency, token
reservation, global USD budget, history limits). When AI is disabled the panel says so and
nothing is sent. Tests: `backend/tests/test_ai_exercise_help.py`,
`scripts/test-ai-widget.mjs`, `scripts/test-courses.mjs`.
