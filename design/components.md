# Components

> Inventory and states for the eventual `components/ui` layer. Build these only
> as screens need them — this is a reference, not a mandate to implement all now
> (`AGENTS.md` rule 2/9).

## Foundations

- **Button** — variants: `primary` (violet), `secondary`, `ghost`, `danger`;
  sizes `sm/md/lg`; states: default/hover/active/focus/disabled/loading.
- **Input / Textarea / Select** — label, helper, error, disabled, focus ring.
- **Checkbox / Radio / Switch** — accessible labels, keyboard operable.
- **Badge / Tag / Pill** — status and labels; optional accent gradient.
- **Avatar** — image + fallback initials.
- **Divider / Separator**.

## Surfaces

- **Card** — base surface, optional raised/glass variant, optional accent border.
- **Panel / SectionHeader** — titled content region.
- **Modal / Dialog** — focus trap, Escape to close, glass backdrop.
- **Drawer / Sheet** — mobile navigation and side panels.
- **Tooltip / Popover** — concise contextual help.

## Navigation

- **SidebarNav** — desktop primary navigation (see `design/pages.md`).
- **Topbar** — search, streak, XP, notifications, profile menu.
- **BottomNav / MobileDrawer** — mobile equivalent.
- **Tabs / SegmentedControl** — within-page sections.
- **Breadcrumbs** — course → lesson context.

## Feedback & state

- **Toast** — transient success/error/info.
- **Alert / InlineMessage** — persistent messages.
- **ProgressBar / ProgressRing** — course/lesson/XP progress (accent gradient).
- **Skeleton** — loading placeholders.
- **EmptyState** — illustration + message + primary action.
- **Spinner** — only for short waits; prefer skeletons.

## Gamification

- **StreakIndicator** — current streak with flame treatment (accent, not
  overdone).
- **XpBar / LevelBadge** — gradient fill; level number.
- **AchievementCard / Badge** — locked vs earned states.
- **ChallengeCard** — goal, progress, time remaining.

## Learning-specific

- **ExerciseCard / ExerciseRenderer** — dispatches by exercise `type`.
- **AnswerOption** — selectable, correct/incorrect states.
- **Flashcard** — front/back, reveal, rating controls.
- **AudioPlayer** — for listening; accessible controls.
- **Recorder** — for speaking (planned; defer until voice work).
- **AI ChatBubble / TypingIndicator** — tutor conversation.

## State conventions

- **Focus:** visible ring (`accent/primary`), never removed.
- **Disabled:** reduced opacity + `cursor: not-allowed`, still legible.
- **Loading:** component-level (skeleton/spinner), never a full-page blocker
  unless unavoidable.
- **Error:** inline where possible; toast only for transient/global errors.
- **Empty:** explain what will appear and the next action.

## Rules

- Components are presentational; data fetching and business rules live in hooks
  and the API client (`docs/frontend.md`).
- Variants come from tokens, not ad-hoc styles.
- Every interactive component is keyboard accessible and labelled.
