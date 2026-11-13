# Curriculum tests

From root:

```sh
backend/.venv/bin/python scripts/validate_curriculum.py --all
backend/.venv/bin/python scripts/validate_curriculum.py --level A0 --report markdown
cd backend
.venv/bin/python -m app.db.curriculum --validate-only
.venv/bin/pytest -q tests/test_curriculum.py tests/test_curriculum_validation.py tests/test_curriculum_preview.py tests/test_a0_migration.py
```

Coverage includes stable IDs/collisions, dry-run/draft separation, progress preservation, real grader probes, unavailable/corrupt evidence/provenance, safe-fix SHA/overwrite guards and preview auth/isolation. Synthetic evidence/AI cannot prove linguistic correctness.

Exit success can include medium warnings/unavailable sources. --check-sources can deliberately return 1. Stored reports are historical; generate into new output paths.

[Section index](README.md) · [Documentation home](../README.md)
