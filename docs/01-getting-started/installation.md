# Installation

From repository root:

```sh
npm run dev
```

The launcher creates a missing backend virtualenv, installs the editable backend with dev extras, prepares SQLite, then starts reload-mode Uvicorn. Open `http://localhost:3001/` and `/docs` for interactive API documentation. No separate frontend process exists.

Explicit equivalent:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e './backend[dev]'
cd backend
.venv/bin/python -m app.db.prepare
.venv/bin/uvicorn app.main:app --reload --no-proxy-headers --host 127.0.0.1 --port 3001
```

Preparation upgrades file-backed SQLite and seeds only an empty catalog. Register at `/register.html` to create an ordinary development account. Do not overwrite an existing .env. [DEMO.md](../../DEMO.md) explains optional fictional demo accounts; keep generated credentials private.

Explicit development catalog maintenance from root:

```sh
npm run db:migrate
npm run db:seed
```

The legacy seed does not import the five draft courses. PostgreSQL requires explicit migrations.

[Section index](README.md) · [Documentation home](../README.md)
