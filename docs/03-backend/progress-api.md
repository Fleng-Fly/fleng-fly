# Progress api

Own Progress/Profile XP with derived exercise/published-course counts. No user override, pagination or writable client totals.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/progress/me`

Get My Progress

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/ProgressResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/progress/me \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "userId": "00000000-0000-4000-8000-000000000001",
  "lessonsStarted": 0,
  "lessonsCompleted": 0,
  "exercisesCompleted": 0,
  "studyMinutes": 0,
  "xp": 0,
  "lastActivityAt": "2026-11-13T00:00:00Z",
  "updatedAt": "2026-11-13T00:00:00Z",
  "courses": [],
  "activeCourses": 0,
  "streak": {"current": 0, "longest": 0, "lastActivityDate": null, "timezone": "UTC"},
  "xpHistory": {"available": false, "reason": "XP_AWARD_HISTORY_NOT_RECORDED", "last7Days": null, "last30Days": null}
}
```

## `GET /api/v1/progress/daily`

Get Daily Goals

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/DailyGoalsResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

The goals come from the profile (`dailyLessonsGoal`, `dailyWordsGoal`, set with `PATCH /users/me`); `done` is derived from lessons completed and distinct words remembered during the learner's current local day (`profiles.timezone`, else the server learning timezone). It may exceed `goal`.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/progress/daily \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "date": "2026-11-20",
  "timezone": "Europe/Kyiv",
  "lessons": {"goal": 3, "done": 2},
  "vocabulary": {"goal": 20, "done": 14}
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
