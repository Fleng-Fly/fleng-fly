# Limits and errors

Defaults: service input 4000 chars, response 16000 chars, output 800 tokens, estimated input 24000 tokens, history 20 messages/16000 chars, conversation 200 messages and 50 conversations/user. ChatRequest allows 16000 message chars, but service settings can be stricter.

Persistent quotas default 10/minute, 100/day, 100000 daily reserved tokens; capacity defaults 4. One active AI reservation/user is permitted. Reservation estimates are not a provider invoice cap.

AI_INPUT_LIMIT=422; AI_HISTORY_LIMIT/AI_CONVERSATION_LIMIT/AI_REQUEST_DUPLICATE=409; AI_BUSY/AI_BUDGET_LIMIT=429; AI_UNAVAILABLE=503; AI_TIMEOUT=504 before streaming. After headers errors are SSE events. [API](../03-backend/ai-api.md) describes request fields; [security](../08-security/README.md) covers remaining boundaries.

[Section index](README.md) · [Documentation home](../README.md)
