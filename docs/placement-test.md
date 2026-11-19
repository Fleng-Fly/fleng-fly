# Placement Test MVP

The private page is `/placement-test.html`, part of the Courses area (breadcrumb
"Courses / Placement Test", Courses highlighted in the sidebar, entered from the "Find your
level" link on `/courses.html`; it has no sidebar item of its own). It uses the shared dashboard
layout and shows the intro block, the four CEFR cards (the newest completed attempt's level is
marked "CURRENT LEVEL") and the attempt history (level badge, date, `correct / total`, View
results/Resume). While answering, only the questions are shown. `GET /placement-test/attempts`
additionally returns `correct` for completed attempts. This feature is isolated from AI,
Words, auth/security behavior and lesson grading. It uses
existing JWT authentication and the existing same-origin API client. No XP,
profile level, lesson/course progress, streak or achievement is written.

## Scope and assessment limits

The bank contains 36 original Fleng multiple-choice items, six each with
**provisional editorial difficulty tags** A1–C2. Skills sampled are grammar,
vocabulary and short reading. Each item has four distinct options, one key and an
explanation. Automated integrity checks and implementation review do not establish
external linguistic approval or CEFR calibration. No teacher-approved bank was
supplied. `review_status=internal_checks_only` explicitly records this limit.

The [Council of Europe self-assessment grid](https://www.coe.int/en/web/common-european-framework-reference-languages/table-2-cefr-3.3-common-reference-levels-self-assessment-grid)
covers listening, reading, spoken interaction/production and writing. This MVP
samples only part of that scope. It does not reproduce CEFR descriptors or copy
exam questions, and is not an endorsed or certified CEFR examination. The
[Council of Europe examination-linking manual](https://www.coe.int/en/web/common-european-framework-reference-languages/relating-examinations-to-the-cefr)
is a methodology reference, not proof that this bank is calibrated.

Scoring version `conservative-1` is a transparent product heuristic:

1. Every saved answer earns one raw point only if it matches the private key.
2. For a study starting-point estimate, consecutive A1, A2, B1 and B2 bands must
   each have at least six questions and at least five-sixths correct. A failed or
   undersupplied lower band stops promotion; harder answers cannot bypass it.
3. The maximum estimate is B2. A ceiling result says **B2 or above on this limited
   test; C1/C2 are not determined**. C1/C2 raw scores are exploratory only.
4. If A1 does not meet the threshold, the estimate is null with a below-A1-test-
   threshold label; this is not an assertion of a validated A0 CEFR level. Existing
   introductory A0 courses can be suggested. Missing A1 coverage instead yields
   insufficient evidence and no inferred course level. A smaller sufficient bank
   reduces the declared assessment range rather than inferring untested bands.
5. Every result is labelled `reliability=limited`. No numeric confidence interval
   is fabricated. Listening, speaking, writing, timed performance, external
   calibration and teacher sign-off remain outside this release.

Before using results for high-stakes placement, obtain teacher/CEFR assessment
review, evaluate item ambiguity and difficulty with learners, calibrate cutoffs,
expand skill coverage and use independently reviewed alternate forms. Retakes
reuse this bank, so prior exposure to released keys can inflate subsequent scores.
No AI provider is involved in selection, grading or recommendations.

## Data and API

`placement_attempts` is one owned table: UUID, user FK, bank/scoring versions,
status, private question/key snapshot, selected answers, stored result, start and
completion timestamps. Snapshots preserve an in-flight attempt and old result
when the packaged bank changes. Completed results are immutable. If an unfinished
attempt refers to an unsupported scoring version, completion refuses explicitly;
future scoring upgrades must retain old evaluators or require a new attempt.

- POST `/api/v1/placement-test/attempts`: new independent attempt, shuffled question
  and option order; 20 starts per user per UTC day through existing DB rate limits.
- GET `/api/v1/placement-test/attempts?limit=20&offset=0`: owned history, including
  resumable unfinished attempts; maximum page size 100.
- GET `/api/v1/placement-test/attempts/{id}`: resume or inspect owned result.
- PUT `/api/v1/placement-test/attempts/{id}/answers`: save one/batched selections;
  duplicate question IDs, foreign questions/options and unknown request fields
  are rejected. Correctness is not returned.
- POST `/api/v1/placement-test/attempts/{id}/complete`: requires all answers,
  performs deterministic scoring once and reveals keys/explanations only now.
  Repeated completion returns the stored result instead of creating another one.

Every route requires an access JWT. Another user's/missing attempt returns 404.
Only the owner-scoped attempt row is locked for writes: a no-op UPDATE takes the
SQLite write lock / PostgreSQL row lock before reading current answers. This
prevents parallel partial saves from losing one another and serializes completion
with editing. No learner/profile row or security implementation is modified.

Question DTOs explicitly exclude keys and explanations. The bank is backend-only
`app/db/content/placement-v1.json`, included by the existing package-data rule;
it is not a frontend asset. No response before completion includes correctness,
answer keys or answer explanations. The browser never calculates the result.

Suggestions use the existing published-course catalog query with the estimated
level (A0 for a below-A1 test threshold). No draft, invented or substitute-level
courses are returned. An empty match is explained honestly. Recommendations
reflect the currently published catalog; the score/review itself stays frozen.

## UI and recovery

The page has its own scoped stylesheet and no sidebar/Dashboard integration.
Start, previous/next, next unanswered, confirmed autosave, finish, history,
pagination, resume and retake are available. The URL holds only an attempt UUID;
answers/results remain server-owned. A failed save does not advance the question
or reveal correctness. An ambiguous start/completion failure asks the user to
refresh history/reload the attempt instead of silently repeating a POST. All
server text is rendered through textContent/DOM creation; no raw HTML rendering.

## Migration and verification

Apply `npm run db:migrate` against a backed-up development/staging database before
serving this version. Revision `20261117_1200` follows Security's `20261116_1400`
and only creates the new table/index. Existing auth, accounts and learning tables
are unchanged. Downgrade removes placement history only; it must be an explicit
operator choice. No migration was applied to the user's main database here.

Regression coverage includes API auth/ownership, no premature keys, invalid
answers, score thresholds, limited range, retakes, published-only recommendations,
nonzero XP/progress preservation, real SQLite parallel saves/completion, restart
persistence, migration up/down/drift and frontend start/resume/error/result flows.
Results and outstanding environment checks are recorded in the placement plan.


Verified implementation: full pytest 517 passed / 24 skipped; dedicated placement
22 passed; seven frontend test files pass (three placement behavior checks), Ruff,
mypy and git diff --check pass. Five existing Security contract-documentation
failures reproduce unchanged on c1769e9; details are in the
[placement plan](../plans/placement-test.md). No live PostgreSQL, external teacher
sign-off, empirical calibration or real-device/browser interaction is claimed.
