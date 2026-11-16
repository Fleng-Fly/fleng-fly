# Exercises api

Bearer caller only. Resolves published lesson/exercise within it. Start/resume is idempotent; submission upserts ExerciseSubmission, LessonProgress/Progress/Profile and gamification under learner write lock. Invalid choices/text/selfAssessment return 422 INVALID_ANSWER; unsupported type is 422; invisible/mismatched content is 404. XP once; self-check is learner assessment.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `POST /api/v1/lessons/{slug}/start`

Start or resume a lesson. Idempotent.

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| slug | path | True | `{"type": "string", "title": "Slug"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/LessonProgressResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/lessons/example-slug/start \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "lessonSlug": "example-lesson",
  "lessonTitle": "Example lesson",
  "status": "in_progress",
  "completed": false,
  "startedAt": "2026-11-13T00:00:00Z",
  "completedAt": null,
  "exercisesTotal": 0,
  "exercisesCompleted": 0,
  "xpEarned": 0,
  "exercises": []
}
```

## `GET /api/v1/lessons/{slug}/progress`

Read the caller's progress through a lesson.

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| slug | path | True | `{"type": "string", "title": "Slug"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/LessonProgressResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/lessons/example-slug/progress \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "lessonSlug": "example-lesson",
  "lessonTitle": "Example lesson",
  "status": "not_started",
  "completed": false,
  "startedAt": null,
  "completedAt": null,
  "exercisesTotal": 0,
  "exercisesCompleted": 0,
  "xpEarned": 0,
  "exercises": []
}
```

## `POST /api/v1/lessons/{slug}/submit`

Grade and persist one answer; return the result and lesson progress.

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| slug | path | True | `{"type": "string", "title": "Slug"}` |

Request body: JSON `SubmissionRequest` (required=True), defined in [schemas](api-schemas.md).

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/SubmissionResultResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X POST http://localhost:3001/api/v1/lessons/example-slug/submit \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"exerciseId": "00000000-0000-4000-8000-000000000001", "answer": "a"}'
```

Synthetic response shape (not a seeded/live result):

```json
{
  "exerciseId": "00000000-0000-4000-8000-000000000001",
  "type": "single_choice",
  "isCorrect": true,
  "completed": true,
  "points": 1,
  "xpAwarded": 1,
  "feedback": "Correct.",
  "correctOptionId": "a",
  "acceptedAnswers": null,
  "modelAnswer": null,
  "explanation": "The selected form agrees with the subject.",
  "lesson": {
    "lessonSlug": "example-lesson",
    "lessonTitle": "Example lesson",
    "status": "completed",
    "completed": true,
    "startedAt": "2026-11-13T00:00:00Z",
    "completedAt": "2026-11-13T00:00:00Z",
    "exercisesTotal": 1,
    "exercisesCompleted": 1,
    "xpEarned": 1,
    "exercises": [
      {
        "exerciseId": "00000000-0000-4000-8000-000000000001",
        "completed": true,
        "isCorrect": true,
        "attempts": 1,
        "pointsAwarded": 1,
        "answer": "a"
      }
    ]
  }
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
