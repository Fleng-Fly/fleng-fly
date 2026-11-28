# Fleng — Reading and Course Words v2

## Reading

30 original topics, six per level A0–B2. Each text has been extended to approximately ten times its original length: 3,168 → 32,348 whitespace-delimited words (10.21×). Questions: 300, ten per text (six single-choice and four True/False), with evidence and a pass mark of 8/10. The old local progress key remains intact; v2 uses a new key because the test length changed. Reading remains browser-local and does not award XP or sync between devices.

| Level | Words per text | Added vocabulary entries |
|---|---:|---:|
| A0 | 309–329 | 117 |
| A1 | 671–720 | 106 |
| A2 | 1,018–1,053 | 105 |
| B1 | 1,451–1,523 | 106 |
| B2 | 1,819–1,924 | 147 |

## Course Words

The bundled CSV adds 581 authored EN–UK entries; it does not contain 25,000 words. On a copy of the supplied database: 1,060 → 1,641 course-word rows (1,012 → 1,593 distinct normalized English terms). Existing duplicates across courses are preserved, not counted twice towards the target. 23,407 further distinct translated terms are required to reach 25,000. Linguistic level placement and translations are authored estimates, not independently certified.

Course Words loads up to 1,000 records per API request and renders 100 at a time, while the existing English/Ukrainian search and save/practise actions cover the loaded catalog. New entries have a course level but no individual lesson, so finishing a lesson will not unexpectedly add hundreds of words to personal vocabulary. Save them to My Words to practise using the existing tests. No CSS or AI modules changed.

### Update existing installation

1. Back up your project and database. Extract the cumulative patch in the repository root, replacing the matching files; do not delete `.env`, `.git`, or `backend/data`.
2. From the repository root, run `npm run db:prepare` to add the bundled entries (idempotent). Start with `npm run dev` as usual.
3. To reach 25,000, obtain an EN–UK dictionary you are permitted to use, with UTF-8 CSV columns `level,word,translation,example` (example may be empty). Allowed levels: A0, A1, A2, B1, B2. Place it at `backend/app/db/content/course-words-25000.csv`.
4. Preview: `npm run db:course-words -- --csv app/db/content/course-words-25000.csv --require-target`.
5. Import after checking the preview: `npm run db:course-words -- --csv app/db/content/course-words-25000.csv --require-target --apply`.

The importer uses published course IDs and preserves existing words/translations. It refuses an insufficient dictionary with `--require-target`, skips normalized duplicates, and stops adding new distinct terms at 25,000. No external dictionary is included or downloaded.

## Verification

- `npm run frontend:test`: 127/127 passed, including 25,001 synthetic rows for Course Words pagination/search and validation of the 30 reading texts and their questions.
- `python scripts/test_course_words_import.py`: passed on isolated SQLite using a synchronous SQLAlchemy test adapter. 25,000 synthetic test records are used only in the disposable test database, not the shipped catalog.
- Import on a temporary copy of the supplied database: 581 added on first run, zero on second; counts of users, lessons, exercises and personal vocabulary unchanged.
- Python syntax compilation passed. Full asynchronous backend integration suite and browser visual tests not run in this environment; async SQLite driver unavailable. No production deployment performed.
