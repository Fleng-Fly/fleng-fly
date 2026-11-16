# Lessons api

Public detail requires course and lesson publication. Returns theory/safe exercises without grading secrets. Missing/draft is 404 NOT_FOUND. Models: Lesson, Course, Exercise.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/lessons/{slug}`

Return a published lesson with its course context.

Authentication/permissions: No Bearer required; session routes validate supplied Origin and refresh uses cookie.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| slug | path | True | `{"type": "string", "title": "Slug"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/LessonDetailResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/lessons/example-slug
```

Synthetic response shape (not a seeded/live result):

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "slug": "example",
  "title": "example",
  "summary": "example",
  "theory": "example",
  "position": 0,
  "estimatedMinutes": 0,
  "courseSlug": "example",
  "courseTitle": "example",
  "level": "A0",
  "exercises": []
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
