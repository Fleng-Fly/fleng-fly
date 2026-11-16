# Api integration

API_BASE is relative /api/v1. apiFetch sets Accept, conditional JSON Content-Type, optional Bearer Authorization, credentials=include and cache=no-store. It maps network/HTTP/invalid JSON errors into ApiError and returns undefined for 204. Protected 401 can refresh once; auth errors cannot recursively refresh.

SSE calls request rawResponse and read response.body with incremental UTF-8 decoding. HTTP success still requires processing error/done events. AbortController manages cancellation. Never expose provider secrets in frontend configuration.

Submission forms send server option IDs; server results determine XP/progress. No optimistic client-authoritative totals or shared response cache exists. Netlify needs a real /api proxy because CORS does not change relative request destinations.

[Section index](README.md) · [Documentation home](../README.md)
