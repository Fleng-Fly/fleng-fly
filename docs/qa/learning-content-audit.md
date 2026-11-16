# Learning content audit

Audit date: 2026-11-16. Branch: `audit/learning-content`, from `main` (`ba6a4ec`).
Scope: read-only. No lesson, API, UI, migration or CSS file was changed. The only
additions are this report and `backend/tests/test_content_structure.py`.

## How this was done

- Every lesson, exercise and word was read by a reviewer (no AI API was used). Machine checks
  were used for counting and cross-referencing.
- `scripts/validate_curriculum.py` was run (exit 0: no blocking defects; 2 `medium`, 107 `info`).
  Its two `medium` items are included below.
- A second, independent set of structure checks was added as
  `backend/tests/test_content_structure.py` (see [Automated checks](#automated-checks)).
- Grammar and CEFR judgements are a reviewer's opinion, not an external corpus check. The
  validator reports that no licensed evidence dataset is configured, so linguistic evidence is
  `not_run`. **A teacher must confirm every finding before the content is changed or published.**

## What exists, and what is live

| Source | Status | Courses | Lessons | Exercises | Words |
| --- | --- | --- | --- | --- | --- |
| `backend/app/db/seed.py` | **Published** (`is_published = True`) | 2 (A1, B1) | 7 | 21 | none |
| `backend/app/db/content/curriculum-a0-b2.json` | **Draft** (`status: draft`, not imported by default) | 5 (A0–B2) | 50 | 400 | 500 |

Learners currently see only the seed catalog. The JSON curriculum is large but unpublished, so
its findings are pre-publication defects. The seed findings affect real learners now.

## Statistics

| Item | Count |
| --- | --- |
| Lessons reviewed | 57 (50 draft + 7 seed) |
| Exercises reviewed | 421 (400 draft + 21 seed) |
| Vocabulary entries reviewed | 500 (494 unique words) |
| Answer keys checked | 421 — **0 wrong keys found** |
| Draft practice exercises / check exercises | 250 / 150 |
| Draft exercise types | 400 `single_choice`, 3 options each |
| Seed exercise types | 7 `single_choice`, 8 `text` (1 with letter tiles), 6 `self_check` |
| Draft lessons with identical structure (5 practice + 3 check) | 50 of 50 |
| Prerequisite chain | valid, 50 of 50 |
| Duplicate prompts | 0 in the JSON; 1 near-duplicate group in the seed |
| Vocabulary example sentences filled | 0 of 500 |
| Vocabulary words never used in their lesson | 83 of 500 (16.6%) |
| Practice items identical to a worked example | 145 of 250 (58%) |
| Words tested by a check exercise | 150 of 500 (30%) |

Counts above were produced by the scripts in this audit and are reproducible with the tests.

## Severity scale

- **critical**: wrong answer key, harmful or unsafe content. None found.
- **high**: a correct answer is marked wrong, or the exercise does not measure what the lesson teaches.
- **medium**: misleading, incomplete or inconsistent material that a learner will notice.
- **low**: polish, wording or minor consistency.

## Findings

IDs: `fleng-…` are draft-curriculum IDs; seed IDs are the slugs in `seed.py`.

### High

**H1. Practice items repeat the worked examples verbatim (draft, all levels)**
- Where: 145 of 250 practice exercises, e.g. `fleng-a0-classroom-practice-1/2/3`, `fleng-a0-hello-practice-1/2`, `fleng-a0-letters-practice-3`; 25 of 50 in A0 and 30 of 50 in every other level.
- Problem: the lesson shows "Look at the text. Read it." under Examples, then asks "Look at the text. ___ it." as practice. The learner can copy the example.
- Why it matters: practice measures recall of a shown sentence, not understanding. Scores overstate learning.
- Fix: keep examples as teaching text and write new practice sentences that use the same pattern with different words. Do not generate hundreds of items; replace only these 145 prompts.

**H2. A second answer is correct (draft)**
- `fleng-b2-synthesis-practice-1`: "The evidence is limited; ___, we recommend a pilot." Options: therefore / nevertheless / despite. "Nevertheless" is also grammatical and arguably more natural for a cautious recommendation.
- `fleng-b1-processes-practice-2`: "The sheets are ___. (dry)" Options: drying / dry / dried. "The sheets are dry" is correct English. Only the passive reading marks "dried" correct.
- Why it matters: a learner who answers correctly is told they are wrong.
- Fix: for synthesis, replace the distractor "nevertheless" with a connector that cannot fit (for example "for example"). For processes, change the prompt to "The sheets are ___ in the sun. (dry, passive)" or remove "dry" from the options.

**H3. Check phase does not test the lesson's grammar (draft, all 50 lessons)**
- All 150 `check` exercises ask only for the Ukrainian meaning of one vocabulary word. The lesson's grammar goal is practised only in 5 items, and the reading passage (on average 21 words in A0, 97 in B2) is never asked about.
- Why it matters: the final check cannot show whether the grammar goal was met, and the "Read in context" section has no purpose in scoring.
- Fix: make at least one check item per lesson grammar-based or based on the reading passage.

### Medium

**M1. Several valid answers because of `would` (draft, validator-flagged)**
- `fleng-a2-conditions-practice-2` ("If it is dry, we ___ have a picnic.") and `fleng-a2-travel-problem-practice-3` ("If you show your passport, I ___ give you the key.") list `would` beside `will`. `would` can be acceptable in both (polite or hypothetical readings).
- Fix: add context that fixes a real, likely condition, or replace `would` with `did`-type distractors that cannot fit.

**M2. Answer position is the same in every lesson (draft)**
- Every lesson uses the order of correct options 1, 3, 2, 1, 3, 3, 2, 1. Across 400 items, option 1 is correct 150 times, option 3 150 times, option 2 100 times. `frontend/js/lesson.js` renders options in stored order; only `vocabulary.js` shuffles.
- Why it matters: the pattern is learnable and a 3-option item already allows one-in-three guessing.
- Fix: vary positions per lesson, or shuffle in the UI (a frontend change, outside this audit's scope).

**M3. All 500 vocabulary example sentences are empty (draft)**
- Every `vocabulary[].example` is `""` while the schema requires the field. The Words and flashcard features have no sentence to show.
- Fix: fill examples, or make the field optional and hide it when empty.

**M4. 83 vocabulary words never appear in their lesson (draft)**
- Examples: `fleng-a0-letters` `alphabet`, `page`; `fleng-a0-hello` `evening`, `friend`, `student`, `thanks`; `fleng-a0-objects` `chair`, `door`, `pencil`, `key`; `fleng-a0-people` `family`, `mother`, `father`, `child`, `parent`.
- Why it matters: learners see a word list with no context and no practice.
- Fix: use each word at least once in the reading, an example or an exercise, or trim the list.

**M5. Prompt does not match the task (draft)**
- `fleng-a0-numbers-practice-1/2/3/5` say "Write 12 in words." but the learner picks one of three options; nothing is written.
- Fix: "Choose the word for 12."

**M6. Wrong or misleading Ukrainian glosses (draft)**
- `fleng-a0-questions`: `late` = "той, хто запізнився" ("the one who is late") is a phrase, not an adjective. Use "пізній / запізнілий" or "спізнившись" with a clear sense.
- `fleng-b1-lasting-change`: `since` = "від" and `for` = "протягом". These are the two words the lesson teaches, and "від" hides the sense "since (a point in time)". Use "з (певного моменту), відколи" and "протягом, упродовж".
- `fleng-b2-modal-past`: `qualification` = "застереження" gives only the rare sense "caveat"; its main sense is "кваліфікація".
- Fix: native-speaker review of every gloss in these lessons.

**M7. Theory does not cover what the practice asks (draft and seed)**
- `fleng-a1-routines`: theory says "use before and after to put actions in order"; no exercise uses them.
- `fleng-a2-travel-problem-practice-5`: tests indirect-question word order ("tell me when breakfast starts"); this is taught only in `fleng-b2-reported-questions`.
- `fleng-b2-wish-practice-4`: needs "wish + were"; the theory teaches only "wish + past simple".
- `fleng-b2-synthesis`: theory says the lesson "integrates conditional, passive and reporting structures"; practice covers passive (2 items), a conditional (1 item) and no reporting.
- Seed `numbers-and-days`: the date section uses ordinals ("the third of May", "the first of June") and a self-check model answer uses "eleventh", but ordinals are never explained.
- Fix: add the missing teaching sentence, or change the item.

**M8. Seed text exercises reject normal learner input (seed, published)**
- Grading (`backend/app/modules/exercises/grading.py`) only trims, collapses spaces and casefolds.
- `the-verb-to-be-q2` accepts `i'm` and `im` but not `I’m` (typographic apostrophe, which phone keyboards insert by default).
- `greetings-and-introductions-q2` accepts two exact strings, so "Nice to meet you too." or "Nice to meet you, too" are marked wrong, and valid replies such as "You too" or "Likewise" are rejected.
- Fix: add the accepted variants, or (a production change, not made here) strip punctuation and normalise apostrophes in `normalize_text`.

**M9. Seed lesson `present-perfect-practice` duplicates `past-experiences` (seed, published)**
- Same theory text (the `_PAST_EXPERIENCES_THEORY` constant is reused), and the same sentence appears three times: `past-experiences-q2`, `present-perfect-practice-q2` and `present-perfect-practice-q3` all test "Have you ever (been) to Ireland?".
- `present-perfect-practice-q1` repeats `past-experiences-q1` with "She" in place of "I".
- Fix: give the practice lesson its own sentences, or merge the two lessons.

**M10. Only one exercise type, with easy-to-eliminate distractors (draft)**
- 400 of 400 draft exercises are 3-option `single_choice`; there is no typing, ordering or letter-tile item, although the seed and docs support them. 23 options are not English forms at all (for example `buyed`, `studys`, `to can`, `could to`, `had buying`).
- Why it matters: B1/B2 lessons use advanced vocabulary but test it with items an A2 learner can pass by elimination, so the labelled CEFR level is not demonstrated.
- Fix: for B1/B2 use plausible distractors (real tenses and modals) and add some typed items.

**M11. Seed level gap and overlapping tracks (seed and draft)**
- Seed course "English Foundations" (A1) has no A2 course before "Everyday Conversations" (B1). The B1 course's "Asking for help" (could/would/mind) and "Past experiences" are normally A2 material, so level labels and difficulty do not match.
- The draft A0 course repeats the seed course's topics (greetings, the verb be, numbers). If both are published, a learner meets the same material twice with different slugs.
- Fix: decide whether the draft curriculum replaces the seed, then relabel or remove the seed courses.

### Low

- **L1. Templated goals.** All 50 draft lessons have `goals[0]` equal to `summary` and `goals[1]` equal to "Practise: <grammar>." Neither is a measurable goal.
- **L2. Prompts that give the answer away.** Prompts that carry a label ("Use going to:", "Strong positive deduction:", "Use will for an offer:") appear in `fleng-a2-plans`, `fleng-b1-future-options`, `fleng-b1-deduction`, `fleng-b2-modal-past`. The labels remove the ambiguity (by design, per the theory text) but also the choice the lesson is meant to teach.
- **L3. Level placement.** A2 includes present perfect, first conditional and defining relative clauses, and B1 `fleng-b1-future-options` repeats `fleng-a2-plans`. Many grammar syllabi place these one level higher or treat them as review. Reviewer judgement; confirm against the target syllabus.
- **L4. A0 metalanguage.** `fleng-a0-letters` teaches `vowel`, `consonant`, `alphabet` at A0.
- **L5. Minor glosses.** `fleng-a0-people` `parent` = "хтось із батьків"; `fleng-a1-food` `potato` = "картоплина"; `fleng-a1-right-now` `rain` = "дощити", `make` = "робити" (the lesson uses "make tea"); `fleng-a2-comparisons` `apartment` = "квартира для проживання" beside A1 `flat` = "квартира"; `fleng-b2-synthesis` `coverage` = "забезпечення присутності персоналу".
- **L6. Homographs across courses.** `book`, `chair`, `result`, `appointment`, `identify`, `limitation` appear in two courses with different glosses. No database conflict (uniqueness is per course), but Words may show two meanings.
- **L7. Thin theory focus.** `fleng-a0-people`: theory says the lesson "practises plural they", but one of five items uses it.
- **L8. Distractors that are obviously wrong.** Examples: `fleng-a1-abilities-practice-2/3` (`Do can`, `isn't can`, `doesn't can`), `fleng-a2-health-practice-1` (`shoulds`).
- **L9. Seed polish.** `greetings-and-introductions-q1` prompt has a stray space before the comma ("'___ , my name is Alex.'"). `numbers-and-days-q3` model answer is a fixed date ("the eleventh of October"). Lesson `numbers-and-days` promises counting to one hundred but exercises use `twelve` and a weekday question.
- **L10. Hint-by-translation.** Some prompts paraphrase the answer ("The cup touches the top of the desk: ___ the desk." in `fleng-a0-where`). Good scaffolding at A0; revisit if it continues at higher levels.

### Checked and found sound

- Every answer key exists in its options; options are unique; positions and slugs are contiguous and unique.
- Every `check` exercise matches its word's translation; its distractors come from the same lesson.
- Every explanation names the correct answer. Every vocabulary translation is Cyrillic and non-empty.
- Prerequisites form one unbroken chain from A0 to B2. Lesson order inside each level is logical.
- No empty lessons: each has theory, reading, three or more examples and ten words.
- Seed letter-tile exercise (`present-perfect-practice-q2`): pattern `b__n` and letters can form `been`.
- No wrong grammar in any theory text was found. The theory is short (about 58 words in A0, 70 in B2) but accurate.

## Automated checks

`backend/tests/test_content_structure.py` adds 1,333 test cases that read the content directly:

- **Passing invariants (1,327):** unique slugs, CEFR course order, contiguous positions, prerequisite chain, complete lesson material, Cyrillic translations, well-formed options and answers, explanations name the answer, check items match vocabulary, no repeated prompts, and seed consistency (unique slugs, exercises reference real lessons, every lesson has exercises, normalised accepted answers, letter tiles can form the answer).
- **Known defects as strict `xfail` (6 at audit time, 4 open now):** empty vocabulary examples (M3), identical answer positions (M2), practice equals examples (H1), unused vocabulary (M4). The typographic-apostrophe (M8) and duplicated-theory (M9) checks were fixed and are now regular tests. When a defect is fixed the test XPASSes and fails, which is the signal to remove its marker.

No production code was changed. The tests import `app.db.seed` and `normalize_text` only to read them.

## Resolution status (branch `fix/published-content`)

Published seed content only; the draft curriculum was not touched.

| ID | Status |
| --- | --- |
| M8 typographic apostrophe, end punctuation, equivalent replies | **Fixed.** `normalize_text` maps typographic apostrophes to `'`, drops optional sentence punctuation, applies NFKC. `greetings-and-introductions-q2` now lists "you too", "likewise", "it's nice to meet you too", "pleased to meet you too", "nice meeting you too". Letters are never altered, so wrong words stay wrong. |
| M9 duplicated theory and exercises | **Fixed.** `present-perfect-practice` has its own theory. `-q1` uses a new sentence and `-q3` now tests "never" in a new sentence. `-q2` (letter tiles, "been") is unchanged because docs and tests use it as the documented letter-tile example. |
| M7 (seed part) ordinals not taught | **Fixed.** `numbers-and-days` theory has an "Ordinal numbers" section. |
| L9 seed polish | **Fixed** (stray space; the fixed "today's date" self-check is now "a date, for example your birthday"). |
| M11 level gap, overlap with the draft A0 course | **Open** (pedagogical decision). |

The two matching `xfail` tests became regular regression tests; 4 strict `xfail` remain (M2, M3, M4, H1).

## Suggested order of work

1. Seed (live): M8, M9, L9, then M11.
2. Draft, before any publication: H2, H1, H3, M1, M6.
3. Then M2 to M5, M7, M10 and the low items.
4. Run `scripts/validate_curriculum.py` and this test file after each batch.

## Draft repair candidate — branch `fix/draft-curriculum`

M3, M2, H1 and M4 are repaired in a **separate**
`backend/app/db/content/curriculum-a0-b2.draft.json` candidate. The primary JSON is
now pinned as an owner-authorized release despite its `draft` status, so it and
the published seed are intentionally unchanged. The four former strict xfails
became ordinary regressions for the corrected draft; the release SHA remains
covered independently. This does **not** mean the published artifact's defects
have been repaired or that the candidate has teacher approval.

The four quantitative fixes are 500 examples, balanced positions across 400
exercises, 145 gap-fill copies plus 5 non-gap copies replaced, and reading context
for all 83 audit omissions (plus 40 further whole-word/distractor-only gaps).
The extended detector checks actual displayed positions and complete words, and
includes new vocabulary examples in its copy check. Other audit findings remain
open. AI-assisted editorial work is not pedagogical verification.

Details, commands, checks and publication limits:
[draft quality fixes](draft-curriculum-fixes.md).
