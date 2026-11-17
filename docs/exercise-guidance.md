# Exercise guidance (hints, explanations, lesson guides)

> Status: A0–A1 implemented as **draft** content (20 lessons, 160 exercises).
> No AI provider, no database migration, no change to grading or XP.

## Design

The published curriculum (`db/content/curriculum-a0-b2.json`) is pinned by a
publication SHA, so learner guidance lives beside it in
`backend/app/db/content/exercise-guidance-a0-a1.json`, keyed by the existing lesson
and exercise slugs. `app/modules/exercises/guidance.py` validates and serves it.

| Content | Where it appears | When |
| --- | --- | --- |
| `hint` (EN/UK) | `ExercisePublic.hint` | before answering; guides, never states the answer |
| `explanation` (EN/UK) | `SubmissionResult.explanationLocalized` | only after a graded submission |
| wrong-answer note | `SubmissionResult.wrongAnswerNote` | only for an incorrect single choice |
| lesson guide | `LessonDetail.guide` | rule in plain words + English examples with Ukrainian translations |

Wrong-answer notes are looked up by the casefolded text of the chosen option: first an
exercise-specific note, then a lesson-wide note. Vocabulary checks name the word the
wrong translation really belongs to ("«говорити» is the meaning of “speak”, not of
“write”") from the lesson vocabulary list.

## Review gate

The file has `review_status: draft | reviewed`. Anything but `reviewed` is **never
served in production** (`APP_ENV=production`); it is served in local development so it
can be reviewed. A teacher/translator review should then set `reviewed`. Hints cannot
be generated at runtime, so XP, attempts and grading are unaffected.

## Tests (`backend/tests/test_guidance.py`)

Coverage of all 160 A0–A1 exercises, bilingual non-empty text, hints never contain the
correct option, wrong-answer keys refer to real options, curriculum SHA unchanged,
public payload has no explanations, submit reveals them with unchanged XP, production
gate.

## Authoring A2–B2

Add a new sidecar (or extend this one) with the same schema, set `levels`, add the new
slugs and keep hints answer-free. Do not edit the curriculum JSON: a changed SHA needs a
new release decision (`docs/06-learning/content-publication.md`).
