# Curriculum content quality report

Status: **DRAFT / HUMAN REVIEW REQUIRED**. Structural checks pass; content has
not been approved for publication. No paid AI calls, production seed or automatic
publication was performed. Review scope is the versioned JSON, not live courses.

Validated source SHA-256: `27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013`.

## Inventory

| Level | Lessons | Word entries / course rows | Practice | Checks | Minutes per lesson |
| --- | --- | --- | --- | --- | --- |
| A0 | 10 | 100 / 100 | 50 | 30 | 15 |
| A1 | 10 | 100 / 100 | 50 | 30 | 20 |
| A2 | 10 | 100 / 100 | 50 | 30 | 25 |
| B1 | 10 | 100 / 100 | 50 | 30 | 30 |
| B2 | 10 | 100 / 100 | 50 | 30 | 35 |

Totals: 5 courses, 50 lessons, 500 course-word rows, 400 exercises.
There are 494 distinct normalized spellings across all levels;
6 cross-level occurrences repeat a spelling.
These are legitimate revisits with different contexts (for example, book as a
noun versus book as a verb); they are not duplicate rows within a course.
Each lesson has ten different normalized word spellings. Every course has 100
unique word spellings; no conflicting translations within a course.

Legacy source content is retained separately: two courses, six lessons and
18 exercises. An import into a database containing only the legacy seed gives
7 courses, 56 lessons, 418 exercises and 500 course words. Publication state
is independent: default curriculum import leaves its five courses hidden.

## Automated gates

- Valid levels, unique lesson/exercise slugs and titles, course/lesson/exercise
  source links, contiguous ordering and an acyclic 50-lesson prerequisite chain.
- Nonempty theory, goals, examples, contextual text, translations and options.
- Five practice and three check questions per lesson; one valid server answer
  reference per question; unique choice identifiers and choice texts.
- NFC/casefold normalization of course words; stable source UUIDs.
- Default dry-run causes no writes; draft import is unpublished; rerun adds zero
  rows; exact-SHA publication acknowledged only in isolated integration tests.
- Conflicting existing slugs or edited source rows are refused before writes.
- Published A0–B2 course/lesson/vocabulary reads, 10-card sets, 0/3-card sets,
  completion and test handoff, no personal-word auto-import or flashcard XP.
- Existing lesson payload, progress and XP preserved across import/re-import;
  new graded exercises still award XP once on retry.
- SQLite CHECK migration preserves courses, lessons, submissions, both
  vocabularies and progress with foreign-key cascades enabled. Downgrade refuses
  when A0 content exists. No old migration file was edited.

## Editorial assessment and unresolved limits

All 50 lessons were written as draft in this coding session. No teacher,
translator or CEFR examiner has signed them off. Automated gates do not prove
semantic correctness or the unique correctness of a choice in every context.
Modal, tense and reporting questions specify the intended form or certainty
where alternatives would otherwise be valid; a human must still audit them.

A0–A1 use short contextual sentences, but explanations contain grammatical
terminology. Beginners may need Ukrainian scaffolding and audio. A2 introduces
situational dialogues; B1 adds connected narratives and supported opinions; B2
adds extended professional/academic passages and qualification of arguments.
The 10-lesson-per-level scope is a product starting point, not full proficiency
coverage. Planned time totals are estimates, not measured learner outcomes.

The 150 check questions currently assess three selected vocabulary meanings per
lesson, not all ten words or independent writing. The 250 practice questions are
grammar/usage multiple choice. No new test engine, spelling checker, letter-drag
question, difficult-question retry policy or XP mechanism was created. Practice
and check labels are editorial; the existing frontend uses one shared exercise
list in both tabs. There is no prerequisite locking or separate exam grade.

Lesson vocabulary lists and examples deliberately help learners; only the
Exercise answer-key columns are withheld from public exercise payloads. Optional
per-word examples are empty when not separately authored; each lesson provides
context and worked examples. No invented translations or placeholder theory
were used. Review word senses, register, Ukrainian morphology and inclusive use
of names/pronouns. Legacy introductory/experience lessons overlap some new
skills and remain supplemental; no progress-bearing material was deleted.

Before release: have a teacher review all 50 lessons and all 400 answer keys,
have a Ukrainian speaker review all 500 translations, try the material with
learners, confirm grading expectations and accessible rendering, and approve a
backup/promotion procedure. C1/C2 remain supported but no C1/C2 content is added.
Live PostgreSQL, browser visual/audio testing and production behavior are
**NOT VERIFIED**. PostgreSQL migration SQL compiles offline only.

## Verification evidence

Full pytest: **325 passed, 15 skipped**. Ruff passes; mypy passes (68 source
files). SQLite Alembic upgrade/check/head pass with one head `20261110_1400`.
PostgreSQL migration SQL compiles offline. A separate temporary SQLite smoke
runs dry-run, imports 955 draft rows, then imports zero new rows on repetition.
The content subsequently received a capitalization-only learning-goal edit;
the final targeted rerun covers the current SHA: **29 passed**. DOM regression harness:
`node --experimental-vm-modules scripts/test-courses.mjs` — **7 passed**.
`git diff --check` passes. Existing pytest-asyncio/Starlette/Alembic deprecation
warnings remain. No claim of live PostgreSQL validation is made.

Self-review covered migration cascade safety, identifier ownership, content
immutability, preservation of publication state, answer secrecy, rollback,
packaged JSON availability, frontend filter compatibility and task boundaries.
