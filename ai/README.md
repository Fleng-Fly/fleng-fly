# ai/

Provider-agnostic AI layer of Fleng (`@fleng/ai`). **Not implemented yet** —
this directory currently holds documentation only.

## Why a separate directory

AI is a distinct logical layer with its own concerns: provider selection,
prompt construction, context assembly, response parsing and safety. Keeping it
isolated from NestJS controllers makes it testable without HTTP and keeps AI
providers swappable.

It is **not** a microservice. `@fleng/ai` is a TypeScript library imported by the
backend `ai` module. A network boundary is not justified at this stage — see
`docs/ai.md` for the conditions under which that could change.

## Planned contents

- A minimal `AIProvider` interface (chat/completion + embeddings).
- A provider registry configured via environment variables.
- Prompt builders for each capability (tutor, grammar, correction, feedback, recommendations).
- Output schemas + validation for structured responses.
- Prompt-injection and PII guardrails (see `docs/security.md`).

## Capabilities (target)

AI Tutor, grammar explanations, writing correction, conversation practice,
speaking feedback, vocabulary recommendations, personalised learning path,
exercise generation, progress analysis.

## Where to look

- Plan: `plans/ai-plan.md`
- Docs: `docs/ai.md`
- Security: `docs/security.md`
