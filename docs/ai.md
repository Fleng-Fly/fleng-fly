# AI Layer

> Status: **design** (pre-implementation). Package: `@fleng/ai`. Consumed by the
> backend `ai` module. This is a library, not a service.

## 1. Purpose

Provide a provider-agnostic way to call language models for well-defined
learning capabilities, without leaking provider specifics into the backend, and
without an abstraction that does more than the product actually needs.

## 2. Design principles

- **One small interface.** The abstraction is a `AIProvider` with the operations
  the product uses. Do not add streaming, tools, or embeddings abstractions until
  a capability requires them.
- **Server-side only.** API keys never reach the frontend.
- **Deterministic where possible.** Prefer structured outputs (JSON schema) and
  validate them; do not parse free text when a schema will do.
- **Safe by default.** System prompts are owned by the server; user content is
  data, never instructions. See `docs/security.md`.
- **Testable.** A `mock` provider makes the whole layer testable offline.

## 3. Package shape (planned)

```
ai/
├── src/
│   ├── index.ts                # public exports
│   ├── types.ts                # AIProvider, message/result/error types
│   ├── providers/
│   │   ├── mock.provider.ts
│   │   ├── openai.provider.ts
│   │   └── anthropic.provider.ts
│   ├── registry.ts             # resolve provider from config
│   ├── prompts/                # one module per capability
│   │   ├── tutor.ts
│   │   ├── grammar.ts
│   │   ├── writing.ts
│   │   ├── speaking.ts
│   │   └── recommendations.ts
│   └── safety/                 # input/output guardrails
└── package.json
```

## 4. Interface (illustrative, not final)

```ts
export interface AIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AICompletionRequest {
  messages: AIMessage[];
  model?: string;
  temperature?: number;
  /** When set, the provider must return JSON matching this schema. */
  responseSchema?: JsonSchema;
}

export interface AICompletionResult {
  content: string;
  model: string;
  usage?: { promptTokens: number; completionTokens: number };
}

export interface AIProvider {
  readonly id: string;
  complete(request: AICompletionRequest): Promise<AICompletionResult>;
}
```

If a future capability needs streaming or embeddings, the interface is extended
then — not pre-emptively.

## 5. Capabilities and how they map to endpoints

| Capability | Endpoint | Prompt module |
| ---------- | -------- | ------------- |
| AI Tutor conversation | `POST /ai/conversations/:id/messages` | `prompts/tutor.ts` |
| Grammar explanation | `POST /ai/grammar/explain` | `prompts/grammar.ts` |
| Writing correction | `POST /ai/writing/correct` | `prompts/writing.ts` |
| Speaking feedback | (planned) | `prompts/speaking.ts` |
| Recommendations | `GET /ai/recommendations` | `prompts/recommendations.ts` |
| Exercise generation | admin/internal (planned) | `prompts/generation.ts` |

## 6. Request flow (backend `ai` module)

```
POST /ai/conversations/:id/messages
 → ownership check (conversation.userId === current user)
 → assemble context: recent messages + learner profile summary
 → safety: sanitise/limit user content, enforce token budget
 → @fleng/ai: build prompt, select provider, call complete()
 → validate output (schema) → persist AIMessage
 → return { userMessage, assistantMessage }
```

Persistence, authorization and rate limiting live in the backend module; the
library has no knowledge of Prisma or HTTP.

## 7. Configuration

| Variable | Meaning |
| -------- | ------- |
| `AI_PROVIDER` | `openai` / `anthropic` / `mock` |
| `AI_API_KEY` | Provider secret (server-side only) |
| `AI_MODEL` | Default model id |
| `AI_MAX_TOKENS` | Upper bound per request |
| `AI_REQUEST_TIMEOUT_MS` | Hard timeout |

Provider selection is config-driven so tests use `mock` and environments can
differ without code changes.

## 8. Error handling, cost and limits

- Provider errors are normalised to a small set (`AI_UNAVAILABLE`,
  `AI_TIMEOUT`, `AI_INVALID_RESPONSE`) and never leak provider payloads.
- Timeouts and retries with backoff for transient failures; no infinite retries.
- Per-user and global rate limits and a max-token budget guard cost.
- Token usage recorded in `AIMessage.metadata` for accounting/analytics.

## 9. When to extract a service

Only if one of these becomes true:

- AI needs independent scaling or a different runtime/language.
- A capability genuinely requires the Python ecosystem.
- Independent deploy cadence is required.

Until then, the library boundary is enough and keeps operations simple.

## 10. Open questions

- Streaming responses for the tutor (UX vs. complexity) — deferred.
- Embeddings / RAG over learning content — deferred until content volume needs it.
- Voice input for speaking practice and an audio-capable provider — deferred.
