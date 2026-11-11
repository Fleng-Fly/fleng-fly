# Vocabulary & flashcards — backend contract

David's backend scope. Frontend implements category buttons, card flipping and
navigation. Roma owns testing questions, incorrect/difficult-answer retries,
letter dragging, full-word grading and XP. No testing engine or XP is added here.

## Audit and design

Existing `VocabularyItem` stores user-owned word/translation/example, optional
lesson ID, learned flag and due time, unique `(user_id, word)`. Existing CRUD,
lesson filtering, stats and `VocabularyReview` history are retained. Review
scheduling remains 1 day for failure / 7 days for remembered. PATCH currently
updates learned state only; this task preserves that contract.

Courses and lessons live in `modules/catalog`, not separate courses/lessons
modules. Lesson belongs to Course. Personal lesson links are not shared course
content: exposing other learners' saved words would leak private data.

`CourseVocabularyItem` adds only missing curated content: course FK, word,
translation and example, unique `(course_id, word)`. CEFR comes from Course;
there is no duplicated level or copy of personal words. Content maintainers may
insert curated entries through SQLAlchemy/import tooling in the future. Normalize
words with `strip().casefold()` before insertion, reject blank values and respect
120/300/1000 length limits; no public catalog-write API or invented seed content
is included. Catalog starts empty. Identical words in different courses are valid.

Course's existing CHECK accepts A1–C2 only. A0 is accepted as a vocabulary filter
and returns empty; it is not silently mapped to A1. Minimal future A0 support
requires a separate migration extending `courses_level_check` and coordination
with course/profile/filter consumers. This task preserves that shared model.

Persistent `FlashcardSession` stores JWT owner, source, status, immutable JSON
snapshot (real original word UUIDs plus database text), timestamps. JSON is a
bounded session snapshot, not another dictionary. Original IDs intentionally are
not FKs: deleting a word or course must not alter an ongoing test's composition.
SQL storage survives restarts and works across workers; in-memory or client-held
unsigned sets would not provide that contract. No expiry/cleanup is implemented;
retention is future operational work.

Migration `20261110_1200` creates only these two tables and their indexes/checks.
Existing user vocabulary and migration files are unchanged. Downgrade removes
only the new feature tables and their feature data.

## API

All routes below require the existing Bearer access JWT. JSON uses the project's
camelCase convention; POST input also accepts snake_case field names.

- `GET /api/v1/vocabulary`: existing personal list (own rows only).
- `GET /api/v1/vocabulary/course-words?courseId=<UUID>&level=A1&limit=50&offset=0`:
  curated words of published courses. Both filters optional and intersect when
  combined. Returns `[{id, courseId, word, translation, example}]`. Limit 1–100.
- `POST /api/v1/vocabulary/flashcards/sessions`: body
  `{ "source": "my_words", "courseId": null, "level": null }`, or
  `{ "source": "course_words", "courseId": "<UUID>", "level": "A1" }`.
  Course source requires at least one filter. Personal source rejects filters.
  Client cannot supply owner, cards, status, count or XP (unknown fields rejected).
- `GET /api/v1/vocabulary/flashcards/sessions/{sessionId}`: owned saved snapshot.
- `POST /api/v1/vocabulary/flashcards/sessions/{sessionId}/complete`: no body;
  owner acknowledges finishing the cards. Idempotent for completed sessions.
- `GET /api/v1/vocabulary/flashcards/sessions/{sessionId}/test-words`:
  same snapshot, available only after completion.

Create returns HTTP 201; read/complete/test-words return 200:

```json
{
  "sessionId": "<UUID>",
  "source": "my_words",
  "status": "active",
  "total": 1,
  "cards": [{"wordId": "<real UUID>", "word": "<database word>",
             "translation": "<database translation>", "example": ""}],
  "testReady": false
}
```

Selection is deterministic, maximum 10: personal words ordered by creation/UUID;
course words by word/UUID. 1–9 uses all; zero returns persisted `empty`, total 0,
cards `[]`, testReady false. No randomization, learned/due filtering or review
updates. A repeated create is a new independent session; repeated GET returns the
same set, even after source edits/deletions. No create idempotency key is claimed.

## Frontend and Roma handoff

Frontend keeps sessionId and reads the saved snapshot on resume. It flips cards
locally and POSTs complete after the last card. Response changes `active` to
`completed`, `testReady: true`; frontend then chooses navigation. Backend does
not redirect. Empty remains empty and cannot start a test.

Pass only sessionId to Roma's future test-start endpoint. That endpoint must use
its authenticated JWT user ID and call
`vocabulary.flashcards.words_for_test(db, user_id, session_id)`. It checks owner
and completed state, then returns exact ordered IDs, words, translations and
examples from the saved snapshot. Never accept a client-supplied word list or
owner as authoritative, nor reselect words from the changing dictionary.
`wordId` is interpreted together with session source; it may refer to a deleted
original, so the snapshot is authoritative during this attempt.

Completion is a learner acknowledgement, not proof that every card was viewed.
It earns no XP, learned flags, reviews, streaks, achievements or lesson progress.
Roma's grading path must validate submitted answers and own once-only XP rules;
completion/testReady must never itself grant XP. Test question/attempt persistence
and retry rules remain Roma's responsibility.

## Security and errors

Every session read/update filters both UUID and JWT owner. Unknown/foreign
sessions return the same 404 (deliberately not 403, to hide existence). Conditional
UPDATE includes owner and active state, so retries cannot reset completion time.
No caller-supplied owner can override JWT. Lists never query another user's
personal vocabulary; unpublished course words are excluded.

- 400: invalid source/filter combination or completing an empty set.
- 401: missing/invalid access JWT, existing auth dependency.
- 404: nonexistent/unpublished course or unknown/foreign session.
- 409: test-words requested before completed.
- 422: invalid UUID, CEFR outside A0–C2, source, pagination or extra POST fields,
  following existing FastAPI validation conventions.

No new 403 branch is necessary. Viewing translations is expected for flashcards;
they are not official exercise answer keys. Existing request-body limits apply.

## Verification

See `tests/test_vocabulary_flashcards.py` for sets of 0/3/12, user isolation,
course filters, unpublished/invalid courses, stable snapshots after deletion,
repeated requests/completion, handoff gating, auth/validation and zero XP.
Live PostgreSQL: NOT VERIFIED without TEST_DATABASE_URL.

Verification on 2026-11-10: full pytest run **293 passed, 15 skipped**;
subsequently expanded feature suite **7 passed**, migration-preservation suite
**1 passed**. Ruff (app/tests/new migration), mypy (66 source files), SQLite
upgrade/head/check, PostgreSQL offline migration SQL and git diff --check passed.
SQLite upgrade/downgrade/upgrade preserves existing personal words. Independent
self-review covered owner predicates, immutable snapshots, idempotent completion,
route precedence, unchanged personal CRUD and absence of grading/XP side effects.
Existing dependency deprecation warnings remain (pytest-asyncio loop scope,
Starlette/httpx and Alembic path_separator). No live PostgreSQL claim is made.

Final pre-commit verification: full pytest **297 passed, 15 skipped**; Ruff,
mypy, SQLite Alembic upgrade/check/head, PostgreSQL offline SQL and staged
whitespace/artifact/credential checks passed. Personal-word preservation test
passed through upgrade/downgrade/upgrade. Live PostgreSQL remains NOT VERIFIED.
