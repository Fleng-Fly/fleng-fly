# Troubleshooting

Windows `Missing script: "setup"`: the current `START-WINDOWS.cmd` uses
absolute paths to `scripts/setup.mjs` and `scripts/dev.mjs` through Node.js,
without resolving npm scripts. Extract the complete archive into one folder;
do not mix manifests and scripts from different releases. Missing companion
files or Node.js below 20 stop the launcher before dependency installation.
Git staging/committing/pushing does not require local setup.

Missing virtualenv/Uvicorn: run `npm run setup` and inspect pip/venv output. Existing installed dependencies are not automatically refreshed after manifest changes. For port conflicts export a different PORT.

401 on private APIs requires a valid Bearer JWT; the refresh cookie alone does not authenticate those endpoints. 403 on auth POSTs can indicate an exact Origin mismatch. 503 requires database connectivity, permission and migration checks. Readiness only probes SELECT 1.

Restricted execution environments can hang aiosqlite tests/migrations. Use a disposable database and the environment approval mechanism for an unrestricted run rather than removing tests or resetting data. Explicit async in-memory Settings URLs have a separate normalization bug; see [limitations](../12-reference/known-limitations.md).

Old guides contain obsolete migration heads, machine-specific paths and `/login` examples. Query `alembic heads` and use `/login.html`. [Deployment troubleshooting](../09-deployment/troubleshooting.md) retains safe 403/503 procedures.

[Section index](README.md) · [Documentation home](../README.md)
