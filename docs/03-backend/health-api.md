# Health api

Public SELECT 1 probe; health keeps HTTP 200 with database down, ready uses 503 on down/five-second timeout. No schema-head/table-integrity guarantee or private rows/config.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/health`

Health

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/HealthResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/health
```

Synthetic response shape (not a seeded/live result):

```json
{
  "status": "ok",
  "service": "backend",
  "timestamp": "2026-11-13T00:00:00Z",
  "database": "up"
}
```

## `GET /api/v1/health/ready`

Readiness

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/HealthResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/health/ready
```

Synthetic response shape (not a seeded/live result):

```json
{
  "status": "ok",
  "service": "backend",
  "timestamp": "2026-11-13T00:00:00Z",
  "database": "up"
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
