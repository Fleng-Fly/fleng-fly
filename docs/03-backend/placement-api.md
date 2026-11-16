# Placement API

All operations require a Bearer JWT. Missing/foreign attempt UUIDs return 404.
Requests and responses use camelCase; [schemas](api-schemas.md) contain exact
fields. See [assessment methodology and limits](../placement-test.md).

## `POST /api/v1/placement-test/attempts`

Create an independent attempt. Returns 201 PlacementDetail with public questions,
empty answers, result=null and no recommendations. No answer keys/explanations.
20 starts per user per UTC day; 429 RATE_LIMITED includes Retry-After. No request
body or caller-selected user, level, score or question set is accepted as authority.

## `GET /api/v1/placement-test/attempts`

Returns 200 PlacementSummary[]. Query limit defaults 20 (1–100), offset defaults
0 (nonnegative). Most recent first with UUID tie-break. Includes unfinished
attempts and completed labels, but no keys or private snapshots.

## `GET /api/v1/placement-test/attempts/{attempt_id}`

Returns 200 PlacementDetail for the owner's UUID. In-progress output includes
selected answers and no correctness. Completed output includes the saved result,
review and current published-course recommendations.

## `PUT /api/v1/placement-test/attempts/{attempt_id}/answers`

Save or change selections until completion. Returns 200 PlacementDetail without
correctness. Nonempty answers array has at most 100 entries. Example:

```sh
curl -X PUT http://localhost:3001/api/v1/placement-test/attempts/00000000-0000-4000-8000-000000000001/answers \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"answers":[{"questionId":"q01","optionId":"a"}]}'
```

422 INVALID_PLACEMENT_ANSWER for duplicate/unknown question or option; schema
validation rejects unknown fields and malformed/empty payloads. 409
PLACEMENT_COMPLETED prevents changing a completed attempt.

## `POST /api/v1/placement-test/attempts/{attempt_id}/complete`

No request body. Requires all questions answered. Returns 200 PlacementDetail
with deterministic result and post-test review. Completion is idempotent: the
stored score is not recomputed. 409 PLACEMENT_INCOMPLETE for missing answers;
409 PLACEMENT_VERSION_UNAVAILABLE for an unsupported unfinished scoring version.
Result never certifies C1/C2; reliability is limited and the current maximum
assessment range is A1–B2. No XP/profile/progress/streak/achievement write.

Shared errors: 401 auth, 413 body size, 422 request/path/query validation,
503 database unavailable and the standard error envelope.
