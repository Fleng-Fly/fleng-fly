# Assets

> No binary assets exist yet. This file defines direction and organisation so the
> repo stays clean when assets are added.

## Logo

- Wordmark "Fleng" in the primary typeface, plus a compact mark for app icons.
- Mark concept: an abstract speech/learning glyph with a violet→cyan gradient.
- Provide SVG (light-on-dark) as the canonical asset; monochrome variant for
  favicons.

## Icons

- One line-icon set, 1.5–2px stroke, consistent radius.
- SVG only, currentColor-driven so state/color is controlled by CSS.
- Store under `frontend/public/icons/` (or a component library for inlined
  icons). Prefer an icon component over raw SVG in feature code.

## Illustrations

- Optional, used sparingly for empty states and onboarding.
- Style: minimal geometric, dark-friendly, accent gradient highlights.
- Keep file size small (SVG preferred).

## Imagery

- Photography, if used, must be dark/moody and consistent in treatment.
- Prefer vector over heavy raster for UI; optimise via `next/image` when raster
  is necessary.

## Audio

- Listening content: compressed audio, hosted/served efficiently; transcripts
  stored as text, not baked into media.
- Keep pronunciation clips small and cacheable.

## Organisation (intended)

```
frontend/public/
├── brand/          # logo, wordmark, favicon
├── icons/          # svg icon set
├── illustrations/  # empty states, onboarding
└── audio/          # listening assets (or external storage)
```

## Rules

- Do not commit large binaries; use optimised formats and external storage for
  media when it grows.
- Every asset has a single source; no duplicated copies across packages.
- Name files by purpose, not appearance (`empty-lessons.svg`, not `pic2.svg`).
- Respect licensing for fonts/images/icons; record attribution where required.

## Open items

- Final logo/mark design.
- Icon library selection.
- Audio hosting strategy (repo vs. object storage) when listening content lands.
