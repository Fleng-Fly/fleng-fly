# Draft curriculum quality fixes

Branch: `fix/draft-curriculum`, based on `fix/published-content` at `00bf878`.
Scope: the four confirmed findings M3, M2, H1 and M4 in
[the learning-content audit](learning-content-audit.md). No AI/provider API calls.

## Separate editorial candidate, not a release

The historical audit calls `curriculum-a0-b2.json` a draft because its status is
`draft`. However, `app/db/prepare.py` now pins that same file's canonical SHA as an
owner-authorized public release. Editing it would invalidate startup approval and
risk conflating a proposed fix with a published update.

Therefore the corrected candidate is **`backend/app/db/content/curriculum-a0-b2.draft.json`**.
The default runtime JSON, `seed.py`, grading code and publication SHA are unchanged.
Nothing was imported into an application database or published. Normal startup
continues to read the original, pinned release; these fixes do not silently reach
existing learners. The draft is not wired into runtime or the default import CLI.

The candidate retains the existing five levels, 50 lessons, IDs, positions,
prerequisites, goals, grammar descriptions, worked examples, 400 exercises and 500
word/gloss pairs. The four former strict xfail tests now run normally against the
corrected candidate. Existing seed/runtime tests still cover the unchanged release;
an additional regression verifies the old approval SHA cannot authorize this draft.

## Changes and measured results

| Finding | Change | Remaining in candidate |
| --- | --- | --- |
| M3 | 500/500 vocabulary examples filled with short contextual English sentences | 0 empty |
| M2 | All 400 answer positions reassigned; actual option order changed in 333 exercises; IDs/keys kept consistent | Positions 1/2/3: 133/133/134; all 50 lesson patterns distinct; every lesson uses all positions |
| H1 | All 145 confirmed gap-fill copies replaced with independent contexts; additionally replaced 5 direct question/number copies without gaps | 0 copies, including checks against new vocabulary examples |
| M4 | All 83 audit omissions given reading context; whole-word matching and exclusion of incorrect distractors found 40 additional context gaps after rewriting, also filled | All 500 words occur in lesson text, worked examples or prompt/correct answer; 123 supplemental reading sentences added |

The original detector counted 145 gap-fill copies, but omitted five repeated
non-gap questions (two letter questions and three number questions). All 150 are
replaced. The generic punctuation stem remains the same; its full-sentence options
now carry a different task. Among these 150 exercises, six correct answer texts
changed to match new spelling/number/plural/punctuation questions; the other 144
retain the original answer. All other 250 exercise prompts remain unchanged.
All 150 vocabulary-check questions retain their word, gloss and distractor meaning.

Two replacement first-conditionals remove `would` as a distractor in favour of
`was`, preserving the intended `will` answer. Passive and result-connector tasks
state their target explicitly. Independent self-review also refined a road-crossing
prompt and a past-counterfactual result to avoid alternative readings. Explanations
were rewritten for the new contexts. Every key is checked against its expected
answer text and the existing real grader; option reshuffling must not change meaning.

## Validation and regression checks

From the repository root, with the existing backend virtualenv:

```sh
python scripts/validate_curriculum.py --input backend/app/db/content/curriculum-a0-b2.draft.json
python scripts/validate_curriculum.py
```

The first validates the corrected candidate explicitly; the second confirms the
runtime source remains valid and unchanged. Candidate: 5/5 courses, 50/50 lessons,
400/400 exercises and 500/500 words structurally valid; no missing examples;
**0 critical/high/medium issues; 107 info**. Original source: its previous
**2 medium / 107 info** remain, as expected for the unmodified released artifact.

Targeted pytest, from `backend/`:

```sh
python -m pytest -q tests/test_content_structure.py tests/test_draft_quality_fixes.py tests/test_curriculum.py tests/test_curriculum_validation.py tests/test_exercises.py
```

The new regressions check short examples and exact headword context, immutable
lesson structure and glosses, independence from all worked/vocabulary examples,
actual displayed answer positions, all correct and incorrect options through the
real grader, unchanged keys except the six explicitly changed tasks, preservation
of published approval and draft-only import into a disposable test database.

Ruff covers `backend/app` and `backend/tests`; `git diff --check` is required.
Final checks: **1880 passed in 58.22 seconds**, no skipped/xfail cases in the
selected suite; Ruff passed for all backend app/tests; `git diff --check` passed.
pytest-asyncio prints its existing unset fixture-loop-scope deprecation warning.
The full unrelated backend suite was not run.

## Editorial status and remaining decisions

**AI-assisted editorial draft; not teacher-reviewed, externally verified or
approved for publication.** Examples were written with short A0/A1 constructions
and more complex B1/B2 contexts; this is an editorial intention, not validated CEFR
placement. Mechanical tests cannot prove grammar, pragmatics, unique natural
answers, translation senses or pedagogical effectiveness. The validator reports
0 externally verified words and requests human review of 500 words / 50 lessons.
No paid review or invented evidence was used.

The four requested defects are mechanically resolved in this candidate; unrelated
findings remain open, notably grammar/reading coverage in the check phase (H3),
gloss senses (M6), curriculum overlap/level decisions (M11) and exercise-type /
distractor difficulty (M10). Existing worked-example ambiguity also needs teacher
review; this task does not certify or silently revise all teaching text.

A teacher/translator must review the candidate before a separate publication
decision. The importer deliberately rejects content conflicts with already imported
stable IDs: future deployment needs an explicit version/update strategy preserving
learner submissions, not copying this file over the pinned release or changing the
approval constant automatically.

## Candidate identity (not publication approval)

Canonical candidate SHA: `6693f8f066507cd94182d51d8ee2dae25aa9b94745ba9c03c97a4100b2a33fc0`.

Raw candidate file SHA: `d844a10a1f50e861dcd59a91b504d3a8c9edadf9aebbe848bbdce178d8566d5b`.

Owner-authorized release SHA stays
`27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013`.
No merge, rebase, push, database deployment or publication was performed.
