# Leaderboard api

Authenticated all-time Profile XP ranking, lesson/activity metrics, stable ties. limit max 100, no offset; returns top entries/caller global position/total. No emails/passwords/raw user IDs/sessions. No weekly/monthly mode.

Shared runtime failures: 413 body overflow, 422 declared schema validation, 503 DATABASE_UNAVAILABLE and 500 unexpected error. Protected calls add 401 missing/invalid identity. See [error handling](error-handling.md) and [complete schemas](api-schemas.md). Module-specific rules above apply to each operation.

## `GET /api/v1/leaderboard`

Get Leaderboard

Authentication/permissions: Bearer JWT, owner scoped where applicable.

| Parameter | In | Required | Exact schema |
| --- | --- | --- | --- |
| limit | query | False | `{"type": "integer", "maximum": 100, "minimum": 1, "default": 100, "title": "Limit"}` |

Request body: none.

Declared responses:

- **200**: Successful Response; `{"$ref": "#/components/schemas/LeaderboardResponse"}`.
- **422**: Validation Error; `{"$ref": "#/components/schemas/HTTPValidationError"}`.

Errors/permissions: module-specific and shared runtime rules above apply. No caller-selected owner override exists.

Example request: substitute discovered slugs/UUIDs; refresh/logout cookie jars require prior login. Example passwords/tokens are synthetic.

```sh
curl -i -X GET http://localhost:3001/api/v1/leaderboard \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN"
```

Synthetic response shape (not a seeded/live result):

```json
{
  "entries": [],
  "currentUser": {
    "rank": 0,
    "displayName": "example",
    "xp": 0,
    "lessonsCompleted": 0,
    "streak": 0,
    "isCurrentUser": false
  },
  "total": 0
}
```

[Backend index](README.md) · [Schema reference](api-schemas.md)
