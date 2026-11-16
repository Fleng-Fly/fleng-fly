# Environments

Development uses reload-mode FastAPI serving frontend/API with persistent local SQLite. Preview uses separate private temporary SQLite, random signing key/cookie and designated reviewer. Production uses run.py, no reload, one worker and production settings guards.

.env.production.example and historical reports name https://fleng.netlify.app and https://fleng-fly.onrender.com. They are repository-recorded targets, not freshly verified live endpoints. No dashboard/live database was inspected here. netlify.toml publishes static files but its API proxy is commented out. No render.yaml exists; Procfile/run.py define startup.

Do not infer current deployed revision, auth success, storage durability or paid-provider connectivity from those names. [Checklist](production-checklist.md) defines release evidence.

[Section index](README.md) · [Documentation home](../README.md)
