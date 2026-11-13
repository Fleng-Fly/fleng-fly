# Render

Repository-compatible settings: Python runtime, repository root, build `python -m pip install ./backend`, start `cd backend && python run.py`, readiness /api/v1/health/ready. Retain frontend/backend/migrations. Host supplies PORT; set production secrets/settings privately.

run.py prepares file-backed SQLite before binding one worker. PostgreSQL needs explicit Alembic release migrations from backend/. Direct Uvicorn bypasses preparation. Configure exact CORS_ORIGIN; validated platform RENDER_EXTERNAL_URL joins it. TRUSTED_PROXY_IPS must reflect actual ingress knowledge, not wildcard guesses.

Ephemeral SQLite is a demo choice and can lose all accounts/progress on storage replacement. Same-file process restart proves no host durability. Durable SQLite requires an explicit persistent volume/single instance; external PostgreSQL still requires backup/restore/TLS validation.

No deployment/host configuration changed here. [Troubleshooting](troubleshooting.md) links historical diagnoses without asserting today's cause.

[Section index](README.md) · [Documentation home](../README.md)
