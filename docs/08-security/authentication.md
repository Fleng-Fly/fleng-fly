# Authentication

Argon2id hashes passwords; hash/verify runs outside the event loop through at most four workers/event loop. Registration enforces 8–128 characters; login allows 1–128. Identity emails normalize. EMAIL_TAKEN registration reveals duplicates, so account enumeration is not fully prevented. Reset requests use a generic response.

PyJWT access tokens default HS256/15 minutes and subjects resolve to real users. Opaque refresh tokens live in HttpOnly cookies; only SHA-256 hashes persist. Atomic rotation revokes/links the successor, and reuse revokes all user refresh sessions, including concurrent successors.

Logout revokes the presented refresh token. Password changes/resets revoke refresh sessions/unused reset tokens atomically. Existing JWTs remain valid until expiry: no denylist, MFA, email verification or OAuth exists. Refresh has no dedicated rate limiter.

[Section index](README.md) · [Documentation home](../README.md)
