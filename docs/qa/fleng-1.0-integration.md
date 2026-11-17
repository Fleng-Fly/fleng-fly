# Fleng 1.0 local integration — 2026-11-17

Base: `ba6a4ec321d8eeda71d91470a54ab311b00fc789`.
Backup: `backup/main-before-fleng-1.0-20261117`.
Integration: `release/fleng-1.0-integration`, worktree `/tmp/fleng-1.0-integration`.
No remote fetch/push, deployment, production migration or draft publication.

## Integrated source branches

| Branch | Source commits |
| --- | --- |
| fix/build-reliability | aed3d98 |
| fix/css-cleanup | 1065612 |
| fix/security-stability | c1769e9 |
| feat/placement-test | 8c6b917 (after Security) |
| feat/progress-analytics | 99879f3 |
| feat/progress-ui | aa6fef5 (after Analytics) |
| audit/learning-content | 6c1f679 |
| fix/published-content | 00bf878 (after Audit) |
| fix/draft-curriculum | d8bb2a9 (after Published Content) |
| fix/ai-budget-concurrency | 2342502 |
| release/save-existing-work | bf464f0, ff51ed2, 593597f |
| test/learning-journey-e2e | 156ff18 |

`feat/words-ai-ui` aliases Security's c1769e9; its actual Words/AI work is in
593597f and is included. All thematic worktrees were clean. Main initially had
25 modified tracked and nine untracked files, all byte-identical to their saved
versions in release/save-existing-work; no unfinished edits were imported.

Remote-only import/flashcard branches (`origin/local-import`,
`origin/feat/flashcards-deck`) were inspected but excluded: no completion evidence,
large unrelated historical imports and a conflicting 20261116_1200 migration
identity. Old backup branches have no missing commits relative to main. No foreign
worktree was removed or altered. Remote state reflects existing local refs.

## Conflict resolution and independent review

Merged all frontend test entries and module/documentation additions. Preserved
Security's fail-closed refresh policy on browsers without Web Locks while sharing
one cookie-mutation lock across refresh/login/register/logout. Kept deterministic
AI budget contenders, staggered/streaming coverage and the admission/settlement
regressions from saved work. The first mechanical resolution contained syntax and
conflict-marker errors; f900d05 repairs these, and final syntax/test gates pass.

Separate integration fixes:

- f900d05: reconcile overlapping session coordination and regression suites.
- 83899bd: synchronize email-change/analytics schemas, model/config reference and examples.
- 5b7662c: disable refresh retries for rejected login/register requests; otherwise
  an auth 401 could recursively acquire its already-held cookie lock. Regression added.
- 235f359: exact Email selectors distinguish login from the new recovery form.

Reviewed auth lock lifetime/error paths, backend admission/settlement, migration
lineage, published-versus-draft content and retained branch changes. Published
`curriculum-a0-b2.json` and publication authorization remain unchanged. The new
`.draft.json` stays an explicit editorial candidate requiring human review and a
separate publication decision.

## Validation

| Gate | Result |
| --- | --- |
| Browser E2E | 9 passed, 30.7 seconds; Chromium 1194, two workers, zero retries |
| Backend pytest, SQLite | 2373 passed, 24 skipped, 77 warnings; 405.24 seconds |
| Frontend | 10/10 test files passed, including Placement, Progress, auth and Words/AI |
| Legacy PWA retirement | Both Node scripts passed |
| Ruff app/tests | Passed |
| mypy app | Passed, 89 source files; existing untyped-body informational note |
| Documentation | 0 failures: 158 Markdown files, 655 links, 49 operations, 60 schemas, 23 models, 53 settings, 52 examples |
| Alembic | One head: 20261117_1200 |
| Disposable SQLite | Empty database upgraded through all revisions; current matches head |
| Dependencies | pip check passed; installed versions match constraints except missing tzdata; constrained dry-run resolves tzdata 2026.6 |
| Whitespace/conflict review | git diff --check passed; final files have no conflict markers |

Backend tests used the existing shared virtualenv without modifying it. PostgreSQL
opt-in tests were skipped; no live PostgreSQL, SMTP, paid OpenRouter or production
validation is claimed. Linux uses system zoneinfo; missing tzdata in this existing
environment is recorded, while setup/constraints already declare it. Python 3.14
pytest-asyncio/Alembic deprecation warnings remain.

Restricted sandbox SQLite tests hung; the unrestricted full suite above passed.
Playwright's browser installer downloaded Chromium 1194 but its Node 26 extraction
hung. The downloaded archive was extracted with Python into /tmp and E2E used the
same version through a temporary config overriding only executablePath and absolute
paths. No assertions, application behavior or retries were bypassed. Initial E2E
was 8 passed / 1 ambiguous Email selector failure; fixed in 235f359.

## Local main promotion

All mandatory local gates passed before promotion. Main must still equal the base
and be clean; promotion uses only `git merge --ff-only release/fleng-1.0-integration`.
The original main edits are preserved in stash
`1255b984bdf9f6729c8955693432a6caebeee876` (including nine untracked files).
They were byte-checked against the saved source branch before stashing and are
already represented by the integrated commits; the stash is retained rather than
reapplied over the integrated security policy. The earlier pre-existing stash is
also retained. The final release commit itself is the promoted main HEAD.

Remaining: optional live PostgreSQL coverage (24 skips), real SMTP/OpenRouter,
human editorial review/publication of the draft candidate, and browser installer
extraction reliability under this Node 26 environment. No local application gate
remains blocked.

## Full integration follow-up

The subsequent integration starts at 76ef2b6 and combines CI bb68fb9, platform
polish ca08125 and UX 69cff1c in a new `/tmp/fleng-full-integration` worktree.
The data-flow conflict was merged by preserving both sections. CI commands, all
frontend tests, EN/UK dictionaries, API contracts and the draft A0–A1 sidecar are
retained. Commit 6c3a133 updates radio-option E2E selection for visible option
letters and adds four-width, EN/UK persistence and sidecar browser regressions.
The published curriculum SHA and existing draft curriculum are unchanged; no
production migration, content publication, push or deploy is performed.
Validation: full backend 2386 passed / 25 skipped; frontend 76 passed; Ruff/mypy,
docs/contracts, disposable SQLite Alembic heads/upgrade/drift/integrity, dependency
checks and actionlint pass. Live PostgreSQL and hosted Actions are not claimed.

Final follow-up browser gate: **15 passed** (50.2s), no retries. Four viewport
widths and EN/UK account persistence checked; A0 authored guide/hint/wrong-answer
feedback displayed with zero XP for an incorrect answer. Screenshots reviewed.
All participating source HEADs are ancestors of the final integration commit.
