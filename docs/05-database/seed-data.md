# Seed data

app.db.seed owns two legacy published courses: english-foundations (A1), everyday-conversations (B1), seven lessons and 21 exercises. Stable slug/ID matching makes reruns idempotent; seed-owned content can update in place. It does not reset users/progress. The CLI refuses APP_ENV=production.

SQLite preparation calls the underlying seed function only when no Course exists, including production startup. It creates catalog records, not demo accounts. app.db.demo is a separate development/demo account workflow with private ignored credential artifacts.

SQLite preparation now also calls the existing A0–B2 importer with unpublished
drafts, including production startup. Fresh SQLite databases therefore contain
seven courses; five remain hidden from public catalog routes. This imports only
packaged curriculum content, not local accounts, passwords or learning history.
PostgreSQL preparation remains explicit and unchanged. app.db.curriculum defaults to DB dry-run; --apply-draft inserts unpublished rows after collision checks. UUIDv5 identities and exact-content preflight refuse drift. Existing rows/IDs and publication flags are preserved; conflicting draft content
causes startup to fail rather than overwrite existing lessons. See [publication](../06-learning/content-publication.md).

[Section index](README.md) · [Documentation home](../README.md)
