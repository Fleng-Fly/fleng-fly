# Development workflow

Read [AGENTS.md](../../AGENTS.md), README and relevant docs/project-map/plans. Project loop: analyze → plan → implement → test → independent review → fix → docs/map/plan update → commit. Explicit task instructions override normal automatic commits; this documentation task requests none.

Inspect status/history first and preserve unrelated work. Use routers/schemas as API authority, models/migrations for storage, Settings for configuration and actual HTML/JS for UI. Stay within existing stack.

Review completed work independently for ownership, transactions, races, failure paths, duplication, unnecessary complexity, stale docs and testability. Run focused checks before broader gates and disclose failures rather than hiding them.

[Section index](README.md) · [Documentation home](../README.md)
