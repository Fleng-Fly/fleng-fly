# AI Plan

> Aligns with `plans/roadmap.md` (AI milestone). Durable design: `docs/ai.md`.
> Guardrails: `docs/security.md`. Legend: ⬜ next · 🔴 planned.

## Principles

- Provider-agnostic, but only as abstract as the current capabilities require.
- Server-side only; keys never reach the browser.
- Structured, validated outputs over free-form text where possible.
- Testable offline through a `mock` provider.

## Phase 1 — Layer skeleton 🔴

- [ ] AI package (`ai/` or `backend/app/ai/`) with `types.py` (provider protocol,
      message/result types).
- [ ] `MockProvider` (deterministic, used in all tests).
- [ ] `registry.py` resolving the provider from `Settings`.
- [ ] Unit tests for registry + mock.

## Phase 2 — First real provider 🔴

- [ ] Implement one provider (e.g. OpenAI) behind the protocol.
- [ ] Timeouts, retries with backoff, normalized errors
      (`AI_UNAVAILABLE`, `AI_TIMEOUT`, `AI_INVALID_RESPONSE`).
- [ ] Token-usage capture into result metadata.
- [ ] Keep the second provider unimplemented until needed.

## Phase 3 — Backend `ai` module 🔴

- [ ] Models `AIConversation`, `AIMessage`.
- [ ] Endpoints from `docs/api.md §2.9`: conversations, messages, writing
      correction, grammar explanation.
- [ ] Ownership checks, per-user rate limits, max-token budget.
- [ ] Persist normalised content (not raw provider payloads).

## Phase 4 — Prompt modules & structured output 🔴

- [ ] `prompts/tutor.py`, `grammar.py`, `writing.py`.
- [ ] JSON-schema outputs for correction/recommendations, validated before use.
- [ ] Prompt-injection guardrails: server-owned system prompt, delimited user
      content, no tool execution from model output.

## Phase 5 — Personalisation 🔴

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
- Failure UX: AI must degrade gracefully, never block core learning flows.
