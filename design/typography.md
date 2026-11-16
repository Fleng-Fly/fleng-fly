# Typography

> Modern, highly legible sans-serif. Final font files are chosen when the
> frontend is scaffolded; load via `next/font` (self-hosted, no layout shift).

## Typeface direction

- **Primary (UI + text):** a modern geometric/neo-grotesque sans. Suggested:
  `Inter` (UI) or `Geist`. Criteria: excellent legibility at small sizes, wide
  language coverage, good numerals.
- **Optional display:** a slightly more expressive sans for hero headlines only.
  If added, keep it to marketing/hero — not the app UI.
- **Mono:** `JetBrains Mono` / `Geist Mono` for code, IPA and technical content.

Avoid: more than two families; decorative fonts in the app shell.

## Type scale

Based on a 1.25 (major third) ratio, in rem (16px root):

| Token | Size | Line height | Use |
| ----- | ---- | ----------- | --- |
| `display` | 2.5–3rem | 1.1 | Hero/marketing headline |
| `h1` | 2rem | 1.2 | Page title |
| `h2` | 1.5rem | 1.3 | Section title |
| `h3` | 1.25rem | 1.4 | Card/panel title |
| `body-lg` | 1.125rem | 1.6 | Lead paragraphs, lesson text |
| `body` | 1rem | 1.6 | Default text |
| `body-sm` | 0.875rem | 1.5 | Secondary text, metadata |
| `caption` | 0.75rem | 1.4 | Labels, captions |

Weights used: 400 (body), 500 (emphasis/UI), 600 (headings), 700 (display).

## Usage rules

- Line length for reading content: 60–75 characters (constrain with max-width).
- Headings are `text/primary`; body is `text/primary`/`text/secondary`.
- Uppercase only for short labels with letter-spacing; never for sentences.
- Numerals: tabular figures for stats (XP, streaks, timers).
- Language content (English examples, IPA) may use the mono font when it aids
  clarity.

## Accessibility

- Base body size is 16px minimum; never smaller than 12px for captions.
- Users can zoom to 200% without loss of content/function.
- Sufficient contrast per `design/colors.md`.

## Implementation note

Type tokens are defined once (CSS variables / Tailwind `fontSize` extension) and
consumed via utility classes. Components never set raw `font-size`.
