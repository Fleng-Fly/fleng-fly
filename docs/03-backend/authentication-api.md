# Authentication api

Register/login issue JWTs and set refresh cookies. Refresh atomically rotates; logout revokes/clears. Supplied Origin is checked on session routes. Password reset request is generic and never returns a token; SMTP defaults off. Confirmation consumes an expiring reset token. Persistent auth/reset quotas apply. Errors include INVALID_CREDENTIALS/INVALID_REFRESH_TOKEN (401), EMAIL_TAKEN (409), FORBIDDEN (403), RATE_LIMITED (429). Models: User, Profile, Progress, RefreshToken, PasswordReset, RequestLimit. Exact domain codes are indexed below.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `POST /api/v1/auth/register`

Register

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: JSON `RegisterRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **201**: Successful Response; `{"$ref": "#/components/schemas/TokenResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/register \
  -b /tmp/fleng-example-cookies.txt -c /tmp/fleng-example-cookies.txt \
  -H 'Content-Type: application/json' \
  --data '{"email": "learner@example.com", "password": "example-passphrase-only", "displayName": "Example learner"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "accessToken": "EXAMPLE_ACCESS_TOKEN",
  "tokenType": "bearer",
  "expiresIn": 900,
  "user": {
    "id": "00000000-0000-4000-8000-000000000001",
    "email": "example",
    "displayName": "Example learner",
    "level": 1,
    "xp": 0,
    "englishLevel": "A1",
    "preferredLanguage": "English",
    "createdAt": "2026-11-13T00:00:00Z"
  }
}
```

## `POST /api/v1/auth/login`

Login

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: JSON `LoginRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/TokenResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/login \
  -b /tmp/fleng-example-cookies.txt -c /tmp/fleng-example-cookies.txt \
  -H 'Content-Type: application/json' \
  --data '{"email": "learner@example.com", "password": "example-passphrase-only"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "accessToken": "EXAMPLE_ACCESS_TOKEN",
  "tokenType": "bearer",
  "expiresIn": 900,
  "user": {
    "id": "00000000-0000-4000-8000-000000000001",
    "email": "example",
    "displayName": "Example learner",
    "level": 1,
    "xp": 0,
    "englishLevel": "A1",
    "preferredLanguage": "English",
    "createdAt": "2026-11-13T00:00:00Z"
  }
}
```

## `POST /api/v1/auth/refresh`

Refresh

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/AccessTokenResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/refresh \
  -b /tmp/fleng-example-cookies.txt -c /tmp/fleng-example-cookies.txt
```

Synthetic response shape (not a seeded/live result):

```json
{
  "accessToken": "EXAMPLE_ACCESS_TOKEN",
  "tokenType": "bearer",
  "expiresIn": 900
}
```

## `POST /api/v1/auth/logout`

Logout

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: none.

Declared responses:

- **204**: Successful Response; no declared JSON model.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/logout \
  -b /tmp/fleng-example-cookies.txt -c /tmp/fleng-example-cookies.txt
```

No JSON body for 204; unmodeled/stream responses follow the transport notes.

## `POST /api/v1/auth/password-reset/request`

Request Reset

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: JSON `ResetRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/ResetResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/password-reset/request \
  -H 'Content-Type: application/json' \
  --data '{"email": "learner@example.com"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "message": "If the account exists, password reset instructions will be sent."
}
```

## `POST /api/v1/auth/password-reset/confirm`

Confirm Reset

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

Parameters: none.

Request body: JSON `ResetConfirm` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **204**: Successful Response; no declared JSON model.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/auth/password-reset/confirm \
  -H 'Content-Type: application/json' \
  --data '{"token": "EXAMPLE_RESET_TOKEN_VALUE_32_CHARACTERS", "password": "example-new-passphrase"}'
```

No JSON body for 204; unmodeled/stream responses follow the transport notes.

[Backend index](README.md) · [Schema reference](api-schemas.md)

Reset confirmation additionally returns 400 INVALID_RESET_TOKEN for invalid/expired/used tokens. Reset delivery defaults disabled and request still returns the generic message; the API does not prove email delivery.
