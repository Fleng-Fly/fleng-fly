# Api status codes

| HTTP | Verified use |
| --- | --- |
| 200 | Reads/login/refresh/updates; stream header success |
| 201 | Registration/word/session creation |
| 204 | Logout/password/reset confirmation/deletion; no body |
| 400 | Source filters/empty session/current password errors |
| 401 | Missing/invalid JWT/login/refresh |
| 403 | Auth Origin rejection/local reviewer denial |
| 404 | Missing/draft/unowned resource |
| 409 | Duplicate email/incomplete handoff/AI conflicts |
| 413 | Body size cap |
| 422 | Schema/domain validation |
| 429 | Quotas/AI busy/budget |
| 500 | Sanitized unexpected exception |
| 503 | Database/provider unavailable before stream |
| 504 | AI timeout before stream |

Health can return 200 with database down; ready returns 503 on down/timeout. After headers, SSE failures are error events inside HTTP 200. Error codes carry more detail than status. [Error handling](../03-backend/error-handling.md) describes envelopes; middleware/static responses can differ.

[Section index](README.md) · [Documentation home](../README.md)
