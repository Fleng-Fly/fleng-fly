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

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_MAX_INPUT_CHARS` | 4000 | Chat/structured request character limit |
| `AI_MAX_RESPONSE_CHARS` | 16000 | Response content bound |
| `AI_HISTORY_MESSAGES` | 20 | Recent messages sent upstream |
| `AI_HISTORY_CHARS` | 16000 | Recent-history character budget |
| `AI_MESSAGES_PER_CONVERSATION` | 200 | Stored message cap; start a new conversation |
| `AI_CONVERSATIONS_PER_USER` | 50 | Stored conversation cap; delete old ones |
| `AI_REQUESTS_PER_MINUTE` | 10 | Persistent per-user fixed window |
| `AI_DAILY_REQUESTS` | 100 | Per-user UTC-day fixed window |
| `AI_DAILY_TOKEN_BUDGET` | 100000 | Conservative daily token reservations |
| `AI_CONCURRENCY` | 4 | Global database reservation limit and per-process bound |
| `HTTP_MAX_BODY_BYTES` | 131072 | API request body bound, including chunked bodies |

One active AI request per user across workers. PostgreSQL locks serialize quota
reservation; active leases expire after timeout + 60 seconds if a worker dies.
Reservations use prompt UTF-8 byte count plus framing allowance and maximum output
tokens. Failed calls retain reservations, since provider billing may still occur.
Provider-reported token usage/cost is stored when available, with a strict allowlist.
Usage rows expire after 30 days during subsequent requests; fixed-window counters
expire after two days. Conversation/message caps bound retained tutoring content.

The token reservation is a basic cost guard, not a currency guarantee. Configure
an OpenRouter key credit limit and a suitably priced model. Cancellation may still
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
For real PostgreSQL validation see `docs/development.md`; SQLite fixtures are
explicitly test-only and do not replace the application's database.

Manual paid integration test (requires running/migrated PostgreSQL and configured
OpenRouter key/model): register/login through `/docs`, copy the returned access
token into Authorize, then call `/api/v1/ai/chat` with `{"message":"Help me practice introductions"}`.
Verify the conversation/history endpoint, send a second turn with its ID, and
try `/explain`, `/generate-exercise` and `/chat/stream`. Verify XP is unchanged,
and verify another account cannot read/delete the conversation. Disable AI and
confirm `/ai/recommendations` still responds. This live check was not performed
in this execution environment: PostgreSQL and live credentials were unavailable.
