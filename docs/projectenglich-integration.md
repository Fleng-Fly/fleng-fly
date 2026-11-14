# Local project integration — 2026-11-14

Integrated `projectenglich` into the Git checkout `fleng-fly`. The source was
a portable distribution without Git metadata. Three-way merges used repository
commit `b64ee7a` as the shared baseline; line-ending-only differences were ignored.
Existing curriculum drafts, validation, reviewer tooling, flashcards and numbered
developer documentation remain in place. No push or deployment was performed.

## Changes

- Letter-tile text exercises, server validation, automatic question advancement,
  delayed retries and self-check completion only after a correct assessment.
- An additional legacy demonstration lesson, without replacing existing lessons.
- Cross-platform npm backend commands and Windows timezone support.
- PWA installation page, manifest/icons and offline screen. The worker caches
  only that public screen; API requests and personal pages are not cached.
- `desktop/` owns a loopback FastAPI subprocess and a dedicated Edge/Chrome
  window on Windows, with persistent user data and process lifetime management.
  Linux source launch uses optional pywebview/Qt. Windows source setup does not
  install pywebview because the Windows launcher uses the existing browser.

## Database compatibility

The two projects independently used revision `20261110_1200`: this repository
for vocabulary/flashcards, the portable distribution for `letter_tiles`.
The new revision `20261114_1200` follows the existing A0 revision `20261110_1400`.
It adds the column for ordinary repository databases. For legacy desktop databases
where the column already exists and both vocabulary tables are absent, it runs
the existing vocabulary migration. A partially present vocabulary pair is rejected.
No existing revision is renamed or manually restamped.

The source development database was copied with SQLite backup into the previously
absent, ignored `backend/data/fleng.db`. Preparation and seed completed on that
copy. The original database and `%LOCALAPPDATA%/Fleng` were not modified. Desktop
startup upgrades its own database when the user next launches the application.

`runtime/`, `Fleng.exe`, `BUILD-MANIFEST.json` and `WINDOWS-DEPENDENCIES.txt` were
copied locally and are ignored release artifacts. The manifest describes the
original binary/runtime distribution, not a rebuild of this combined source.
`desktop/build_windows.py` builds a fresh distribution from committed source.

## Windows adaptation

SQLite configuration uses forward-slash paths; diagnostics compare resolved paths,
so slash direction does not report a false engine mismatch. Text fixtures specify
UTF-8 and subprocess fixtures use portable Python paths.

The private curriculum reviewer depends on POSIX ownership, permission bits and
file locks. On Windows it now reports that limitation before writing files instead
of raising an AttributeError. Its POSIX-only tests skip on Windows; an additional
test verifies refusal. Ordinary courses, draft validation and learning work on
Windows. Live PostgreSQL and browser installation remain separate verification.

## Review and validation

Self-review checked three-way merge results, migration ordering and legacy schema
compatibility, unchanged course drafts, once-only XP, API answer-key protection,
worker cache boundaries, desktop process ownership, generated files and secrets.
Migration tests cover fresh repository and legacy desktop paths, schema drift,
foreign keys, content preservation, downgrade and re-upgrade.

- Combined backend/desktop pytest: **382 passed, 22 skipped** on Windows.
  Skips cover unavailable PostgreSQL, POSIX-specific permissions/reviewer flows
  and the platform-specific skipped cases. Five desktop lifecycle checks passed.
- Ruff, mypy (77 app files), additional desktop/migration lint and diff whitespace
  checks passed. Existing Starlette/Alembic deprecation warnings remain.
- PWA worker/install interaction tests and 24 JavaScript catalog/AI tests passed.
- Alembic reports one head, `20261114_1200`; schema drift check is clean.
- Copied legacy database preparation and idempotent seed passed through Windows
  npm commands; original source and desktop user databases were left unchanged.
- OpenRouter secret scan found zero concrete secrets. Local databases, user keys,
  environments and release binaries are excluded from commits.

Not exercised: opening the real Windows GUI, rebuilding the native EXE, Linux GUI,
physical-device PWA installation, live PostgreSQL/SMTP/OpenRouter or deployment.
