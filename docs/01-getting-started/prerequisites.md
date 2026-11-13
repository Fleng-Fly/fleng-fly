# Prerequisites

Python **3.11+** is declared by backend/pyproject.toml; Node.js **20+** by package.json. Python needs venv and pip. Node runs orchestration and regression scripts, not the backend. A browser needs ES modules and fetch. Git is required for contribution. SQLite requires no server; Docker/PostgreSQL are optional.

Commands below target Linux/macOS POSIX shells. setup.mjs/dev.mjs select Windows executables, but shell scripts using `.venv/bin/` and `${PORT:-3001}` need adaptation. Windows parity is unverified.

```sh
python3 --version
node --version
npm --version
```

Dependencies live in [pyproject.toml](../../backend/pyproject.toml). No frontend dependency installation/build is needed. Root `npm test`, `npm run lint` and `npm run typecheck` invoke pnpm internally; use explicit backend:* npm commands if pnpm is absent.

[Section index](README.md) · [Documentation home](../README.md)
