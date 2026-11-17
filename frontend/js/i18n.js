/**
 * Minimal EN/UK interface i18n for the static, build-free frontend.
 *
 * - One HTML file per page; static text is marked with `data-i18n*` attributes
 *   and dynamic text goes through `t()` / `tn()`.
 * - Translations are plain strings assigned with `textContent` / `setAttribute`,
 *   never `innerHTML`, so dictionary text and parameters cannot inject markup.
 * - English is the fallback for any missing Ukrainian key (and for unknown keys
 *   the key itself is returned so gaps are visible, not blank).
 * - English *lesson content* is never translated here: only the interface.
 *
 * Language choice: explicit choice (localStorage) > account `preferredLanguage`
 * > browser language > English. A choice made while signed out is pushed to the
 * account on the next sign-in; otherwise the account preference wins.
 */
import en from './i18n/en.js';
import uk from './i18n/uk.js';
import { updateCurrentUser } from './api.js';

export const LANGUAGES = ['en', 'uk'];
const DICTIONARIES = { en, uk };
const STORAGE_KEY = 'fleng.lang';
const PENDING_KEY = 'fleng.lang.pending';
// Backend `preferred_language` values (kept for compatibility with existing accounts).
const ACCOUNT_VALUES = { en: 'English', uk: 'Ukrainian' };

function read(key) {
  try { return window.localStorage.getItem(key); } catch { return null; }
}
function write(key, value) {
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch { /* Storage can be blocked; the language then lasts for this page only. */ }
}

export function languageFromAccount(value) {
  if (typeof value !== 'string') return null;
  const normalised = value.trim().toLowerCase();
  if (['ukrainian', 'українська', 'uk'].includes(normalised)) return 'uk';
  if (['english', 'en'].includes(normalised)) return 'en';
  return null;
}

function detect() {
  const stored = read(STORAGE_KEY);
  if (LANGUAGES.includes(stored)) return stored;
  const browser = (navigator.languages?.[0] || navigator.language || 'en').toLowerCase();
  return browser.startsWith('uk') ? 'uk' : 'en';
}

let current = detect();

export function getLang() {
  return current;
}

function interpolate(template, params) {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    Object.hasOwn(params, name) ? String(params[name]) : match);
}

export function t(key, params) {
  const value = DICTIONARIES[current][key] ?? DICTIONARIES.en[key];
  return value === undefined ? key : interpolate(value, params);
}

/** Plural-aware lookup: `key.one`/`key.few`/`key.many`/`key.other` (Ukrainian has all four). */
export function tn(key, count, params) {
  const category = new Intl.PluralRules(current).select(count);
  const dictionary = DICTIONARIES[current];
  const resolved = [`${key}.${category}`, `${key}.other`]
    .find((candidate) => dictionary[candidate] !== undefined) ?? `${key}.other`;
  return t(resolved, { count, ...params });
}

/** Translate `[data-i18n]`, `[data-i18n-attr]` descendants of `root` (default: document). */
export function applyDom(root = document) {
  for (const node of root.querySelectorAll('[data-i18n]')) {
    node.textContent = t(node.dataset.i18n);
  }
  for (const node of root.querySelectorAll('[data-i18n-attr]')) {
    // "placeholder:search.placeholder;aria-label:search.label"
    for (const pair of node.dataset.i18nAttr.split(';')) {
      const [attribute, key] = pair.split(':').map((part) => part.trim());
      if (attribute && key) node.setAttribute(attribute, t(key));
    }
  }
}

function render() {
  document.documentElement.lang = current;
  applyDom();
  document.documentElement.classList.remove('i18n-pending');
  window.dispatchEvent(new CustomEvent('fleng:language-changed', { detail: { lang: current } }));
}

/**
 * Switch language. `user` (optional) is the signed-in user: the choice is then
 * stored in the account; failures to save never block the switch.
 */
export async function setLang(lang, { persistToAccount = false } = {}) {
  if (!LANGUAGES.includes(lang) || lang === current) return;
  current = lang;
  write(STORAGE_KEY, lang);
  render();
  if (persistToAccount) {
    try {
      await updateCurrentUser({ preferredLanguage: ACCOUNT_VALUES[lang] });
      write(PENDING_KEY, null);
    } catch { /* Keep the choice locally; it is retried on next sign-in. */ }
  } else {
    write(PENDING_KEY, '1');
  }
}

/** Reconcile the interface language with the signed-in account (call once per page). */
export async function applyUserLanguage(user) {
  const account = languageFromAccount(user?.preferredLanguage);
  if (read(PENDING_KEY) === '1' && LANGUAGES.includes(read(STORAGE_KEY))) {
    // The learner picked a language while signed out: keep it and save it.
    try {
      if (account !== current) {
        await updateCurrentUser({ preferredLanguage: ACCOUNT_VALUES[current] });
      }
      write(PENDING_KEY, null);
    } catch { /* Retried on the next page load. */ }
    return;
  }
  if (account && account !== current) {
    current = account;
    write(STORAGE_KEY, account);
    render();
  }
}

/** Compact EN/УК toggle. `getUser` tells whether the choice should be saved to the account. */
export function createLanguageSwitch(isSignedIn = () => false) {
  const group = document.createElement('div');
  group.className = 'lang-switch';
  group.setAttribute('role', 'group');
  group.dataset.i18nAttr = 'aria-label:lang.switch';
  group.setAttribute('aria-label', t('lang.switch'));
  for (const [code, label] of [['en', 'EN'], ['uk', 'УК']]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.lang = code;
    button.dataset.lang = code;
    button.addEventListener('click', () => setLang(code, { persistToAccount: isSignedIn() }));
    group.append(button);
  }
  const sync = () => {
    for (const button of group.querySelectorAll('button')) {
      button.setAttribute('aria-pressed', String(button.dataset.lang === current));
    }
  };
  window.addEventListener('fleng:language-changed', sync);
  sync();
  return group;
}

// Apply on first load; modules are deferred so the DOM is parsed by now.
render();
