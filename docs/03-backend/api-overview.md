# Api overview

All ordinary API routes use `/api/v1`. Public routes include health, catalog and session/reset operations. Protected endpoints use `Authorization: Bearer ACCESS_TOKEN`; refresh uses the HttpOnly cookie. Supplied-Origin checks on cookie session routes are additional to CORS.

JSON uses camelCase aliases (exerciseId, sessionId, testReady); CamelModel also accepts Python names. UUIDs are strings and timestamps use ISO JSON representations. Only declared list endpoints support bounded limit/offset; catalog has no pagination.

Endpoint pages enumerate runtime routes, parameters, schemas, examples and module-specific error/permission rules. [API schemas](api-schemas.md) preserves the complete generated contracts, including required fields and bounds. Examples are synthetic shape illustrations, not existing database records; discover real slugs/UUIDs via catalog/owned reads. HTTP 204 has no body.

```sh
curl -sS http://localhost:3001/api/v1/courses
curl -sS http://localhost:3001/api/v1/users/me -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Keep tokens private. POST SSE is fetched as a stream rather than EventSource. OpenAPI omits many service errors, so read [error handling](error-handling.md) and endpoint notes as well.

[Section index](README.md) · [Documentation home](../README.md)
