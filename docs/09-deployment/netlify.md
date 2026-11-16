# Netlify

[netlify.toml](../../netlify.toml) sets base=frontend and publish=.; publication resolves exactly to frontend/. No build command/bundler is needed. Publish only that tree, including an inspection of ignored files/symlinks. gitignore is not a security boundary.

The /api/* proxy example is disabled. Relative /api/v1 calls cannot work from static hosting alone. Configure a real HTTPS backend proxy preserving /api/, then verify refresh cookies, Origin validation and SSE. CORS does not redirect requests. Avoid SPA fallback: pages are separate documents.

Asset-only local inspection:

```sh
python3 -m http.server 8080 --bind 127.0.0.1 --directory frontend
```

This does not emulate Netlify redirects/live behavior. Unknown/private/unproxied API paths should be actual 404s. [Historical deployment guide](../deployment.md) retains publish checks and root lockfile mismatch evidence.

[Section index](README.md) · [Documentation home](../README.md)
