# Browser tests

Optional scripts/review_curriculum_browser.py uses Firefox WebDriver BiDi, not a required Playwright suite. It needs already-running headless Firefox with a temporary profile and websockets Python module. Inspect --help for actual arguments. It accepts loopback preview origins and reads private reviewer credentials from a marker, which must never enter reports.

Prepare/start [preview](../06-learning/curriculum-preview.md), use a fresh output directory and review five drafts/theory/choices at mobile/desktop. The runner refuses overwriting a completed report. Historical screenshots/HTTP checks remain in [visual review](../curriculum-visual-review.md).

A current CLI help check does not count as a real browser run. Manual checks should also cover auth reload/logout, drawers, keyboard/focus, loading/empty/error/retry and AI cancellation. No comprehensive accessibility/visual parity gate is established.

[Section index](README.md) · [Documentation home](../README.md)
