# Architecture

AI is a backend module, not a separate service or grading authority. router.py exposes status/chat/history/explain/generation/recommendations/stream; service.py owns input/ownership, quota reservations, capacity and persistence; provider.py implements OpenRouter HTTPS; context.py resolves educational/user context and prompts.py owns server instructions.

AIConversation, AIMessage and AIUsage persist history/reservations. Disabled AI leaves learning/ranking functional. Recommendations are deterministic without provider configuration. Tests inject synthetic providers; no configurable production mock mode is promised. See [streaming](streaming.md) and [limits](limits-and-errors.md).

[Section index](README.md) · [Documentation home](../README.md)
