# Design System

## Principles

- **Token-first.** Every visual value comes from a token; no ad-hoc hex values,
  spacing or radii in feature code.
- **Content over chrome.** Surfaces recede; text and actions stand out.
- **Consistent rhythm.** Spacing, radii and type follow fixed scales.
- **Motion with intent.** Animate to explain state change, never for spectacle.

## Color tokens

Semantic tokens map to the palette in `design/colors.md`. Components reference
semantic names, not raw palette values.

| Token | Purpose |
| ----- | ------- |
| `bg/base` | App background (deepest) |
| `bg/surface` | Cards, panels |
| `bg/surface-raised` | Elevated/glass surfaces |
| `border/subtle`, `border/strong` | Dividers and outlines |
| `text/primary`, `text/secondary`, `text/muted` | Text hierarchy |
| `accent/primary` | Purple/violet — primary actions, focus |
| `accent/secondary` | Blue/cyan — highlights, info |
| `state/success`, `state/warning`, `state/danger`, `state/info` | Feedback |
| `xp/gradient` | Gamification gradient (violet → cyan) |

## Spacing scale

4px base: `4, 8, 12, 16, 24, 32, 48, 64`. Layout uses these steps only.
Page gutters: 16px mobile, 24–32px desktop.

## Radius

`sm: 8px`, `md: 12px`, `lg: 16px`, `xl: 24px`, `full: 9999px`. Cards use `lg`;
inputs/buttons use `md`; pills use `full`.

## Elevation & glassmorphism

- Base surfaces use subtle borders + soft shadows, not heavy drop shadows.
- Glass panels: semi-transparent background + `backdrop-blur` + 1px subtle
  border. Use sparingly (topbar, modals, hero) — not on every card.
- Never rely on blur for contrast; text still meets AA on the composited result.

## Gradients

- Background: very subtle radial/linear violet→cyan glow at low opacity.
- Accent gradient for XP/level/progress: violet → blue/cyan.
- Keep gradients quiet; avoid rainbow effects.

## Motion

| Token | Duration | Use |
| ----- | -------- | --- |
| `motion/fast` | 120–150ms | hover, press, small toggles |
| `motion/base` | 200–250ms | panels, list items, page transitions |
| `motion/slow` | 300–400ms | larger reveals, progress fills |

Easing: standard ease-out for entrances. Respect `prefers-reduced-motion`
(disable non-essential animation).

## Layout

- App shell: persistent sidebar (desktop) / bottom or drawer nav (mobile) +
  topbar.
- Content max width ~1200px; reading content narrower (~720px).
- Grid: 12 columns desktop, 4 columns mobile, 24px gutter.

## Iconography

- Single line-icon set, 1.5–2px stroke, consistent corner radius.
- Icons support meaning; labels accompany icons in primary navigation.

## Accessibility

- Contrast: body text ≥ 4.5:1, large text ≥ 3:1, UI borders visible.
- Focus: visible ring using `accent/primary`.
- Hit targets ≥ 44×44px on touch.
- Never encode meaning by color alone (pair with icon/label).

## Implementation note

Tokens are implemented once as CSS variables / Tailwind theme extensions and
consumed by `components/ui`. Changing a token propagates everywhere; changing a
component never introduces a new raw value.
