# AI Plan

> Aligns with `plans/roadmap.md` Stage 5. Durable design: `docs/ai.md`.
> Guardrails: `docs/security.md`.

## Principles

- Provider-agnostic, but only as abstract as the current capabilities require.
- Server-side only; keys never reach the browser.
- Structured, validated outputs over free-form text where possible.
- Testable offline through a `mock` provider.

## Phase 1 — Library skeleton

- [ ] `@fleng/ai` package with `types.ts` (`AIProvider`, message/result types).
- [ ] `mock` provider (deterministic, used in all tests).
- [ ] `registry.ts` resolving provider from `AI_PROVIDER` config.
- [ ] Unit tests for registry + mock.

## Phase 2 — First real provider

- [ ] Implement one provider (e.g. OpenAI) behind the interface.
- [ ] Timeouts, retries with backoff, normalized errors
      (`AI_UNAVAILABLE`, `AI_TIMEOUT`, `AI_INVALID_RESPONSE`).
- [ ] Token-usage capture into result metadata.
- [ ] Keep the second provider unimplemented until needed (avoid dead code).

## Phase 3 — Backend `ai` module

- [ ] Prisma models `AIConversation`, `AIMessage`.
- [ ] Endpoints from `docs/api.md §2.9`: conversations, messages, writing
      correction, grammar explanation.
- [ ] Ownership checks, per-user rate limits, max-token budget.
- [ ] Persist normalised content (not raw provider payloads).

## Phase 4 — Prompt modules & structured output

- [ ] `prompts/tutor.ts`, `grammar.ts`, `writing.ts`.
- [ ] JSON-schema outputs for correction/recommendations, validated before use.
- [ ] Prompt-injection guardrails: server-owned system prompt, delimited user
      content, no tool execution from model output.

## Phase 5 — Personalisation

- [ ] Learner context assembly (profile + recent progress) with a token budget.
- [ ] `recommendations` module: rule-based first, AI-assisted later.
- [ ] Cache/avoid repeated expensive calls for identical recommendation requests.

## Explicitly deferred

- Streaming responses.
- Embeddings / RAG over learning content.
- Voice/audio provider integration for speaking feedback.
- Exercise generation (admin tooling).
- Extracting a separate AI service (conditions in `docs/ai.md §9`).

## Risks / watch-items

- Cost control: rate limits + token budgets from the first AI endpoint.
- Prompt injection: cover with tests using adversarial inputs.
- Provider lock-in: keep provider-specific code inside `providers/` only.
- Failure UX: AI must degrade gracefully (clear error, retry), never block core
  learning flows.
