# Local draft curriculum workflow

Normal `npm run dev` now uses the existing local SQLite database and shows all
seven courses (two legacy + five A0–B2 drafts) after ordinary login at
http://127.0.0.1:3001/courses.html. Existing accounts and progress remain in that
file. The local-only launcher takes an online private backup before preparation,
applies existing migrations, and imports drafts idempotently without publishing
them. Backup paths are printed locally; temporary backup directories may be cleaned
by the OS, so copy important backups to private durable storage.

This dev launcher binds only 127.0.0.1, checks Host/client loopback, and refuses
production/Render and non-file-SQLite settings. Production `run.py` and ordinary
`app.main:app` retain published-only routes. SQLite production startup also loads the packaged drafts, but its public routes
continue to hide unpublished content.

For a separate reviewer account and database, the private preview remains available.
For a separate isolated review of all five drafts, use the existing private preview:

```sh
npm run setup
npm run curriculum:validate
npm run curriculum:preview:prepare -- --directory /tmp/fleng-my-review
npm run curriculum:preview -- --directory /tmp/fleng-my-review
```

Open `http://127.0.0.1:3011/courses.html`. The start command prints the generated
reviewer credentials locally. Preparation runs Alembic, loads the two legacy
courses, imports drafts unpublished and creates a reviewer in a **new isolated**
SQLite file. Seven courses/57 lessons are available to this reviewer, including
all 50 draft lessons. The original local database and its users remain untouched.
Restart with the same `curriculum:preview` command to retain preview progress, XP,
refresh and flashcard sessions. Do not run prepare again on that directory; it
refuses replacement. `/tmp` may be cleaned on reboot. For longer-lived review use
a new absolute private directory outside the repository, whose parent exists.

The factory refuses production mode, requires a private marker and isolated DB,
binds loopback, restricts hosts and permits only its reviewer to read drafts.
It uses existing course/lesson UI and grading services. The ordinary app factory continues to return 404 for drafts; only guarded local
entry points opt in. No global include-drafts setting is added.

To import unpublished content into an explicitly configured development DB:

```sh
npm run db:migrate
npm run curriculum:import-drafts
```

This alone does not make drafts visible in the normal app; use the preview above
for viewing. UUIDv5 IDs derive from versioned source keys; re-import adds no
duplicates, does not overwrite existing exercises or progress and refuses source
key/content conflicts before writing. Production CLI writes are rejected.
Course/level word filtering and lesson/exercise ownership use existing services.
Draft import belongs only to the guarded local npm dev launcher; never add it
or publication commands to production startup/deploy hooks.

Publication remains separate: complete teacher/translator review, record the exact
canonical SHA and follow [content publication](content-publication.md). The reviewed
SHA operation is allowed in a review database, not production; production promotion
needs a separate approved release. The structural validator does not certify
pedagogical or licensing readiness.

## Default-launch verification — 2026-11-14

The existing local database was backed up before importing 955 curriculum rows.
It now contains seven courses, 56 lessons (six pre-existing + 50 drafts), 418
exercises and 500 course words. All pre-existing accounts, profile XP, progress,
submissions, catalog rows and personal vocabulary were preserved. A newly seeded
empty database has the additional present-perfect lesson from the team update;
existing catalogs are not overwritten by default preparation.

An actual `npm run dev` run on port 3001 verified all seven courses with an existing
account, all 50 draft lesson payloads and all 500 course words over HTTP. A restart
preparation reported zero new rows / 955 existing rows. Targeted development/private
preview checks: 17 passed, one platform skip; the known upstream lesson-count
assertion was excluded from this focused run. Ruff, mypy, frontend Node checks and
Markdown links pass. The SQLite startup follow-up updated the stale 56-vs-57 preview count and old
Test-tab asset expectation. The full regression run now passes with **406 passed /
18 skipped**. No production visibility rule was relaxed to hide a failing test.

The shared private reviewer continues to reject other users. Default local draft
access instead requires ordinary learner authentication, a loopback client/Host,
development mode and a persistent SQLite URL; production/Render/PostgreSQL/in-memory
configuration is rejected. Separate security tests cover both existing-user access
and once-only XP plus anonymous/remote/normal-app rejection.
