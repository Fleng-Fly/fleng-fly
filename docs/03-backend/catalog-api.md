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

## `GET /api/v1/courses/{slug}/progress`

Authenticated own-user snapshot for all published lessons of one published course.
Slug is a required path string. There is no caller-selected userId, no body and
no exercise/submission payload. Uses two catalog queries independently of lesson
count, plus the existing authentication reads. It never writes progress or XP.

Response 200: CourseLessonProgressResponse; courseId, lessonsTotal,
lessonsStarted (includes completed), lessonsCompleted and lessons in catalog
order (lessonId, slug, status). Status is not_started, in_progress or completed.
Empty courses return zero totals and an empty list. Own missing rows are
not_started, including when a different user has completed the same lesson.
Cache-Control: private, no-store. Missing/invalid bearer identity returns 401;
missing/draft courses return the same 404 NOT_FOUND. Unpublished lessons are
excluded. The existing detailed lesson-progress endpoint is unchanged.

The course page makes one status request, renders lessons before that request
finishes, and retains all lesson links on progress failure. Unknown status is
shown as unavailable; it is never presented as zero progress or Not Started.
