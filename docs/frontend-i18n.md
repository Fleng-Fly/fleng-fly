# Frontend i18n (EN / UK)

Fleng supports English and Ukrainian in its static HTML and vanilla JavaScript.

## Principles

- **One HTML page per route.** Static text carries `data-i18n="key"`; attribute text
  uses `data-i18n-attr="placeholder:key;aria-label:key"`. The English text stays in the
  HTML as the no-JavaScript fallback.
- **Dynamic text uses `t(key, params)` / `tn(key, count, params)`** from
  `frontend/js/i18n.js`. Results are assigned with `textContent` / `setAttribute`
  only (never `innerHTML`), so dictionary text and parameters cannot inject markup.
- **Interface language and learning content.** Menus, instructions, feedback and
  result screens use the selected language. Authored English prompts, choices,
  reading passages and study words keep their original text.
- **English fallback:** a missing Ukrainian key falls back to English, an unknown key
  returns the key itself so gaps are visible.

## Files

| File | Role |
| --- | --- |
| `frontend/js/i18n.js` | `t`, `tn`, `applyDom`, `setLang`, `applyUserLanguage`, `createLanguageSwitch` |
| `frontend/js/i18n-boot.js` | blocking `<head>` script: sets `<html lang>` early, hides the page for an instant in Ukrainian to avoid an English flash (1.5 s safety timeout) |
| `frontend/js/i18n/en.js`, `uk.js` | flat dictionaries; identical key sets |
| `scripts/test-i18n.mjs` | key/placeholder parity, plural completeness, every referenced key exists, language logic |
| `scripts/i18n-stub.mjs` | English stand-in used by the vm-based DOM tests |

## Language choice

The initial page uses its saved browser language, then the browser preference
(`uk*` selects Ukrainian), then English. After session restore, the account
preference wins unless an explicit browser choice is awaiting synchronization.

- Signed in: the EN/УК switch (header, workspace top bar) and **Settings → Language**
  save `preferredLanguage` (`"English"` / `"Ukrainian"`). Workspace pages reload
  to render their dynamic content in the chosen language.
- Signed out: the choice is stored locally and flagged `fleng.lang.pending`; after the
  next sign-in it is saved to the account. Otherwise the account preference wins.
- `document.documentElement.lang` always matches the active language.

## Plurals

Ukrainian needs one / few / many / other. Use `tn('catalog.lessonCount', n)` with the
four keys `….one/few/many/other` (English needs `one` + `other`). `Intl.PluralRules`
selects the form.

## API errors

`describeApiError` maps `error.code` to `errors.<CODE>` keys, then falls back
to localized status or generic copy.

## Learning screens and Fleng AI

- Placement instructions, skills, result labels, limitations and recommendations
  use the dictionaries. Completed reviews include `explanationUk` for all 36
  current bank questions, including older attempts with matching saved content.
- Course exercises use the authored instruction for the active language or the
  instruction for that exercise type. Feedback uses available Ukrainian
  explanations and falls back to English for legacy content. Reading is available
  inside lessons and Placement; the standalone Reading feature was retired.
- Fleng AI controls, status messages and dates use the active locale. Conversation
  content comes from the learner and the configured provider.
- Progress displays earned achievements from `GET /api/v1/achievements/me`, with
  dictionary titles by achievement code.

## Adding a string

1. Add the key to **both** dictionaries (same key, same `{placeholders}`).
2. Use `data-i18n` in HTML or `t()` in JS.
3. Run `npm run frontend:test`. `test-i18n.mjs` checks keys and placeholders.
