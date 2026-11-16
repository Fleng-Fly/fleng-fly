# Flashcards

FlashcardSession stores an owned immutable JSON snapshot. Creation source is my_words or course_words. Personal selection rejects courseId/level; course selection requires courseId, level or an explicit wordIds list. Default limit is 10; callers may choose 1–50. Explicit IDs are validated against ownership/publication and all active filters before selection; their order is preserved. Small sets are valid.

Empty selection is stored as empty/total=0 and completion fails with 400 EMPTY_SESSION. Nonempty sets start active; completion idempotently marks completed/completed_at. Foreign/missing IDs return 404 for reads, completion and handoff.

testReady derives from completed status. /test-words and internal words_for_test require completion (otherwise 409 FLASHCARDS_NOT_COMPLETED), returning the saved sessionId/cards/IDs. They do not generate tests, grade, award XP, mark source words learned or schedule reviews. Future testing must call words_for_test with the JWT user, never a client owner.

JSON word references survive source deletion. Dedicated Course Words and Study & Test browser pages now use these endpoints. Personal test answers call the existing review API; course-run scores remain local to that run, with no XP. See [API](../03-backend/flashcards-api.md).

[Section index](README.md) · [Documentation home](../README.md)
