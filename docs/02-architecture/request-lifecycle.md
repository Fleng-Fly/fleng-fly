# Request lifecycle

Body-size/CORS middleware surrounds routing, Pydantic parsing and dependencies. Protected routes resolve the JWT subject to a persisted user. get_db yields an AsyncSession; handlers/services commit writes explicitly. Closing the session does not automatically commit pending work. Domain and unexpected errors map through centralized handlers.

```mermaid
sequenceDiagram
  participant UI as Browser
  participant Auth as Auth router
  participant DB as Database
  UI->>Auth: Login email and password
  Auth->>DB: Consume quotas and verify identity
  Auth->>DB: Store hashed refresh token
  Auth-->>UI: Access JWT and HttpOnly cookie
  UI->>Auth: Refresh cookie
  Auth->>DB: Atomically claim old token and link successor
  Auth-->>UI: Replacement JWT and cookie
  Note over Auth,DB: Token reuse revokes refresh sessions
```

Access JWTs remain valid until expiry after logout/password changes; refresh revocation is not an access-token denylist. [SSE](../07-ai/streaming.md) uses events for failures after headers.

[Section index](README.md) · [Documentation home](../README.md)
