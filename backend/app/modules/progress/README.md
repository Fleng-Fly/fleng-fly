# Personal learning analytics

Implemented locally on `feat/progress-analytics`. This module extends the existing
endpoint without duplicate routes, tables, migrations or XP/streak writes.
Documentation stays here to respect the progress-module-only task boundary.

## API

`GET /api/v1/progress/me` requires Bearer authentication. Identity comes only from
the token, never a query-supplied user ID. Missing/invalid credentials return 401.
Existing response keys remain; additions are:

- `activeCourses`: visible courses with at least one started lesson and fewer
  completed lessons than their visible lesson total. Fully completed, untouched
  and empty courses are not active. This means retained progress, not recent
  engagement; there is no enrollment/abandonment model.
- `courses[].completionPercent`: completed visible lessons / all visible lessons
  * 100, rounded to two decimal places; 0.0 for an empty course. Unstarted lessons
  remain in the denominator. Normal requests include published courses/lessons;
  existing explicit local draft-preview visibility is preserved.
- `streak`: `{current, longest, lastActivityDate, timezone}`, from the existing
  gamification read service, identical to `GET /api/v1/streaks/me`.
- `xpHistory`: `{available: false, reason: "XP_AWARD_HISTORY_NOT_RECORDED",
  last7Days: null, last30Days: null}`. Null means unavailable, not zero XP.

## Existing sources and limitations

| Metric | Source | Meaning |
| --- | --- | --- |
| lessonsStarted | Own LessonProgress rows | Includes completed lessons |
| lessonsCompleted | Own LessonProgress rows with status completed | Retained lifetime completion |
| courses / completionPercent | Courses + lessons joined to own LessonProgress | Current catalog visibility |
| activeCourses | Existing course breakdown | Started but not fully complete |
| exercisesCompleted | Own ExerciseSubmission.completed | One retained row per exercise |
| xp | Profile.xp | Stored cumulative total |
| streak | LearningActivity.day + existing gamification service | Recorded days in configured learning timezone |
| studyMinutes / lastActivityAt / updatedAt | Progress | Existing stored fields; no new time measurement |

Read totals now use actual LessonProgress state, fixing missing/stale aggregate
counters without repairing or writing Progress. They include retained progress
on now-hidden lessons/courses; lifetime totals need not equal the sum of visible
course counts. Deleted lessons cascade-delete their progress, so this is not an
archival ledger. Catalog edits can change completion percentages; no historical
course snapshot exists.

LearningActivity records activity, not XP. ExerciseSubmission stores the latest
attempt: retries overwrite submitted_at. It has only an xp_awarded flag, without
an immutable award timestamp or awarded amount; current Exercise.points can also
change. Profile.xp has no daily breakdown. Neither a 7-day nor a 30-day XP timeline
can therefore be reconstructed reliably. No estimated or zero-filled history is
returned, even for new users. A future award ledger would not restore missing old
history and is outside this task.

Streaks represent recorded history only; missing legacy days are never inferred.
Current streak includes a run ending today or yesterday; longest covers recorded
history under the existing policy. XP/streak award logic is unchanged. Missing
Progress/Profile rows produce zero stored totals/null aggregate timestamps while
real LessonProgress remains counted, with no rows created by reads.

## Queries, review and verification

Seven SELECT queries including authentication/profile loading, independent of
course/lesson count. Course aggregation is one grouped query; no per-course
queries. Streak reads the user's activity-day list. As before, separate reads are
not a transactionally frozen snapshot under concurrent lesson submissions.

Tests in `backend/tests/test_progress_analytics.py` cover empty/legacy users,
stale aggregates, lifetime vs visible totals, partial/complete/empty courses,
rounding, streak expiry, invalid credentials, two-user isolation, no inferred XP
history and constant SELECT count with catalog growth. Existing lesson/grading,
progress/streak and draft-preview regressions are also run.

Independent self-review checked visibility joins, all ownership filters, read-only
missing-row handling, query count and reuse of existing streak policy. No frontend,
Security, Words, AI, migration or award changes. No commit, merge or push.

Local verification: `test_progress.py`, `test_progress_analytics.py`,
`test_exercises.py`, `test_learning_extensions.py`, `test_development_drafts.py`
and `test_stabilization.py`: **78 passed, 14 skipped** (PostgreSQL unavailable).
Full-backend Ruff check and mypy (82 source files) passed. `git diff --check`
passed. Live PostgreSQL was not exercised; the full unrelated suite was not run.
