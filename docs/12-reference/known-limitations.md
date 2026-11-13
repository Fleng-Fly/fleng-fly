# Known limitations

Backend completion does not imply UI/production completion. Dedicated Vocabulary/Flashcards/AI Tutor/reset pages are absent; lesson saved-word UI/floating assistant exist. Numeric progression, adaptive SRS, billing, notifications, audio/speaking assessment and a separate vocabulary testing/XP engine are absent.

Five A0–B2 courses remain drafts. Structural tests, narrow heuristics, mocked sources and SHA acknowledgement do not establish linguistic/translation/CEFR approval. Prerequisites are metadata; Practice/Test share exercise lists; word examples can be empty.

Live PostgreSQL, production proxy/TLS/cookies/SSE, real OpenRouter/SMTP and backup/restore are unverified here. Netlify API proxy is commented out; recorded public URLs are not availability claims. Ephemeral SQLite loses data.

Verified code issue: Settings with explicit sqlite+aiosqlite:///:memory: duplicates its driver; sqlite:///:memory: works. Application code is unchanged. Production preparation rejects memory DBs.

Security gaps: no MFA/email verification, old JWTs valid until expiry, duplicate-email enumeration, no refresh-specific quota, extras not globally forbidden and no complete CSP/edge policy. Strict refresh reuse interacts with browser concurrency. Dependency ranges are not a frozen Python lock; historical warnings/plans are not universal compatibility guarantees.

[Section index](README.md) · [Documentation home](../README.md)
