# Configuration

[Settings](../../backend/app/core/config.py) reads process environment (highest priority), root .env, then backend/.env. Unknown environment keys are ignored. .env.production.example is a reference template and is not loaded automatically.

Defaults: file-backed SQLite at backend/data/fleng.db, port 3001, AI disabled and reset email disabled. Relative SQLite paths resolve against backend/. Preserve existing configuration and keep real credentials out of Git.

[Configuration reference](../12-reference/configuration-reference.md) lists every Settings field/default/bound and script-only variables. Production requires APP_ENV=production, a random JWT secret of at least 32 characters, Secure cookies and exact HTTPS origins. These guards do not establish durable storage or HTTPS termination.

Verified limitation: explicit `sqlite+aiosqlite:///:memory:` is incorrectly normalized to a duplicated driver; `sqlite:///:memory:` works for Settings-based inspection. Production preparation rejects memory databases.

[Section index](README.md) · [Documentation home](../README.md)
