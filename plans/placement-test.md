# Placement Test MVP

Branch: feat/placement-test, separate worktree based on c1769e9 (Security).
Implementation was initially prepared without commits. Finalization now authorizes
one Placement-only commit; merge, rebase and push remain prohibited.

## Completed implementation

- Independent attempt model, additive Alembic migration, private versioned bank.
- Original 36-question bank, six provisional tags per A1–C2, explicit keys/rationales.
- JWT-owned start/history/resume/autosave/complete, immutable stored results.
- Deterministic consecutive-band heuristic with B2 ceiling and limited reliability.
- Existing published-course recommendations, no learner/profile/XP changes.
- Standalone placement-test.html and scoped CSS; no Dashboard/Words/AI edits.
- API/scoring/retake/privacy, SQLite concurrency/restart/migration and DOM regressions.
- Existing migration-head assertions updated to the new revision; old migration
  files and deliberate historical-stamp fixtures preserved.

## Verification completed

- Full backend: **517 passed, 24 skipped**, 77 existing/framework warnings,
  319.43 seconds. PostgreSQL-dependent/environment cases are not claimed verified.
- Targeted placement API/storage: **22 passed**, including real SQLite migration,
  parallel partial saves, idempotent completion and restart persistence.
- Frontend: all **7 test files pass**; dedicated placement module has **3 behavior
  checks** for start/save/result/retake, URL resume and failure recovery.
- Ruff passes for app/tests and the new migration; mypy passes for 89 source files.
  Existing AI annotation-unchecked note remains. `git diff --check` passes.
- Documentation links: 151 Markdown files / 645 local links checked. Runtime
  contract checker has **5 pre-existing Security documentation failures**:
  missing two Email Change operations, two Email Change schemas, EmailChange model
  and Settings inventory drift (operation mismatch is one reported failure).
  Running the same checker on clean c1769e9 reproduces exactly the same five;
  no placement operation/schema/model mismatch was introduced. Security artifacts
  were not rewritten to hide the baseline issue.
- Independent self-review checked projection of private answer keys, own-resource
  filtering, write-lock order, immutable results, reduced assessment range,
  no-learning-write guarantees and scoped frontend behavior. It caught and fixed
  SQLite UTC response inconsistency; native save focus is restored after controls
  are re-enabled.
- Main/user databases were not migrated. Only disposable test databases were used.
  Existing virtualenv packages were reused locally; no dependency was installed.
  At the implementation checkpoint no commit, merge or push was performed;
  the source worktree was clean.

## Pending validation / next

- No teacher-approved bank was supplied; no external sign-off or psychometric
  calibration is claimed. Current result is approximate course guidance only.
- Listening/speaking/writing and reliably separating C1/C2 are intentionally absent.
- Review with an educator, pilot/calibrate items and cutoffs, and introduce reviewed
  alternate forms before high-stakes placement or stronger proficiency claims.
- Live PostgreSQL and physical-device/browser interaction checks are not yet verified.
- Production deployment/migration and final editorial acceptance remain owner actions.

## Finalization verification

Placement API/storage tests repeated: 22 passed; placement DOM checks: 3 passed;
all seven frontend test files and targeted Ruff pass. Migration chain has one
head (20261117_1200), linked to 20261116_1400. Existing nonzero XP/profile/progress
preservation and SQLite upgrade/downgrade checks pass. Reviewed feature files have
no detected credentials/runtime artifacts. Baseline Security documentation failures
remain outside scope. A single feature commit is explicitly authorized.
