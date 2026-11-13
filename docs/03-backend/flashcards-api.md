# Flashcards api

JWT-owned persistent snapshot, foreign/missing returns 404. Creation selects at most ten. my_words rejects course filters (400 INVALID_SOURCE_FILTER); course_words requires courseId/level (400 MISSING_COURSE_FILTER). Empty creation valid; complete empty returns 400 EMPTY_SESSION. Premature handoff 409 FLASHCARDS_NOT_COMPLETED. No XP/test grader. Models: FlashcardSession, VocabularyItem, CourseVocabularyItem.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `POST /api/v1/vocabulary/flashcards/sessions`

Create Flashcards

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `FlashcardCreate` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **201**: Successful Response; `{"$ref": "#/components/schemas/FlashcardResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/vocabulary/flashcards/sessions \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"source": "my_words"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "sessionId": "00000000-0000-4000-8000-000000000001",
  "source": "my_words",
  "status": "empty",
  "total": 0,
  "cards": [],
  "testReady": false
}
```

## `GET /api/v1/vocabulary/flashcards/sessions/{session_id}`

Get Flashcards

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| session_id | path | True | `{"type": "string", "format": "uuid", "title": "Session Id"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/FlashcardResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary/flashcards/sessions/00000000-0000-4000-8000-000000000001 \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "sessionId": "00000000-0000-4000-8000-000000000001",
  "source": "my_words",
  "status": "empty",
  "total": 0,
  "cards": [],
  "testReady": false
}
```

## `POST /api/v1/vocabulary/flashcards/sessions/{session_id}/complete`

Complete Flashcards

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| session_id | path | True | `{"type": "string", "format": "uuid", "title": "Session Id"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/FlashcardResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/vocabulary/flashcards/sessions/00000000-0000-4000-8000-000000000001/complete \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "sessionId": "00000000-0000-4000-8000-000000000001",
  "source": "my_words",
  "status": "empty",
  "total": 0,
  "cards": [],
  "testReady": false
}
```

## `GET /api/v1/vocabulary/flashcards/sessions/{session_id}/test-words`

Flashcards Test Words

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| session_id | path | True | `{"type": "string", "format": "uuid", "title": "Session Id"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/FlashcardResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary/flashcards/sessions/00000000-0000-4000-8000-000000000001/test-words \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "sessionId": "00000000-0000-4000-8000-000000000001",
  "source": "my_words",
  "status": "empty",
  "total": 0,
  "cards": [],
  "testReady": false
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
