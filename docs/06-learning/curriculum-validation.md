# Curriculum validation

Offline app/services/curriculum_validation reuses importer contracts, checks raw whitespace/Unicode/duplicates/prerequisites and real grader answers, then adds narrow linguistic/CEFR/modal advisories. It never connects to learner storage or publishes.

From root:

```sh
backend/.venv/bin/python scripts/validate_curriculum.py --all
backend/.venv/bin/python scripts/validate_curriculum.py --level A0 --report markdown
backend/.venv/bin/python scripts/validate_curriculum.py --check-sources
backend/.venv/bin/python scripts/validate_curriculum.py --all --suggest-fixes
backend/.venv/bin/python scripts/prepare_curriculum_sources.py --help
```

Exit 0: no high/critical defects, possibly warnings/unavailable evidence. Exit 1: blocking defects or unavailable sources in source-check mode. Exit 2: input/config/I/O failure. Passing structural tests does not prove linguistic correctness.

Optional local Wiktextract JSONL and Tatoeba detailed TSV/direct-link projections carry provenance, license and attribution. Missing evidence is unavailable; dictionary matching is not sense/POS verification. Reports do not automatically emit verified status. No live downloader/scraper is implied. Read [source/licensing details](../curriculum-sources-and-licenses.md) before redistributing caches.

SHA-guarded safe fixes write a separate new normalized draft/diff, never answer/meaning/publication changes. Optional bounded OpenRouter review needs explicit AI enablement, budget and checked price ceiling; findings remain low-confidence ai_assisted and cannot enter safe fixes. [Validator operations](../curriculum-validator.md) preserves detailed flags/bounds and evidence limits.

[Section index](README.md) · [Documentation home](../README.md)
