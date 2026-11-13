# Data integrity

PK/FK/unique/CHECK constraints enforce identities, relationships and state vocabularies; SQLite FK enforcement is explicitly enabled. Ownership is a service query rule in addition to database structure.

Unique user/exercise submissions retain latest attempts and sticky completed/xp_awarded flags. Unique user/lesson progress prevents repeat aggregate completion. Activity is unique per user/day. Refresh rotation atomically claims/links successors; password/reset invalidates refresh sessions within the write transaction.

Flashcard cards are JSON snapshots, not source-word FKs: deletion of a source does not erase the session. Completion changes status/time, not cards, XP or review schedules. Vocabulary deletion explicitly removes its review rows.

Curriculum imports refuse content/identity conflicts rather than rewriting used content. Backup/restore remains an operator responsibility. Idempotency and migrations do not establish durable hosting storage.

[Section index](README.md) · [Documentation home](../README.md)
