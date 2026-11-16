# Pull requests

Recommended PRs lead with the concrete problem/result, explain material choices and report passed/failed/skipped/not-run checks. No formal repository template/organization approval policy is invented here.

Database changes need preservation/upgrade/downgrade and offline/live PostgreSQL evidence. API changes update contracts/maps; modules update project-map/plans. UI changes separate browser/viewport evidence from DOM tests.

Keep scope reviewable, disclose release steps/limits and avoid unrelated formatting. Never publish private logs, account data, reviewer credentials or credential-bearing URLs in PRs.

[Section index](README.md) · [Documentation home](../README.md)

## Infrastructure release gate

Require the exact `Required database checks` aggregate; inspect all SQLite, PostgreSQL and workflow jobs. PostgreSQL reports must include transfer/restore/migration/preservation cases with no skips. A locally passing suite does not replace a hosted run. Review the [prepared main ruleset](../../.github/main-ruleset.json) and [owner setup steps](../09-deployment/final-infrastructure-integration.md); main was publicly reported unprotected on 2026-11-14. This task explicitly leaves commits/pushes to the owner. Production migrations, cutover, restores and draft publication require separate explicit authorization.
