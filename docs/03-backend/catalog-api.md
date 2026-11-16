# Catalog api

Public published-only courses ordered by position; optional level A0–C2. No catalog pagination. Missing and draft course return 404 NOT_FOUND. Models: Course, Lesson.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/courses`

List published courses ordered by position.

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| level | query | False | `{"anyOf": [{"enum": ["A0", "A1", "A2", "B1", "B2", "C1", "C2"], "type": "string"}, {"type": "null"}], "title": "Level"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"type": "array", "items": {"$ref": "#/components/schemas/CourseSummaryResponse"}, "title": "Response List Courses Api V1 Courses Get"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/courses
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

## `GET /api/v1/courses/{slug}`

Return a published course and its published lessons.

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| slug | path | True | `{"type": "string", "title": "Slug"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/CourseDetailResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/courses/example-slug
```

Synthetic response shape (not a seeded/live result):

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "slug": "example",
  "title": "example",
  "description": "example",
  "level": "A0",
  "lessons": []
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
