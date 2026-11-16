# Fleng Curriculum Validator

Implemented 2026-11-11. Offline, read-only audit of the existing version-1 draft
format. It imports no database session, never changes XP/grading, and does not
publish or invoke the curriculum importer. The existing publication SHA process
remains a separate human review/release operation.

## Architecture and scope

`backend/app/services/curriculum_validation/` contains:

- `validator.py`: existing Curriculum/LessonSpec/WordSpec/ExerciseSpec contract,
  raw Unicode/whitespace audit before Pydantic normalization, duplicates,
  prerequisites via the importer, real server grader calls for each answer ID
  and wrong/empty probes, limited grammar/CEFR/modal advisories, review queues.
- `sources.py`: typed local evidence and license/provenance validation; missing
  or corrupt sources are explicitly unavailable. Multiple caches are supported.
- `datasets.py`: local official Wiktextract JSONL and Tatoeba detailed TSV/direct
  link projections. No downloader or Cambridge scraper.
- `ai_review.py`: optional existing OpenRouterProvider transport, structured JSON,
  request/token/time/retry/reservation limits and reported usage. Disabled by default.
- `fixes.py`: SHA-guarded NFC/edge-whitespace proposals applied only to a separate
  new draft file, revalidated with the importer; unified diff saved alongside it.
- `reports.py`: JSON and Markdown views of the same evidence-based audit.

No schema migration, endpoint, frontend, user progress or Roma test logic changes.
No new dependency. Report IDs use existing draft slugs and JSON paths; they are
source identities, not invented production IDs. Each issue includes scope,
category, severity, confidence, source type, evidence, proposed action and review
status. Raw-file SHA and canonical publication SHA are distinct and both reported.

The current draft schema supports only single-choice exercises. All 400 draft
exercises use that type. A future `text` or `self_check` draft is rejected by the
existing import contract and flagged unsupported, rather than silently treated
as validated. The existing text grader folds case and whitespace, but does not
normalize NFC or infer synonyms; self-check is a learner assessment, not an
objective grade. Extending draft formats and context-aware alternative-answer
checks is future work, not a grader/XP change in this implementation.

## Running an audit

Use the existing backend virtualenv; run from the repository root. No network or
DB is required. Only explicit `--output`/fix arguments write files.

```bash
backend/.venv/bin/python scripts/validate_curriculum.py --all
backend/.venv/bin/python scripts/validate_curriculum.py --level A0 --report markdown
backend/.venv/bin/python scripts/validate_curriculum.py --level A1
backend/.venv/bin/python scripts/validate_curriculum.py --all --suggest-fixes
backend/.venv/bin/python scripts/validate_curriculum.py --check-sources
backend/.venv/bin/python scripts/validate_curriculum.py --all \
  --dataset /tmp/fleng-wiktionary.jsonl --dataset /tmp/fleng-tatoeba.jsonl \
  --report json --output /tmp/new-audit.json
```

`--input` selects another draft snapshot in the existing format. Level filtering
selects report contents; the full snapshot is still checked against the importer
contract, including cross-level prerequisites. Output files must be new files;
existing reports/drafts are protected from accidental overwrite. Source check
inspects local availability/schema/license metadata only, not remote reachability.

Exit codes: `0` no high/critical defects, `1` high/critical defects (or unavailable
source in `--check-sources` mode), `2` invalid input/configuration/I/O. Warnings and
unavailable linguistic evidence may coexist with exit 0: this is a structural CI
signal, not permission to publish. JSON exposes all unavailable/not-run statuses.

## Vocabulary and language limits

Every lesson word receives an item result, source provenance, and one of
`probable`, `needs_review`, `invalid`, `source_unavailable`. `verified` is reserved
for future sense-level reviewed evidence and is never emitted automatically.
A dictionary match only attests a headword; an exact translation match still
cannot establish that its sense/POS fits the lesson. Missing translations and
script failures are reproducible defects; source translation mismatches and
multiple senses are review warnings, not automatic replacements. Synonyms are
not rejected as wrong merely because their strings differ.

All lesson worked examples are looked up against Tatoeba. Matched evidence
retains sentence and directly linked translation IDs, licensing and attribution;
the local registry exposes translations without republishing them in reports.
No match is not evidence of bad English. Current 500 word examples are empty by
design; contextual examples are at lesson level. This is reported as a coverage
limit, not patched with fabricated examples.

Grammar pattern checks are deliberately narrow (agreement and a few negation
patterns); quoted incorrect examples can trigger warnings. Every explanation,
example and goal still requires teacher review. Modal alternatives are a
low-confidence triage rule; conditional clauses may legitimately constrain them.
The CEFR advisory uses locally chosen reading-length thresholds and obvious
advanced-topic labels in introductory courses. It does not implement a CEFR
classifier, licensed frequency corpus or exhaustive topic prerequisite taxonomy.
The existing chain is structurally validated, not proof that the pedagogical
sequence is correct. CEFR/Cambridge are reference links; no official descriptors
are copied. A0 uses Fleng's introductory specification in `curriculum-a0-b2.md`.

## Safe proposed corrections

```bash
backend/.venv/bin/python scripts/validate_curriculum.py --all --suggest-fixes
backend/.venv/bin/python scripts/validate_curriculum.py \
  --apply-safe-fixes /tmp/curriculum-reviewed-normalization.json \
  --expected-sha RAW_FILE_SHA256
```

