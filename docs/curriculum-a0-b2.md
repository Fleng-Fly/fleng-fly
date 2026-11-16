# Fleng curriculum A0–B2

Status: **DRAFT — human pedagogical and Ukrainian translation review required**.
This is a starting product curriculum, not a complete CEFR examination syllabus.
A0 is Fleng's internal introductory label. Official materials use Pre-A1;
Fleng does not claim equivalence or certification. Reference:
[Council of Europe descriptor scales](https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-descriptors).
All lesson content here was authored in this coding session, with no OpenRouter
calls, production keys or purchased generation. English is the teaching language;
vocabulary translations are Ukrainian (`uk`).

## Audit and preservation

Tracked legacy catalog: `english-foundations` (A1), containing
`greetings-and-introductions`, `the-verb-to-be`, `numbers-and-days`;
`everyday-conversations` (B1), containing `small-talk`, `asking-for-help`,
`past-experiences`. Each has three lessons and nine exercises: 6 lessons,
18 exercises total. Each lesson has one single-choice, one short-answer and one
self-check exercise. Legacy seed contains no CourseVocabularyItem entries.
No local `backend/data/fleng.db` was present during the audit; these are source
facts, not a claim about a production catalog. No production DB was inspected.

All legacy slugs/UUIDs/content/publication state, submissions, personal vocabulary,
XP and progress are preserved. New sources use separate `fleng-a0` … `fleng-b2`
slugs. Legacy greetings/be/experiences overlap foundational skills in the new
sequence and remain supplemental existing material, not extra core sequence
lessons; their level and role are not silently changed. There are no exact title
or slug duplicates in the new 50-lesson sequence. Semantic overlap in spiral
practice still requires human review. No existing content is deleted or moved.

## Level implementation

`app/core/levels.py` defines LearningLevel: A0, A1, A2, B1, B2, C1, C2.
Catalog response/request filters, profile updates, vocabulary filters and AI
exercise request validation reuse it. Existing default profile A1 is unchanged.
AI tutoring instructions explain introductory A0; no AI transport or quota changes.
`GET /api/v1/courses?level=A0` filters published courses; omitted filter preserves
the existing response. Lessons inherit their course level; vocabulary inherits
its course level without duplicated columns. Invalid levels return 422.

Migration `20261110_1400` extends `courses_level_check`. On SQLite its batch
rebuild temporarily disables FK cascades outside a transaction, restores the
previous setting and checks foreign keys. This prevents dropping lessons and
progress as an accidental consequence of replacing the parent table. PostgreSQL
uses ALTER CHECK. Downgrade refuses while A0 courses exist rather than mapping or
deleting them. Historical migrations remain untouched. Run migrations as a
single maintenance operation; SQLite table replacement requires a backup and
exclusive migration ownership, not simultaneous migration workers.

The existing catalog filter gains an A0 button using the same markup/CSS;
there is no redesign. The standard lesson player already supports the generated
single-choice exercises and `##`/paragraph/list theory format.

## Content composition

Source of truth: `backend/app/db/content/curriculum-a0-b2.json`, included as
Python package data. Five courses, ten lessons each. Every lesson contains:

- Title, summary, two learning goals, grammar focus and estimated minutes.
- Prerequisite: the immediately preceding lesson, including the level boundary.
- An original explanation, three worked examples and a contextual dialogue/text.
- Ten thematic vocabulary entries with Ukrainian translations.
- Five grammar/usage practice choices and three vocabulary check choices.
- Three meaningful options per question and one server-side correct option ID.

Totals: **50 lessons, 500 lesson word entries, 500 course dictionary rows,
400 exercises (250 practice + 150 checks)**. All have one point, using existing
grading and once-only XP rules. No separate test engine is added. The phase is
source editorial metadata; stable exercise slugs contain `practice` or `check`.
The existing frontend shows the same exercise list in Practice and Test, so these
are not separate locked exams. Answer keys and explanations use existing private
Exercise columns and are absent from public exercise payloads before submission.
Vocabulary translations and teaching examples are intentionally visible study aids.

Course vocabulary is linked to Course, not a second lesson dictionary. The JSON
retains lesson membership. Rows are deduplicated by course + NFC/casefolded word;
conflicting translations within a course are rejected. A word can legitimately
appear at different levels. Word UUIDs are deterministic and snapshots use those
real IDs. Optional per-word examples may be empty: contextual examples are
provided at lesson level rather than fabricated for every dictionary entry.
Personal vocabulary is never populated from course content automatically.

The new main courses in prerequisite order are:

### A0 — Absolute Beginner (`fleng-a0`)

