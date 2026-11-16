# Gamification api

Authenticated own streak/achievement views. LearningActivity user/day unique; timezone server-owned. Unearned award timestamps null. No caller-written awards/streaks. Models: LearningActivity, Achievement, UserAchievement.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/streaks/me`

Get Streak

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/StreakResponse"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/streaks/me \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "current": 0,
  "longest": 0,
  "lastActivityDate": null,
  "timezone": "UTC"
}
```

## `GET /api/v1/achievements/me`

Achievements

Authentication/permissions: Bearer JWT, owner scoped where applicable.

Parameters: none.

Request body: none.

Declared responses:

- **200**: Successful Response; `{"items": {"$ref": "#/components/schemas/AchievementResponse"}, "type": "array", "title": "Response Achievements Api V1 Achievements Me Get"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/achievements/me \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
[]
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
