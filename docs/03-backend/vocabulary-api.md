# Vocabulary api

Bearer caller only. Personal CRUD/history is owner-scoped (404 foreign/missing); duplicate word can return 409. Course words require published Course and inherit level; missing/draft courseId is 404. Only declared filters/page bounds apply. Review appends VocabularyReview and schedules one-/seven-day due. Models: VocabularyItem, VocabularyReview, CourseVocabularyItem, Course.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/vocabulary/course-words`

Course Words

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| courseId | query | False | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}], "title": "Courseid"}` |
| level | query | False | `{"anyOf": [{"enum": ["A0", "A1", "A2", "B1", "B2", "C1", "C2"], "type": "string"}, {"type": "null"}], "title": "Level"}` |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 50, "title": "Limit"}` |
| offset | query | False | `{"type": "integer", "minimum": 0, "default": 0, "title": "Offset"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/CourseWordResponse"}, "title": "Response Course Words Api V1 Vocabulary Course Words Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary/course-words \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

## `GET /api/v1/vocabulary/stats`

Count the caller's saved words marked learned, without paging through the list.

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/VocabularyStatsResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary/stats \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "wordsLearned": 0
}
```

## `GET /api/v1/vocabulary`

List Words

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| due | query | False | `{"type": "boolean", "default": false, "title": "Due"}` |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 50, "title": "Limit"}` |
| offset | query | False | `{"type": "integer", "minimum": 0, "default": 0, "title": "Offset"}` |
| lessonId | query | False | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}], "title": "Lessonid"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/VocabularyResponse"}, "title": "Response List Words Api V1 Vocabulary Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

## `POST /api/v1/vocabulary`

Add Word

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: JSON `VocabularyCreate` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **201**: Successful Response; `{"$ref": "#/components/schemas/VocabularyResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/vocabulary \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"word": "hello", "translation": "привіт", "example": "Hello, Alex."}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "word": "example",
  "translation": "example",
  "example": "",
  "lessonId": "00000000-0000-4000-8000-000000000001",
  "id": "00000000-0000-4000-8000-000000000001",
  "learned": false,
  "dueAt": "2026-11-13T00:00:00Z",
  "createdAt": "2026-11-13T00:00:00Z"
}
```

## `PATCH /api/v1/vocabulary/{item_id}`

Update Word

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| item_id | path | True | `{"type": "string", "format": "uuid", "title": "Item Id"}` |

Request body: JSON `VocabularyUpdate` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/VocabularyResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X PATCH http://localhost:3001/api/v1/vocabulary/00000000-0000-4000-8000-000000000001 \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"learned": false}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "word": "example",
  "translation": "example",
  "example": "",
  "lessonId": "00000000-0000-4000-8000-000000000001",
  "id": "00000000-0000-4000-8000-000000000001",
  "learned": false,
  "dueAt": "2026-11-13T00:00:00Z",
  "createdAt": "2026-11-13T00:00:00Z"
}
```

## `DELETE /api/v1/vocabulary/{item_id}`

Remove Word

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| item_id | path | True | `{"type": "string", "format": "uuid", "title": "Item Id"}` |

Request body: none.

Declared responses:

- **204**: Successful Response; no declared JSON model.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X DELETE http://localhost:3001/api/v1/vocabulary/00000000-0000-4000-8000-000000000001 \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

No JSON body for 204; unmodeled/stream responses follow the transport notes.

## `POST /api/v1/vocabulary/{item_id}/review`

Review Word

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| item_id | path | True | `{"type": "string", "format": "uuid", "title": "Item Id"}` |

Request body: JSON `ReviewRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/VocabularyResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/vocabulary/00000000-0000-4000-8000-000000000001/review \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"remembered": false}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "word": "example",
  "translation": "example",
  "example": "",
  "lessonId": "00000000-0000-4000-8000-000000000001",
  "id": "00000000-0000-4000-8000-000000000001",
  "learned": false,
  "dueAt": "2026-11-13T00:00:00Z",
  "createdAt": "2026-11-13T00:00:00Z"
}
```

## `GET /api/v1/vocabulary/{item_id}/reviews`

Review History

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| item_id | path | True | `{"type": "string", "format": "uuid", "title": "Item Id"}` |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 50, "title": "Limit"}` |
| offset | query | False | `{"type": "integer", "minimum": 0, "default": 0, "title": "Offset"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/ReviewResponse"}, "title": "Response Review History Api V1 Vocabulary  Item Id  Reviews Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/vocabulary/00000000-0000-4000-8000-000000000001/reviews \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

[Backend index](README.md) · [Schema reference](api-schemas.md)

Duplicate insertion returns 409 WORD_EXISTS. Personal word input is trimmed then casefolded for persistence; it is not automatically imported from the course dictionary.
