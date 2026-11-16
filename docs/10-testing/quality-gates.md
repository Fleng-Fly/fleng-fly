# Quality gates

From root:

```sh
npm run backend:lint
npm run backend:typecheck
npm run backend:test -- -q
node --experimental-vm-modules scripts/test-courses.mjs
node --experimental-vm-modules scripts/test-ai-api.mjs
node --experimental-vm-modules scripts/test-ai-stream.mjs
node --experimental-vm-modules scripts/test-ai-widget.mjs
python3 scripts/check-docs.py
backend/.venv/bin/python scripts/check-docs.py --contracts
git diff --check
```

Ruff checks app/tests with configured E/F/I/UP/B rules; mypy checks app. Historical migrations are outside the standard lint command. Explicit backend npm commands avoid root wrappers' pnpm requirement. No CI enforcement/coverage threshold is implied by local commands.

The documentation checker uses stdlib for links and optional backend environment for contracts. [Validation report](../12-reference/validation-report.md) states scope/limits. Full startup/auth persistence smoke is `python3 scripts/backend-stabilization-smoke.py`; it uses temporary DB/port, not application data.

[Section index](README.md) · [Documentation home](../README.md)

Contract mode compares all API operations/named JSON schemas, model columns and Settings inventory, and validates documented request/response examples with the actual Pydantic classes. It performs no database query/network call. It is a drift guard, not an exhaustive service authorization/error-path test.