| # | Lesson | Grammar | Communicative goal | Minutes |
| --- | --- | --- | --- | --- |
| 1 | Words on the screen | Imperatives and classroom instructions | Follow five short classroom instructions. | 15 |
| 2 | Letters and spelling | Letter names and spelling chunks | Recognise vowels and spell a short name. | 15 |
| 3 | A first meeting | I am and you are as introduction chunks | Give a name and greet a new classmate. | 15 |
| 4 | Numbers zero to twenty | Number words and singular age chunks | Read small numbers and give an age. | 15 |
| 5 | One thing, two things | A/an and regular plural -s | Name common objects and count them. | 15 |
| 6 | People around me | He/she/it/we/they with be | Match people and things to simple pronouns. | 15 |
| 7 | Colours and simple descriptions | Adjective position and be + adjective | Describe familiar objects with one adjective. | 15 |
| 8 | Where is it? | In/on/under and where + be | Locate an object in a room. | 15 |
| 9 | Yes, no and simple questions | Be questions and negatives | Ask and answer a short question with be. | 15 |
| 10 | My first day: a short exchange | Integrated be, articles and location | Understand and complete a short first-day conversation. | 15 |

### A1 — Beginner (`fleng-a1`)

| # | Lesson | Grammar | Communicative goal | Minutes |
| --- | --- | --- | --- | --- |
| 1 | My home and possessions | Have/has and possessive adjectives | Describe possessions and who they belong to. | 20 |
| 2 | A typical weekday | Present simple affirmative and third-person -s | Describe a daily routine in order. | 20 |
| 3 | Asking about habits | Present simple do/does questions and negatives | Ask about another person’s habits. | 20 |
| 4 | Time and schedules | At/on/in for time and clock expressions | Read a simple timetable and state meeting times. | 20 |
| 5 | Places in my town | There is/are and some/any | Describe local places and ask what is nearby. | 20 |
| 6 | Food and simple quantities | Countable/uncountable nouns and much/many | Ask for food using appropriate quantity words. | 20 |
| 7 | What can you do? | Can/cannot for ability | Describe abilities and ask about a partner’s skills. | 20 |
| 8 | What is happening now? | Present continuous affirmative and negative | Describe actions happening at the moment. | 20 |
| 9 | Free time and preferences | Like/love/enjoy + -ing and simple contrast | Explain simple leisure preferences. | 20 |
| 10 | Where were you yesterday? | Past simple of be | Describe a past location and state. | 20 |

### A2 — Elementary (`fleng-a2`)

| # | Lesson | Grammar | Communicative goal | Minutes |
| --- | --- | --- | --- | --- |
| 1 | A weekend story | Past simple regular and irregular verbs | Tell a sequence of finished past actions. | 25 |
| 2 | Choosing a place to stay | Comparatives and superlatives | Compare accommodation using clear criteria. | 25 |
| 3 | Plans and arrangements | Going to and present continuous for arrangements | Distinguish an intention from a fixed arrangement. | 25 |
| 4 | Experiences and recent results | Present perfect with ever/never/already/yet | Ask about experiences without giving a finished past time. | 25 |
| 5 | Health and practical advice | Should, must and have to | Give advice and distinguish it from an obligation. | 25 |
| 6 | Getting around a new city | Directional imperatives and movement prepositions | Follow and give a short route. | 25 |
| 7 | When the phone rang | Past continuous and past simple | Describe an ongoing background action and an interruption. | 25 |
| 8 | If the weather changes | First conditional and future time clauses | Explain a realistic future condition and result. | 25 |
| 9 | Which person do you mean? | Defining relative clauses with who/which/where | Identify people, things and places precisely. | 25 |
| 10 | Solving a travel problem | Integrated past, requests and future conditions | Explain a travel problem and agree on a solution. | 25 |

### B1 — Intermediate (`fleng-b1`)

| # | Lesson | Grammar | Communicative goal | Minutes |
| --- | --- | --- | --- | --- |
| 1 | Changes that still matter | Present perfect with since/for versus past simple | Explain a continuing situation and its starting point. | 30 |
| 2 | Projects in progress | Present perfect continuous | Describe recent effort and activity continuing up to now. | 30 |
| 3 | Before the journey began | Past perfect and narrative order | Make the order of two past events clear. | 30 |
| 4 | Predictions and decisions | Will, going to and future arrangements | Explain a prediction and make a spontaneous decision. | 30 |
| 5 | Imagining a different choice | Second conditional | Discuss an imagined present or future situation. | 30 |
| 6 | How everyday products are made | Present and past simple passive | Describe a process when the action matters more than the actor. | 30 |
| 7 | Reporting a conversation | Reported statements with tense backshift | Report a past statement without changing its meaning. | 30 |
| 8 | Deciding what to do | Common gerund and infinitive patterns | Use common verb patterns to discuss decisions. | 30 |
| 9 | How sure are you? | Must/might/cannot for present deduction | Distinguish certainty from possibility using evidence. | 30 |
| 10 | A reasoned recommendation | Because/although/however and paragraph structure | Give an opinion supported by a reason and a limitation. | 30 |

### B2 — Upper Intermediate (`fleng-b2`)

