# Local draft curriculum workflow

Normal `npm run dev` preserves the usual database and serves only published content.
A0–B2 is a JSON draft: five courses, 50 lessons, 500 words and 400 exercises.
It is not a production seed and deployment never publishes it.

For development with all five drafts, reuse the existing private preview:

```sh
npm run setup
npm run curriculum:validate
npm run curriculum:preview:prepare -- --directory /tmp/fleng-my-review
npm run curriculum:preview -- --directory /tmp/fleng-my-review
```

Open `http://127.0.0.1:3011/courses.html`. The start command prints the generated
reviewer credentials locally. Preparation runs Alembic, loads the two legacy
courses, imports drafts unpublished and creates a reviewer in a **new isolated**
SQLite file. Seven courses/56 lessons are available to this reviewer, including
all 50 draft lessons. The original local database and its users remain untouched.
Restart with the same `curriculum:preview` command to retain preview progress, XP,
refresh and flashcard sessions. Do not run prepare again on that directory; it
refuses replacement. `/tmp` may be cleaned on reboot. For longer-lived review use
a new absolute private directory outside the repository, whose parent exists.

The factory refuses production mode, requires a private marker and isolated DB,
binds loopback, restricts hosts and permits only its reviewer to read drafts.
It uses existing course/lesson UI and grading services. The normal application
continues to return 404 for drafts; no global include-drafts setting is added.

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
Never add import/publication commands to startup or deploy hooks.

Publication remains separate: complete teacher/translator review, record the exact
canonical SHA and follow [content publication](content-publication.md). The reviewed
SHA operation is allowed in a review database, not production; production promotion
needs a separate approved release. The structural validator does not certify
pedagogical or licensing readiness.
