# Users api

JWT user only. PATCH validates editable profile/email; null rejected. EMAIL_TAKEN/PROFILE_MISSING=409. Password verifies current (400 INVALID_PASSWORD), requires different new value and revokes refresh/reset sessions. Existing JWTs expire normally. Models: User, Profile, RefreshToken, PasswordReset.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/users/me`

Read the authenticated user's profile. Read-only; never creates a user.

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/UserResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/users/me \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "email": "example",
  "displayName": "Example learner",
  "level": 1,
  "xp": 0,
  "englishLevel": "A1",
  "preferredLanguage": "English",
  "createdAt": "2026-11-13T00:00:00Z"
}
```

## `PATCH /api/v1/users/me`

Update Me

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `ProfileUpdate` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/UserResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X PATCH http://localhost:3001/api/v1/users/me \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"displayName": "Example learner"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "email": "example",
  "displayName": "Example learner",
  "level": 1,
  "xp": 0,
  "englishLevel": "A1",
  "preferredLanguage": "English",
  "createdAt": "2026-11-13T00:00:00Z"
}
```

## `POST /api/v1/users/me/password`

Change Password

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `PasswordChange` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **204**: Successful Response; no declared JSON model.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/users/me/password \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"currentPassword": "example-old-passphrase", "newPassword": "example-new-passphrase"}'
```

No JSON body for 204; unmodeled/stream responses follow the transport notes.

[Backend index](README.md) · [Schema reference](api-schemas.md)
