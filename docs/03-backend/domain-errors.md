# Domain error source index

Literal ApiError declarations in the ordinary backend, indexed for diagnosis. Dynamic wrappers such as NOT_FOUND/INVALID_ANSWER, generic HTTP handlers and SSE errors also apply; this is not a per-route exhaustive call-graph analysis. No actual exception/request values are included.

| Status | Code | Message | Source |
| --- | --- | --- | --- |
| 400 | EMPTY_SESSION | An empty set cannot start a test | [backend/app/modules/vocabulary/flashcards.py:89](../../backend/app/modules/vocabulary/flashcards.py) |
| 400 | INVALID_PASSWORD | Current password is incorrect | [backend/app/modules/users/router.py:68](../../backend/app/modules/users/router.py) |
| 400 | INVALID_RESET_TOKEN | Invalid or expired reset token | [backend/app/modules/password_reset/service.py:69](../../backend/app/modules/password_reset/service.py) |
| 400 | INVALID_RESET_TOKEN | Invalid or expired reset token | [backend/app/modules/password_reset/service.py:87](../../backend/app/modules/password_reset/service.py) |
| 400 | INVALID_SOURCE_FILTER | Personal words do not accept course filters | [backend/app/modules/vocabulary/flashcards.py:43](../../backend/app/modules/vocabulary/flashcards.py) |
| 400 | MISSING_COURSE_FILTER | Provide courseId or level | [backend/app/modules/vocabulary/flashcards.py:53](../../backend/app/modules/vocabulary/flashcards.py) |
| 401 | INVALID_CREDENTIALS | Incorrect email or password | [backend/app/modules/auth/router.py:159](../../backend/app/modules/auth/router.py) |
| 401 | INVALID_CREDENTIALS | Incorrect email or password | [backend/app/modules/auth/service.py:93](../../backend/app/modules/auth/service.py) |
| 401 | INVALID_REFRESH_TOKEN | Invalid or expired session | [backend/app/modules/auth/router.py:87](../../backend/app/modules/auth/router.py) |
| 401 | INVALID_REFRESH_TOKEN | Invalid or expired session | [backend/app/modules/auth/service.py:28](../../backend/app/modules/auth/service.py) |
| 401 | REFRESH_TOKEN_REUSED | Session reuse detected; please sign in again | [backend/app/modules/auth/service.py:37](../../backend/app/modules/auth/service.py) |
| 401 | UNAUTHORIZED | Authentication required | [backend/app/api/deps.py:17](../../backend/app/api/deps.py) |
| 403 | FORBIDDEN | Origin not allowed | [backend/app/modules/auth/router.py:81](../../backend/app/modules/auth/router.py) |
| 404 | NOT_FOUND | Conversation not found | [backend/app/modules/ai/service.py:56](../../backend/app/modules/ai/service.py) |
| 404 | NOT_FOUND | Course not found | [backend/app/modules/vocabulary/flashcards.py:27](../../backend/app/modules/vocabulary/flashcards.py) |
| 404 | NOT_FOUND | Exercise not found | [backend/app/modules/ai/service.py:268](../../backend/app/modules/ai/service.py) |
| 404 | NOT_FOUND | Flashcard session not found | [backend/app/modules/vocabulary/flashcards.py:82](../../backend/app/modules/vocabulary/flashcards.py) |
| 404 | NOT_FOUND | Lesson not found | [backend/app/modules/ai/context.py:28](../../backend/app/modules/ai/context.py) |
| 404 | NOT_FOUND | Lesson not found | [backend/app/modules/vocabulary/service.py:39](../../backend/app/modules/vocabulary/service.py) |
| 404 | NOT_FOUND | Vocabulary item not found | [backend/app/modules/vocabulary/service.py:20](../../backend/app/modules/vocabulary/service.py) |
| 409 | AI_CONVERSATION_LIMIT | Delete an old conversation first | [backend/app/modules/ai/service.py:104](../../backend/app/modules/ai/service.py) |
| 409 | AI_HISTORY_LIMIT | Start a new conversation | [backend/app/modules/ai/service.py:76](../../backend/app/modules/ai/service.py) |
| 409 | AI_REQUEST_DUPLICATE | Request already received; reload history | [backend/app/modules/ai/service.py:129](../../backend/app/modules/ai/service.py) |
| 409 | EMAIL_TAKEN | An account with this email already exists | [backend/app/modules/auth/service.py:53](../../backend/app/modules/auth/service.py) |
| 409 | EMAIL_TAKEN | An account with this email already exists | [backend/app/modules/auth/service.py:64](../../backend/app/modules/auth/service.py) |
| 409 | EMAIL_TAKEN | An account with this email already exists | [backend/app/modules/users/router.py:43](../../backend/app/modules/users/router.py) |
| 409 | EMAIL_TAKEN | An account with this email already exists | [backend/app/modules/users/router.py:53](../../backend/app/modules/users/router.py) |
| 409 | FLASHCARDS_NOT_COMPLETED | Complete flashcards before testing | [backend/app/modules/vocabulary/flashcards.py:120](../../backend/app/modules/vocabulary/flashcards.py) |
| 409 | PROFILE_MISSING | Profile unavailable | [backend/app/modules/users/router.py:33](../../backend/app/modules/users/router.py) |
| 409 | WORD_EXISTS | Word already saved | [backend/app/modules/vocabulary/service.py:46](../../backend/app/modules/vocabulary/service.py) |
| 422 | AI_INPUT_LIMIT | AI context exceeded input token limit | [backend/app/modules/ai/service.py:158](../../backend/app/modules/ai/service.py) |
| 422 | AI_INPUT_LIMIT | AI input is empty or too long | [backend/app/modules/ai/service.py:44](../../backend/app/modules/ai/service.py) |
| 422 | UNSUPPORTED_EXERCISE_TYPE | Unsupported exercise type | [backend/app/modules/exercises/service.py:262](../../backend/app/modules/exercises/service.py) |
| 422 | VALIDATION_FAILED | Choose a different new password | [backend/app/modules/users/router.py:70](../../backend/app/modules/users/router.py) |
| 422 | VALIDATION_FAILED | Email cannot be null | [backend/app/modules/users/router.py:38](../../backend/app/modules/users/router.py) |
| 422 | VALIDATION_FAILED | Profile fields cannot be null | [backend/app/modules/users/router.py:47](../../backend/app/modules/users/router.py) |
| 429 | AI_BUDGET_LIMIT | Daily AI budget reached | [backend/app/modules/ai/service.py:170](../../backend/app/modules/ai/service.py) |
| 429 | AI_BUSY | AI is busy; try again shortly | [backend/app/modules/ai/service.py:34](../../backend/app/modules/ai/service.py) |
| 429 | AI_BUSY | AI is busy; try again shortly | [backend/app/modules/ai/service.py:152](../../backend/app/modules/ai/service.py) |
| 429 | AI_BUSY | An AI request is already running | [backend/app/modules/ai/service.py:141](../../backend/app/modules/ai/service.py) |
| 429 | AI_RATE_LIMITED | AI provider rate limit reached | [backend/app/modules/ai/provider.py:79](../../backend/app/modules/ai/provider.py) |
| 429 | RATE_LIMITED | Request limit reached | [backend/app/core/limits.py:29](../../backend/app/core/limits.py) |
| 500 | INTERNAL_ERROR | Account could not be loaded | [backend/app/modules/auth/service.py:68](../../backend/app/modules/auth/service.py) |
| 502 | AI_INCOMPLETE_STREAM | AI stream did not complete | [backend/app/modules/ai/provider.py:192](../../backend/app/modules/ai/provider.py) |
| 502 | AI_INVALID_RESPONSE | AI response exceeded limits | [backend/app/modules/ai/provider.py:99](../../backend/app/modules/ai/provider.py) |
| 502 | AI_INVALID_RESPONSE | AI returned invalid practice material | [backend/app/modules/ai/service.py:298](../../backend/app/modules/ai/service.py) |
| 502 | AI_INVALID_RESPONSE | Invalid AI response | [backend/app/modules/ai/provider.py:125](../../backend/app/modules/ai/provider.py) |
| 503 | AI_UNAVAILABLE | AI service is unavailable | [backend/app/modules/ai/provider.py:27](../../backend/app/modules/ai/provider.py) |
| 504 | AI_TIMEOUT | AI request timed out | [backend/app/modules/ai/provider.py:121](../../backend/app/modules/ai/provider.py) |
| 504 | AI_TIMEOUT | AI request timed out | [backend/app/modules/ai/provider.py:188](../../backend/app/modules/ai/provider.py) |
| 504 | AI_TIMEOUT | AI request timed out | [backend/app/modules/ai/router.py:69](../../backend/app/modules/ai/router.py) |
| 504 | AI_TIMEOUT | AI request timed out | [backend/app/modules/ai/router.py:134](../../backend/app/modules/ai/router.py) |
| 504 | AI_TIMEOUT | AI request timed out | [backend/app/modules/ai/router.py:148](../../backend/app/modules/ai/router.py) |

[Error handling](error-handling.md) · [Backend index](README.md)
