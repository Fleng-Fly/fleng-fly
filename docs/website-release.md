> Current prepared release: 2026.11.17-web.3.1; see [exported Figma alignment](figma-export-web3.md).

> Latest browser release: [reference-board completion](reference-web2.md),
> version 2026.11.16-web.2. The notes below record the previous release.

# Website release — 2026.11.16-web

Fleng is now a browser website. This release merges the actual GitHub
`fleng-update` interface with the latest reference follow-up, on top of main
b1c80e7. It keeps main's A0 filter, theory/practice/vocabulary navigation,
SQLite startup and owner-authorized A0–B2 curriculum.

## Behavior

Purple theme and local Poppins fonts; vocabulary search/add/learned filters;
four API-backed practice modes, animated flashcards and results/mistakes-only
retry; role-area Our Team cards and reduced-motion support. No invented people,
XP, audio lessons or pronunciation scoring were added.

Desktop shell/build code, desktop diagnostics and EXE-based instructions were
removed. START-FLENG aliases now start the browser website through npm run dev.
No bundled Python runtime or EXE is shipped. Old user databases are neither
removed nor automatically migrated from a Windows app data directory; existing
backend compatibility migrations are preserved.

Install links, manifest links, standalone metadata and worker registration are
removed. Old install.html redirects to Dashboard. The empty manifest, retiring
sw.js and pwa.js cleanup exist only to retire previously cached installations.
Only Fleng worker registrations and fleng-offline-v caches are removed; account
cookies, sessions and learner data are not cleared.

FastAPI and Netlify static assets now use Cache-Control: no-cache, preserving
ETag/304 revalidation. Footer/sidebar and /version.json identify this release.
Netlify /api/* proxies to the existing FastAPI host on Render.

## What prevented the live update

Public GitHub inspection found main at b1c80e7 and fleng-update at 2ed3f98:
the interface changes were on the branch, not main. The latest archive additions
had not reached either remote branch. On 2026-11-15 UTC, HTTP checks found:

- https://fleng.netlify.app returned the old theme without Our Team;
  /api/v1/health returned 404 (missing backend proxy).
- https://fleng-fly.onrender.com returned 503 with
  x-render-routing: suspend-by-user. A Git push cannot resume a suspended service.

## Publish the prepared update

The update package contains UPDATE-SITE.cmd, update-website.ps1 and website.patch.
Extract it and run UPDATE-SITE.cmd on the Windows computer that has Git access.
Default checkout: C:\Users\Roman\Fleng-GitHub. A different checkout can be passed
as the first argument. The script checks the origin, refuses tracked local
changes, fetches, switches to main and fast-forwards it, checks the full patch,
creates a local backup branch, commits only the prepared patch and pushes main
without force. Unrelated untracked files and ignored databases/.env are not
staged. Patch conflicts stop before application; push failures leave the local
commit available to retry. If publishing already succeeded, reruns detect the
release instead of applying it again. No credentials are stored in the package.

On Render, resume the existing service and deploy the latest main commit.
On Netlify, deploy main with frontend as base/publish directory (existing config).
Retain backend secrets and persistent database settings; allow the real Netlify
origin in backend CORS_ORIGIN. Do not copy backend/.env or private data into frontend.
After deployment check /version.json == 2026.11.16-web, refresh the page, sign in,
open Courses and My Words, save a review and reload. Check API health through
both hosts. A live update is not complete until the host serves this release.

## Verification

40 frontend scenarios and legacy worker/installation retirement checks passed.
51 targeted backend/static/learning scenarios passed, including ETag/304 cache
revalidation. Ruff and HTML/page asset checks passed. Independent review caught
and corrected archive regressions to the A0 filter and lesson tab navigation.
No remote push, deployment, Windows GUI/script run or host dashboard access is
claimed by preparation of this package. GitHub write authentication and Render
administration remain required for publishing.

## Windows publishing launcher correction — 2026-11-16

The previous CMD launcher requested update-site.ps1 while the shipped script
was update-website.ps1. It also treated only positive process error codes as
failure, so PowerShell startup errors could be followed by a success message.
The launcher now checks both companion files before execution, uses the shipped
filename and treats every nonzero exit code as failure. The PowerShell script
explicitly exits zero only after successful completion. Archive paths and a
clean-base patch application were verified; Windows execution remains untested
in this Linux environment. A missing-script screenshot does not confirm any
GitHub commit, push or live deployment.
