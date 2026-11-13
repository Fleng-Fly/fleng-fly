# Development

`npm run dev` runs setup only if Uvicorn is absent, then app.db.prepare and Uvicorn with reload/proxy headers disabled. Node reads PORT from process environment rather than a .env file:

```sh
PORT=3010 npm run dev
```

Open `http://localhost:3010/`; the frontend uses relative `/api/v1`. `npm run backend:dev` starts Uvicorn directly and bypasses preparation; migrate first. Production uses run.py without reload.

```sh
npm run backend:lint
npm run backend:typecheck
npm run backend:test -- -q
node --experimental-vm-modules scripts/test-courses.mjs
```

Use [isolated preview](../06-learning/curriculum-preview.md) for drafts. Follow [frontend architecture](../04-frontend/frontend-architecture.md) when adding a page. Never reset databases as a setup fix.

[Section index](README.md) · [Documentation home](../README.md)
