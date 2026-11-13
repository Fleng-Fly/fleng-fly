# Error handling

[core/errors.py](../../backend/app/core/errors.py) maps domain, HTTP, validation, database and unexpected failures to an envelope:

```json
{"error":{"code":"UNAUTHORIZED","message":"Authentication required","statusCode":401,"timestamp":"2026-11-13T00:00:00Z","path":"/api/v1/users/me"}}
```

Optional details lists validation type/location/message without raw submitted input. Bearer failures have WWW-Authenticate: Bearer. Missing/draft/foreign-owned objects return 404. SQLAlchemy/OSError failures produce 503 DATABASE_UNAVAILABLE with safe diagnostic metadata logged; unexpected errors produce 500 INTERNAL_ERROR. Restrict log access.

Body limit defaults to 131072 bytes and returns 413. Persistent quotas return 429 RATE_LIMITED plus Retry-After. SSE errors after headers arrive inside HTTP 200 as error events. Static/CORS middleware responses need not use this envelope. [Status reference](../12-reference/api-status-codes.md) explains distinctions.

[Section index](README.md) · [Documentation home](../README.md)
