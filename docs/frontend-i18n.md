# Frontend i18n (EN / UK)

> Status: implemented in the UX overhaul. Plain vanilla JavaScript, no build step,
> one HTML file per page.

## Principles

- **One HTML page per route.** Static text carries `data-i18n="key"`; attribute text
  uses `data-i18n-attr="placeholder:key;aria-label:key"`. The English text stays in the
  HTML as the no-JavaScript fallback.
- **Dynamic text uses `t(key, params)` / `tn(key, count, params)`** from
  `frontend/js/i18n.js`. Results are assigned with `textContent` / `setAttribute`
  only (never `innerHTML`), so dictionary text and parameters cannot inject markup.
- **Interface and explanations are translated; English lesson content is not.**
  Lesson prompts, options, theory and vocabulary stay English.
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

Priority: explicit choice (`localStorage['fleng.lang']`) → account `preferredLanguage`
→ browser language (`uk*` → Ukrainian) → English.

- Signed in: the EN/УК switch (header, workspace top bar) and **Settings → Language**
  apply immediately and save `preferredLanguage` (`"English"` / `"Ukrainian"`, the
  existing backend values – no migration).
- Signed out: the choice is stored locally and flagged `fleng.lang.pending`; after the
  next sign-in it is saved to the account. Otherwise the account preference wins.
- `document.documentElement.lang` always matches the active language.

## Plurals

Ukrainian needs one / few / many / other. Use `tn('catalog.lessonCount', n)` with the
four keys `….one/few/many/other` (English needs `one` + `other`). `Intl.PluralRules`
selects the form.

## API errors

`describeApiError` maps `error.code` to `errors.<CODE>` keys, then to status keys
(`errors.401`, `errors.422`, …). The backend message is only a last resort.

## Not translated yet / dependencies

- Text produced by the backend (placement result label, limitations, recommendation
  note, per-question explanations; exercise `explanation` text) stays English until
  the API returns translatable codes or a `lang` parameter.
- The AI assistant widget (`ai-assistant.js`) is disabled by default and not yet
  localized.
- Exercise **hints** and Ukrainian explanations need backend support (the exercise API
  exposes no `hint` field), so no "Підказка" button is shown.

## Adding a string

1. Add the key to **both** dictionaries (same key, same `{placeholders}`).
2. Use `data-i18n` in HTML or `t()` in JS.
3. Run `pnpm frontend:test` – `test-i18n.mjs` fails on a missing or mismatched key.
