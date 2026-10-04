# Colors

> Values are indicative starting points for the dark theme. Validate final
> values for WCAG AA contrast when the frontend is implemented; adjust as needed
> and update this file.

## Palette

### Neutrals (dark base)

| Name | Hex | Use |
| ---- | --- | --- |
| `ink-950` | `#0A0A12` | App background (deepest) |
| `ink-900` | `#0F0F1A` | Base background |
| `ink-850` | `#14141F` | Surface |
| `ink-800` | `#1A1A28` | Raised surface |
| `ink-700` | `#24243A` | Subtle borders / hover |
| `ink-600` | `#32324D` | Strong borders |
| `slate-400` | `#9A9AB8` | Secondary text |
| `slate-300` | `#C3C3DA` | Body text |
| `slate-100` | `#F1F1F7` | Primary text |

### Primary — purple / violet

| Name | Hex | Use |
| ---- | --- | --- |
| `violet-400` | `#A78BFA` | Hover / light accent |
| `violet-500` | `#8B5CF6` | Primary accent |
| `violet-600` | `#7C3AED` | Pressed / strong |
| `violet-700` | `#6D28D9` | Deep accent |

### Secondary — blue / cyan

| Name | Hex | Use |
| ---- | --- | --- |
| `blue-400` | `#60A5FA` | Info accent |
| `cyan-400` | `#22D3EE` | Highlights / gradient end |
| `cyan-500` | `#06B6D4` | Strong highlight |

### Semantic

| Name | Hex | Use |
| ---- | --- | --- |
| `success` | `#34D399` | Correct, completed |
| `warning` | `#FBBF24` | Streak at risk, caution |
| `danger` | `#F87171` | Errors, destructive actions |
| `info` | `#60A5FA` | Informational |

## Gradients

| Token | Definition | Use |
| ----- | ---------- | --- |
| `bg-glow` | radial violet/cyan at ~8–12% opacity over `ink-950` | page background |
| `accent-gradient` | `135deg, #8B5CF6 → #22D3EE` | XP bars, level badges, progress |
| `success-gradient` | `135deg, #34D399 → #22D3EE` | completed states (optional) |

## Semantic mapping (dark theme)

```
background        → ink-950 / ink-900
surface           → ink-850
surface-raised    → ink-800 (+ glass: rgba(255,255,255,0.04) + blur)
text-primary      → slate-100
text-secondary    → slate-400
text-muted        → slate-400 at reduced emphasis
border-subtle     → ink-700
border-strong     → ink-600
accent-primary    → violet-500
accent-hover      → violet-400
accent-pressed    → violet-600
focus-ring        → violet-400 (2px)
```

## Contrast guidance

- Body text (`slate-300`/`slate-100`) on `ink-900+` meets AA.
- Violet text on dark is fine for large text/accents; for small text prefer
  `violet-400`.
- Do not place `slate-400` on `ink-700` for essential small text.
- Verify each final pairing; when in doubt, check contrast, don't guess.

## Usage rules

- Purple = primary actions and focus; cyan/blue = secondary emphasis, never
  competing with primary actions.
- Semantic colors carry meaning only (success/danger/warning/info).
- No pure black (`#000`) or pure white backgrounds.
