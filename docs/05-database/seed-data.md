# Seed data

app.db.seed owns two legacy published courses: english-foundations (A1), everyday-conversations (B1), seven lessons and 21 exercises. Stable slug/ID matching makes reruns idempotent; seed-owned content can update in place. It does not reset users/progress. The CLI refuses APP_ENV=production.

SQLite preparation calls the underlying seed function only when no Course exists, including production startup. It creates catalog records, not demo accounts. app.db.demo is a separate development/demo account workflow with private ignored credential artifacts.

SQLite preparation calls the existing A0–B2 importer with the pinned
owner-authorized publication SHA, including production startup. Fresh SQLite
databases contain seven public courses. All 50 A0–B2 lessons and their 1,000
words are available. Startup imports the vocabulary supplement alongside the
pinned base curriculum and adds 500 words and 500 matching exercises in one
transaction. Words and exercises use stable IDs for repeat imports.
Linguistic review remains incomplete. This imports only
packaged curriculum content, not local accounts, passwords or learning history.
PostgreSQL preparation remains explicit and unchanged. app.db.curriculum defaults to DB dry-run; --apply-draft inserts unpublished rows after collision checks. UUIDv5 identities and exact-content preflight refuse drift. Existing rows/IDs are preserved; only approved curriculum publication flags are
promoted, and conflicting content
causes startup to fail rather than overwrite existing lessons. See [publication](../06-learning/content-publication.md).

[Section index](README.md) · [Documentation home](../README.md)

The sourced vocabulary importer is separate from startup seeding. Run
`python -m app.db.import_vocabulary <release.jsonl> --test-database <prepared-test.db>`
from the backend directory for a dry run, then include `--apply` to insert.
Each JSONL shard is transactional, and rerunning the same shard is idempotent.
The database must already contain published courses and lessons matching the
level on each source entry.
