# Browser access; PWA retired

Fleng is website-only as of 2026-11-16. No install links, manifest links,
standalone Apple metadata or service-worker registration remain in the UI.
`install.html` redirects to Dashboard; the empty manifest and retiring `sw.js`
are compatibility endpoints. `js/pwa.js` unregisters only Fleng root workers
and removes only fleng-offline-v caches. Accounts and database are untouched.

See [website release](website-release.md) for update and hosting details.
