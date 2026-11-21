# Reading API

All operations require a Bearer JWT, use camelCase JSON and the standard error envelope.
[Schemas](api-schemas.md) contain exact fields. An article is visible to learners only when it
is `published` and its category is active; anything else, and any other learner's attempt, is
404 NOT_FOUND. There are no authoring routes yet: demo content comes from
`python -m app.db.reading_seed` (draft-only, idempotent). Pass mark is 70 %. XP is the existing
`profiles.xp`, paid once per learner and article on the first passing attempt. Answer keys and
explanations appear only in a submitted attempt's result, never before.

## `GET /api/v1/reading/categories`

Returns 200 ReadingCategoryResponse[]: active categories with the number of published articles.

## `GET /api/v1/reading/articles`

Returns 200 ReadingArticleList `{items,total,limit,offset}` without article text. Query:
`categoryId`, `level` (A0, A1, A2, B1, B2), `bookmarked` (boolean), `progress` (`new`,
`in_progress`, `completed`), `limit` (1-100, default 20) and `offset`. Newest published first.
Invalid values return 422.

## `GET /api/v1/reading/articles/{slug}`

Returns 200 ReadingArticleDetail: text, `questionCount`, `pointsPossible`, the caller's
progress and bookmark flag. No questions or answers are included.

## `PUT /api/v1/reading/articles/{slug}/progress`

Records how far the learner has read. The percentage only grows; a lower value is ignored.
Limited to 60 writes per minute per learner (429 RATE_LIMITED with Retry-After); clients must
throttle. An article without a quiz completes at 100 % (no XP). Example:

```sh
curl -X PUT http://localhost:3001/api/v1/reading/articles/my-day/progress \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"percent":60}'
```

Returns 200 ReadingProgressResponse. 422 for a non-integer or a value outside 0-100.

## `PUT /api/v1/reading/articles/{slug}/bookmark`

Idempotent. Returns 200 ReadingBookmarkResponse. 404 for an unavailable article.

## `DELETE /api/v1/reading/articles/{slug}/bookmark`

Idempotent 204, also for an unavailable or unknown slug, so a stale bookmark can be removed.

## `GET /api/v1/reading/bookmarks`

Returns 200 ReadingArticleSummary[]: the caller's saved articles that are still available.

## `GET /api/v1/reading/preferences`

Returns 200 ReadingPreferencesResponse: preferred topics that are still active.

## `PUT /api/v1/reading/preferences`

Replaces the whole list (at most 50 ids). Unknown or inactive categories return 422 and change
nothing. Example:

```sh
curl -X PUT http://localhost:3001/api/v1/reading/preferences \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"categoryIds":["00000000-0000-4000-8000-000000000001"]}'
```

Returns 200 ReadingPreferencesResponse.

## `POST /api/v1/reading/articles/{slug}/attempts`

Starts a quiz attempt (201) or returns the unfinished one (200) so a learner can resume. The
response lists questions with answer options and no correctness. 409 NO_QUESTIONS when the
article has no quiz. Starting a new attempt is limited to 30 per hour per learner.

## `GET /api/v1/reading/articles/{slug}/attempts`

Returns 200 ReadingAttemptSummary[], newest first.

## `GET /api/v1/reading/attempts/{attempt_id}`

Returns 200 ReadingAttemptResponse: an open attempt carries `questions` and saved `answers`; a
submitted one carries `result`.

## `PATCH /api/v1/reading/attempts/{attempt_id}/answers`

Merges `{questionId: answerId}` pairs into an unfinished attempt (autosave). Limited to 30
attempt writes per minute per learner. Example:

```sh
curl -X PATCH http://localhost:3001/api/v1/reading/attempts/00000000-0000-4000-8000-000000000001/answers \
  -H "Authorization: Bearer $FLENG_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"answers":{"00000000-0000-4000-8000-000000000002":"00000000-0000-4000-8000-000000000003"}}'
```

Returns 200 ReadingAttemptResponse. 422 INVALID_ANSWER for a question or answer that does not
belong to the article; 409 ATTEMPT_SUBMITTED for a submitted attempt.

## `POST /api/v1/reading/attempts/{attempt_id}/submit`

Optional body `{answers}` is merged first. Grades, freezes the result and, on the first pass of
the article, awards XP once. Repeating the call returns the stored result with
`alreadySubmitted: true` and pays nothing. Unanswered questions score zero.

Shared errors: 401 auth, 404 not available, 422 request validation, 429 rate limit and the
standard error envelope. Editing a published article's quiz while attempts are open is rejected
by the service layer (QUIZ_LOCKED); no HTTP route edits content.
