# Seed data

app.db.seed owns two legacy published courses: english-foundations (A1), everyday-conversations (B1), six lessons and 18 exercises. Stable slug/ID matching makes reruns idempotent; seed-owned content can update in place. It does not reset users/progress. The CLI refuses APP_ENV=production.

SQLite preparation calls the underlying seed function only when no Course exists, including production startup. It creates catalog records, not demo accounts. app.db.demo is a separate development/demo account workflow with private ignored credential artifacts.

Draft A0–B2 import is separate and never automatic. app.db.curriculum defaults to DB dry-run; --apply-draft inserts unpublished rows after collision checks. UUIDv5 identities and exact-content preflight refuse drift. See [publication](../06-learning/content-publication.md).

[Section index](README.md) · [Documentation home](../README.md)
