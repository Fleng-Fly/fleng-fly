# Curriculum expansion plan (A0–B2)

Status: **A0 +5 lessons authored (draft, unpublished); A1–B2 planned.** Goal: grow each
course from 10 toward 15–20 lessons without padding. Every lesson must teach something new
that the previous lessons prepared. Nothing here is published until an owner release decision
(see section 3, "Release gate").

## 1. What the current 50 lessons are (audit, 2026-11-20)

| Aspect | Finding |
| --- | --- |
| Shape | 5 courses × 10 lessons; one new grammar point per lesson; chain of prerequisites; 10 words, 8 single-choice questions (5 practice + 3 check) and 4 typed practice items per lesson. |
| Strengths | Consistent CEFR-ordered grammar (be → present simple → past → perfect → conditionals → reporting/hedging); Ukrainian translations; guided hints/explanations for A0–A1; deterministic grading. |
| Weaker spots | Every word example sentence is empty (500/500); ~80 % of choice questions are one-gap fill-ins built from the lesson examples and 30 are "choose the Ukrainian meaning"; explanations repeat the answer ("Correct choice: works. …"); readings are 14–113 words (median 40); no listening, no free speaking/writing beyond one self-check per lesson; no human linguistic review. |
| Structural limits | `curriculum-a0-b2.json` is a pinned release (owner-authorized SHA, immutable rows, exactly 10 lessons per course in the validator and in many tests). Existing lessons cannot be moved or edited without breaking learners' progress. |

## 2. How new lessons are added (implemented)

* New lessons live in **extension files** `backend/app/db/content/curriculum-extension-<level>.json`;
  the pinned release is never edited. `app/db/extension.py` validates, imports and (only on request)
  publishes them. Same row identities scheme, same immutability rule, additive only.
* New lessons are **appended** (positions 11…); lesson 11 requires lesson 10, and so on. Lesson
  10 of each course was written as an integrated review, so lesson 15 of the extension acts as the
  course's new integrated closing lesson.
* Quality gates stricter than the base release, enforced by the validator: every word has an
  example sentence; ≥ 8 words new to the course; readings are real paragraphs (55+ words);
  explanations explain (not "Correct choice: x"); the correct option is not always the same
  position; the four typed formats (gap, word order, translate, write); unique titles and slugs.
* Ukrainian translation for all words and typed prompts; the lesson page already shows the rule
  step by step from the theory text, with no extra work per lesson.
* Tests: structural/quality rejection tests, additive and idempotent import, SHA gate, refusal to
  rewrite changed rows, and an integration test that completes every new lesson through the API
  with the intended answers.

## 3. Release gate

`prepare.py` imports an extension only when its exact SHA is in
`OWNER_AUTHORIZED_EXTENSION_SHAS` (empty today). Without it the content stays out of the
catalog. To preview locally: `python -m app.db.extension --publish-sha <sha>` (refuses production).
Check a file with `npm run curriculum:extension:validate` (prints its SHA).

## 4. Structure per level

Order inside a course follows dependency: each lesson uses only grammar and vocabulary taught
before it. "New" = not taught in lessons 1–10 of the same course.

### A0 — done (positions 11–15)

| # | Lesson | Grammar / function | Why now |
| --- | --- | --- | --- |
| 11 | Where are you from? | Where + be + from; country and nationality words | Personal information after introductions (L3, L6). |
| 12 | This, that, these, those | Demonstratives, regular/-es plurals | Uses plural nouns (L5) and be (L6). |
| 13 | Days and months | on + day, in + month; What day is it? | Needed for dates; prepares A1 time lesson. |
| 14 | Numbers and prices | Numbers 30–100; How much is/are…? | Extends L4 numbers; first real transaction language. |
| 15 | At the café | Can I have …, please?; polite exchange | Integrates 11–14 in one realistic situation. |

### A1 — planned (positions 11–15)

| # | Lesson | Grammar / function |
| --- | --- | --- |
| 11 | How often? | Adverbs of frequency (always, usually, sometimes, never) with present simple |
| 12 | Me, you, him, her | Object pronouns after verbs and prepositions |
| 13 | Asking for information | Question words: who, what, where, when, why, how |
| 14 | Weather, seasons and clothes | Present continuous vs present simple for now/usually |
| 15 | An email to a new friend | Integrated writing: routines, likes, abilities (closing lesson) |

### A2 — planned

| # | Lesson | Grammar / function |
| --- | --- | --- |
| 11 | Too much, enough, a few | Quantifiers: too/enough, a lot of, a few/a little |
| 12 | When I was young | Used to for past habits |
| 13 | Offers and invitations | Would you like…?, Shall we…?, Let's |
| 14 | How well do you do it? | Adverbs of manner; comparative adverbs |
| 15 | A review of a place | Integrated reading and writing: comparing and recommending (closing lesson) |

### B1 — planned

| # | Lesson | Grammar / function |
| --- | --- | --- |
| 11 | Rules and permission | Have to / don't have to / must / mustn't / allowed to, past forms |
| 12 | So and such, too and enough | Result and degree structures |
| 13 | Phrasal verbs at work and travel | Common separable/inseparable phrasal verbs in context |
| 14 | Unless, as long as, in case | Conditional linkers beyond first/second conditional |
| 15 | A formal email | Integrated writing: register, linkers, polite requests (closing lesson) |

### B2 — planned

| # | Lesson | Grammar / function |
| --- | --- | --- |
| 11 | Things done for us | Causative have/get something done; modal passives |
| 12 | Emphasis and focus | Cleft sentences, inversion after negative adverbials |
| 13 | Compressed clauses | Participle clauses; advanced gerund/infinitive contrasts |
| 14 | Words that go together | Collocations and idioms in professional and academic contexts |
| 15 | Arguing in writing | Essay structure, cohesion, summarising a text (closing lesson) |

A later pass may take each course to 18–20 lessons (e.g. listening-style dialogues once audio exists,
more reading-based lessons, spaced review lessons) after the first five per level are reviewed.

## 5. Process per level

1. Draft the five lessons in an extension file (validator must pass).
2. Complete-through-API test and browser pass (EN and UK UI).
3. Human review by a teacher/translator **before any release decision**; no CEFR sign-off exists yet.
4. Owner adds the SHA to `OWNER_AUTHORIZED_EXTENSION_SHAS` to publish.

## 6. Known limits and risks

* Only `single_choice`, typed gap/order/translate and self-check exercises exist; no audio, no
  speaking exercises.
* New lessons are appended after the old capstone (lesson 10); a learner sees the sequence
  10 → 11 as "unit 2". The old lesson positions cannot change.
* Guidance (hints, per-option notes) exists only for A0–A1 base lessons; new lessons show the
  rule steps and examples but no option notes yet.
* Some words repeat across levels (e.g. café, tea, milk in A1); each level introduces them in a
  different context.
* The dashboard and course pages count only published lessons, so published and draft lessons
  never mix in progress totals.
