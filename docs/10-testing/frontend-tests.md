# Frontend tests

Run from root:

```sh
node --experimental-vm-modules scripts/test-courses.mjs
node --experimental-vm-modules scripts/test-ai-api.mjs
node --experimental-vm-modules scripts/test-ai-stream.mjs
node --experimental-vm-modules scripts/test-ai-widget.mjs
```

Scripts execute real JS under synthetic DOM/fetch and exercise SSE splits/UTF-8. VM-module scripts need the experimental flag. Backend test_frontend.py checks FastAPI static serving/API precedence. No new framework/build/install is required.

DOM checks cannot prove CSS, touch, visual fidelity or accessibility. Supplement [browser checks](browser-tests.md), including mobile chat overlap.

[Section index](README.md) · [Documentation home](../README.md)
