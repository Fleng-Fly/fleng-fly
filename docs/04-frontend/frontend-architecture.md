# Frontend architecture

frontend/js uses browser ES modules loaded by HTML. layout.js/workspace.js share navigation/profile controls; catalog-ui.js shares catalog presentation; errors.js maps user-facing failures. api.js centralizes fetch/helpers and session.js manages restoration/guards. ai-assistant.js and ai-stream.js implement the floating chat and parser.

To add a page, create an HTML file and page module with type=module, reuse existing CSS/layout, place fetch helpers in api.js and use requireSession for private state. Render untrusted content through textContent/created nodes. Show loading, empty and recoverable errors separately. Link .html URLs; do not introduce SPA rewrites or a build system.

FastAPI mounts static files last, preserving API/docs precedence. A pure static server can inspect assets but does not run authenticated application features. [Design docs](../../design/README.md) preserve visual intent.

[Section index](README.md) · [Documentation home](../README.md)