| # | Lesson | Grammar | Communicative goal | Minutes |
| --- | --- | --- | --- | --- |
| 1 | Deadlines and future milestones | Future continuous and future perfect | Distinguish a future activity from a result completed by a deadline. | 35 |
| 2 | Evaluating past alternatives | Third conditional | Explain an unreal past condition and its hypothetical result. | 35 |
| 3 | Wishes and present consequences | Wish/if only and mixed conditionals | Link a past decision to a present consequence. | 35 |
| 4 | Reporting questions and requests | Indirect questions and reporting verb patterns | Report a question or request using accurate word order. | 35 |
| 5 | Assessing what may have happened | Modal perfect deductions | Express degrees of confidence about a past event. | 35 |
| 6 | Adding detail without losing clarity | Non-defining relative clauses and reduced relatives | Add supplementary information with clear reference. | 35 |
| 7 | Making a cautious academic claim | Hedging and reporting evidence | Distinguish a finding from an interpretation. | 35 |
| 8 | Responding to a counterargument | Concession with although/despite/whereas | Acknowledge an objection and defend a qualified position. | 35 |
| 9 | A professional request and complaint | Formal register and indirect requests | Write a precise request with an appropriate tone. | 35 |
| 10 | A balanced proposal for action | Synthesis, cohesion and qualified recommendations | Summarise competing evidence and propose a proportionate next step. | 35 |

## Read-only validation and import

From `backend/` after installing existing project dependencies:

```bash
.venv/bin/python -m app.db.curriculum --validate-only
.venv/bin/python -m app.db.curriculum
```

The first validates without a DB connection and prints the content SHA. The
second is a database dry-run: preflights identity/content conflicts, reports
new/existing row counts, and performs no writes or publication. Use an explicit
DATABASE_URL for any review database. No startup/demo seed calls this importer.
The legacy `python -m app.db.seed` retains its existing behavior and adds level
validation before writing. It does not import the new curriculum.

To inspect unpublished rows in an isolated review database:

```bash
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-review.db .venv/bin/alembic upgrade head
DATABASE_URL=sqlite+aiosqlite:////tmp/fleng-review.db .venv/bin/python -m app.db.curriculum --apply-draft
```

Dry-run first. Human review should use the JSON/theory, answer keys and this plan.
After review, an operator may explicitly publish the exact reviewed content in
a non-production review database using `--publish-reviewed-sha <printed-sha>`.
The SHA is an operator acknowledgement, not cryptographic proof of pedagogical
approval. Any content edit changes it. Neither this task nor automatic startup
publishes the draft. Production writes are rejected by the CLI; production
promotion requires a separately agreed release procedure and backup.

UUIDv5 identities derive from source version, kind and stable slug (or course +
normalized word). A rerun adds nothing and preserves publication state. Existing
rows are not rewritten: differing content, a foreign slug owner or a conflicting
word aborts preflight before any write. Runtime failures must be rolled back by
the caller; CLI sessions do that on exit. Imports are a single-writer maintenance
operation. Content updates after import need an explicit reviewed revision process,
not overwriting an exercise already associated with submissions. No reset/drop_all,
user-table writes or deletions are used. A separate database cannot be treated
as a production backup.

## Quality gates and integration

Pydantic validates schema and level order, slug ownership/uniqueness, titles,
nonempty theory/goals/translations/options, exercise counts and order, exact
answer references, duplicate options, NFC/casefold word duplicates and the
acyclic prerequisite chain. It rejects conflicting course translations.
Importer tests preserve legacy lesson payloads and aggregate progress/XP across
dry-run, two draft imports, review publication and another import. Collision and
source-drift tests prove refusal to overwrite content. SQLite migration tests
retain lessons, submissions, progress and both vocabularies with FK cascades on.

Each published course supports level/course word selection, 10-card sessions,
small/empty sets, owner completion and the existing `sessionId`/`words_for_test`
handoff. Draft course words remain hidden. Viewing/completing cards has no XP.
The existing grading path still awards each exercise once; no Roma test logic
has been added. Prerequisites are pedagogical metadata, not new access controls.

## Human review before publication

See [quality report](curriculum-content-quality.md). Structural validation cannot
certify grammar accuracy, translation nuance, authentic B2 proficiency, cultural
suitability or uniqueness of a plausible answer in every interpretation. All
50 lessons remain draft. Check instruction clarity, answer ambiguity, lexical
load and progression, and review the B2 arguments and professional register.
A0 explanations may need Ukrainian scaffolding or recorded audio. The course
has no audio, pronunciation assessment, open-ended writing rubric or speaking
assessment, and cannot establish CEFR proficiency. MC checks test recognition,
not independent production. Optional word examples are not generated artificially.
Some readings expose additional vocabulary for inference; audit their difficulty.
The system does not enforce prerequisite locks or separate practice/exam grades.
Live PostgreSQL remains NOT VERIFIED unless a real test URL is supplied.
