# AI Layer

> Status: **not implemented**. This is the design for the AI milestone. No AI
> code or provider dependency exists yet; the backend has no AI module.

## 1. Purpose

Provide a provider-agnostic way to call language models for well-defined learning
capabilities, without leaking provider specifics into the API layer, and without
an abstraction that does more than the product actually needs.

With a Python backend, this layer is naturally a Python package inside the
backend (or a `ai/` package imported by it). It is **not** a microservice.

## 2. Design principles

- **One small interface.** The abstraction covers only the operations the product
  uses. Do not add streaming, tools or embeddings abstractions until a capability
  requires them.
- **Server-side only.** API keys never reach the frontend.
- **Deterministic where possible.** Prefer structured outputs (JSON schema) and
  validate them; do not parse free text when a schema will do.
- **Safe by default.** System prompts are owned by the server; user content is
  data, never instructions. See `docs/security.md`.
- **Testable.** A `MockProvider` makes the layer testable offline.

## 3. Package shape (planned)

```
ai/                       # or backend/app/ai/
├── __init__.py
├── types.py              # Provider protocol, message/result types
├── providers/
│   ├── mock.py
│   ├── openai.py
│   └── anthropic.py
├── registry.py           # resolve provider from Settings
├── prompts/              # one module per capability
│   ├── tutor.py
│   ├── grammar.py
│   ├── writing.py
│   ├── speaking.py
│   └── recommendations.py
└── safety.py             # input/output guardrails
```

## 4. Interface (illustrative)

```python
from typing import Protocol

class AIMessage(TypedDict):
    role: str  # "system" | "user" | "assistant"
    content: str

class AICompletionResult(TypedDict):
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int

class AIProvider(Protocol):
    id: str
    async def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AICompletionResult: ...
```

If a future capability needs streaming or embeddings, the interface is extended
then — not pre-emptively.

## 5. Capabilities and how they map to endpoints

| Capability | Endpoint | Prompt module |
| ---------- | -------- | ------------- |
| AI Tutor conversation | `POST /ai/conversations/:id/messages` | `prompts/tutor.py` |
| Grammar explanation | `POST /ai/grammar/explain` | `prompts/grammar.py` |
| Writing correction | `POST /ai/writing/correct` | `prompts/writing.py` |
| Speaking feedback | (planned) | `prompts/speaking.py` |
| Recommendations | `GET /ai/recommendations` | `prompts/recommendations.py` |
| Exercise generation | admin/internal (planned) | `prompts/generation.py` |

## 6. Request flow (backend `ai` module)

```
POST /ai/conversations/:id/messages
 → ownership check (conversation.user_id == current user)
 → assemble context: recent messages + learner profile summary
 → safety: sanitise/limit user content, enforce token budget
 → build prompt, select provider, call complete()
 → validate output (schema) → persist AIMessage
 → return { userMessage, assistantMessage }
```

Persistence, authorization and rate limiting live in the API module; the AI layer
knows nothing about HTTP or the database.

## 7. Configuration

| Variable | Meaning |
| -------- | ------- |
| `AI_PROVIDER` | `openai` / `anthropic` / `mock` |
| `AI_API_KEY` | Provider secret (server-side only) |
| `AI_MODEL` | Default model id |
| `AI_MAX_TOKENS` | Upper bound per request |
| `AI_REQUEST_TIMEOUT_SECONDS` | Hard timeout |

Provider selection is config-driven so tests use `mock` and environments can
differ without code changes. These settings do not exist in `Settings` yet.

## 8. Error handling, cost and limits

- Provider errors are normalised to a small set (`AI_UNAVAILABLE`,
  `AI_TIMEOUT`, `AI_INVALID_RESPONSE`) and never leak provider payloads.
- Timeouts and retries with backoff for transient failures; no infinite retries.
- Per-user and global rate limits and a max-token budget guard cost.
- Token usage recorded in `AIMessage.metadata` for accounting/analytics.

## 9. When to extract a service

Only if AI needs independent scaling, a different runtime, or an independent
deploy cadence. Until then it stays a module inside the FastAPI backend.

## 10. Open questions

- Streaming responses for the tutor (UX vs. complexity) — deferred.
- Embeddings / RAG over learning content — deferred until content volume needs it.
- Voice input for speaking practice and an audio-capable provider — deferred.