Fix mode recomputes proposals locally, requires the source SHA and draft status,
refuses blocking defects/overwrites/in-place edits, validates the resulting
snapshot with the original import contract, then writes the new snapshot and
`.json.diff`. It preserves schema version 1; snapshot SHA identifies the new
content revision. A changed snapshot needs fresh editorial/publication review.
It never consumes editable AI proposals or changes an answer key, translation
meaning, option ID, publication state or database row. The two output files are
exclusive-created but not a filesystem transaction: an I/O failure can leave a
new snapshot without its diff; the original remains untouched. Do not run
concurrent writers to the same output names.

## Optional paid AI review

No paid calls were made for this task. `not_run` is the default report status.
To opt in, configure the existing backend AI settings and explicitly supply a
budget and an operator-checked maximum price in USD per token, covering both
input and output. Do not use example prices without checking your actual model.

```text
backend/.venv/bin/python scripts/validate_curriculum.py --all --ai-review \
  --ai-budget-usd BUDGET --ai-price-ceiling USD_PER_TOKEN \
  --ai-max-requests 2 --ai-max-tokens 600 --ai-timeout 20 --ai-retries 0
```

Only supplied draft teaching content is sent, not DB rows, environment settings
or credentials. Treat the draft as public content before opting in; this tool
cannot discover secrets embedded by an author in teaching text. Findings remain
`ai_assisted`, low confidence, human review required, and never enter safe fixes.

Limits: budget >0 and <=10 USD, 1–20 total attempts including retries, 100–2000
output tokens, timeout <=60 seconds and at most one retry. Each attempt reserves
UTF-8 input size plus schema/protocol overhead plus output allowance at the
operator's price ceiling, even if it fails. Usage records provider-reported cost
and tokens separately; unknown usage is flagged incomplete. Actual cost above
the reservation stops further calls. Local reservations cannot guarantee external
billing (provider pricing, tokenization, reasoning and failed-request billing can
vary): configure an account-side spending cap too. Transport remains the existing
OpenRouter implementation. No live API behavior is claimed from mocked tests.

## Verification and self-review

See the generated [quality report](curriculum-validation-report.md) and
[JSON artifact](../reports/curriculum-validation/a0-b2.json). Regenerate into a new
output file and compare it to the stored report; the same inputs produce the
same audit, with no live time or network-dependent grading.

Automated checks include inventory/level selection, all accepted and rejected
choice IDs, empty/Unicode-equivalent options, ambiguous modals, repeats,
nonexistent synthetic words, controlled translation mismatch, unavailable/corrupt
sources, per-sentence license preservation, source projections, CLI exit codes,
dry-run preservation, SHA/overwrite protection, structured JSON/Markdown,
AI limits/timeouts/retries/usage and disabled AI.

Independent self-review fixed an ASCII-only false positive for `café`, avoided
flagging explicitly constrained backshift/would questions, separated translation
sense groups, preserved both Tatoeba licenses, checked raw values before importer
normalization, reused per-item import schemas for pass counts, and blocked safe
fixing in the presence of high/critical defects. Remaining linguistic limits are
explicit above; no claim of a completed teacher/translator review is made.

Verification run (2026-11-11):

- Full pytest: **364 passed, 15 skipped**, 12 existing deprecation warnings.
  PostgreSQL tests skip without the dedicated test URL. The full DB suite ran
  outside the restricted sandbox because of the previously documented aiosqlite
  hang; no application/production database was used.
- Final targeted validator regression rerun after AI summary/output-path review:
  **39 passed**. All external evidence and AI responses are synthetic/mocked.
- Standard Ruff (`backend/app backend/tests`) plus both new scripts: passed.
  An additional broad `ruff check .` in backend found six pre-existing I001
  import-order findings in historical migrations; these were left unchanged.
- mypy: passed, **76 source files**.
- Alembic on a temporary SQLite file: one head `20261110_1400`, upgrade head
  passed, check reported no new upgrade operations. PostgreSQL offline migration
  SQL compiled (13,455 bytes). Live PostgreSQL remains unverified.
- `git diff --check`: passed. CLI help, all-course JSON/Markdown generation,
  A0 filtering and unavailable-source exit behavior exercised directly.
- Current raw draft SHA: `4e0af1aa292b24e58515ea4b8656274ff6464d9b865fda29b232ddd416d5cd58`.
  Existing canonical publication SHA remains
  `27ab5cdc8cdadbfc85353cea58fc2584459c130aea460cf391a2e5d67b108013`.
  No deterministic correction was needed (zero proposals); original draft intact.

Current triage: 0 critical/high/low issues, 2 medium advisory conditional items,
107 informational entries (50 grammar-review tasks, 50 competency-coverage tasks,
6 cross-level word revisits, 1 unavailable-source notice). The two prompts are
`fleng-a2-conditions-practice-2` and `fleng-a2-travel-problem-practice-3`.
Their `will`/`would` options need contextual teacher review; these warnings do not
establish that the existing answer keys are wrong. Explicitly constrained
backshift/second-conditional/“Use would have” questions are not flagged by this
narrow modal rule. No grammar error or incorrect Ukrainian meaning was proven;
external verification was unavailable, not passed. All five courses can proceed
to editorial review, none is recommended for publication by this audit.

Files added by this stage: the two service package initializers and six validator
modules listed above; `scripts/validate_curriculum.py`,
`scripts/prepare_curriculum_sources.py`, `backend/tests/test_curriculum_validation.py`,
this document, `docs/curriculum-sources-and-licenses.md`, the generated Markdown
report and `reports/curriculum-validation/a0-b2.json`. Appended status/flow entries
to `project-map/modules.md`, `project-map/data-flow.md`, `plans/roadmap.md` and
`plans/milestones.md`. Existing uncommitted curriculum/backend/frontend work was
preserved. No commit, push, production import, publication or paid request.
