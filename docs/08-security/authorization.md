# Authorization

get_current_user requires Bearer identity and loads persisted user/profile. Caller IDs from JSON cannot select a different owner. Own profile/progress/vocabulary/flashcards/history queries scope by JWT user; foreign owned IDs return 404. Authenticated leaderboard intentionally shares display names/learning metrics.

Public catalog filters unpublished content and excludes pre-submission keys. Authenticated attempts reveal grading feedback. No production admin-role hierarchy/publication endpoint exists. Local preview requires its designated reviewer plus loopback/file guards and is not general administration.

Session/word/conversation UUIDs are lookup keys, never grants. Future testing must call owned words_for_test instead of trusting a client snapshot/owner.

[Section index](README.md) · [Documentation home](../README.md)
