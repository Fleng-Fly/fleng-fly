import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { test } from 'node:test';
import en from '../frontend/js/i18n/en.js';
import uk from '../frontend/js/i18n/uk.js';

const placeholders = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(',');

test('English and Ukrainian dictionaries have the same keys and placeholders', () => {
  assert.deepEqual(Object.keys(uk).sort(), Object.keys(en).sort());
  for (const [key, value] of Object.entries(en)) {
    assert.ok(typeof value === 'string' && value.trim(), `empty English text: ${key}`);
    assert.ok(typeof uk[key] === 'string' && uk[key].trim(), `empty Ukrainian text: ${key}`);
    assert.equal(placeholders(uk[key]), placeholders(value), `placeholders differ: ${key}`);
    assert.ok(!/[<>]/.test(value + uk[key]), `markup in dictionary text: ${key}`);
  }
});

test('Ukrainian plural keys are complete (one, few, many, other)', () => {
  const bases = new Set(Object.keys(uk).filter((k) => k.endsWith('.other')).map((k) => k.slice(0, -6)));
  for (const base of bases) {
    for (const form of ['one', 'few', 'many', 'other']) assert.ok(uk[`${base}.${form}`], `${base}.${form}`);
    for (const form of ['one', 'other']) assert.ok(en[`${base}.${form}`], `en ${base}.${form}`);
  }
});

test('every key referenced from HTML and JS exists in the dictionaries', async () => {
  const missing = [];
  const files = [];
  for (const name of await readdir('frontend')) if (name.endsWith('.html')) files.push(`frontend/${name}`);
  for (const name of await readdir('frontend/js')) if (name.endsWith('.js')) files.push(`frontend/js/${name}`);
  for (const file of files) {
    const text = await readFile(file, 'utf8');
    const keys = [
      ...[...text.matchAll(/data-i18n="([\w.]+)"/g)].map((m) => m[1]),
      ...[...text.matchAll(/data-i18n-attr="([^"]+)"/g)].flatMap((m) => m[1].split(';').map((p) => p.split(':')[1]?.trim())),
      ...[...text.matchAll(/\bt\('([\w.]+)'/g)].map((m) => m[1]),
      ...[...text.matchAll(/\btn\('([\w.]+)'/g)].map((m) => `${m[1]}.other`),
    ].filter(Boolean);
    for (const key of keys) if (!(key in en)) missing.push(`${file}: ${key}`);
  }
  assert.deepEqual(missing, []);
});

// Run the real i18n.js against a minimal browser stand-in.
async function loadI18n({ stored = null, languages = ['en-US'], updateCurrentUser = async () => ({}) } = {}) {
  const { default: vm } = await import('node:vm');
  const storage = new Map(stored ? [['fleng.lang', stored]] : []);
  const classes = new Set(['i18n-pending']);
  const events = [];
  const documentElement = { lang: '', classList: { remove: (c) => classes.delete(c), add: (c) => classes.add(c) } };
  const context = vm.createContext({
    window: {
      localStorage: { getItem: (k) => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, v), removeItem: (k) => storage.delete(k) },
      addEventListener() {}, dispatchEvent: (e) => events.push(e),
    },
    document: { documentElement, querySelectorAll: () => [] },
    navigator: { languages }, CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init?.detail; } },
    Intl,
  });
  const source = await readFile('frontend/js/i18n.js', 'utf8');
  const module = new vm.SourceTextModule(source, { context });
  await module.link(async (specifier) => {
    const values = specifier.endsWith('en.js') ? { default: en } : specifier.endsWith('uk.js') ? { default: uk } : { updateCurrentUser };
    return new vm.SyntheticModule(Object.keys(values), function () { for (const [k, v] of Object.entries(values)) this.setExport(k, v); }, { context });
  });
  await module.evaluate();
  return { api: module.namespace, storage, documentElement, classes, events };
}

test('language detection: stored choice > browser language > English', async () => {
  assert.equal((await loadI18n({ languages: ['uk-UA'] })).api.getLang(), 'uk');
  assert.equal((await loadI18n({ languages: ['de-DE'] })).api.getLang(), 'en');
  assert.equal((await loadI18n({ stored: 'en', languages: ['uk'] })).api.getLang(), 'en');
});

test('t() falls back to English then to the key; params are interpolated as plain text', async () => {
  const { api } = await loadI18n({ languages: ['uk'] });
  assert.equal(api.t('auth.login'), uk['auth.login']);
  assert.equal(api.t('no.such.key'), 'no.such.key');
  assert.equal(api.t('dashboard.greeting', { name: '<b>Ann</b>' }), uk['dashboard.greeting'].replace('{name}', '<b>Ann</b>'));
});

test('Ukrainian plural forms follow CLDR (1 / 2-4 / 5+)', async () => {
  const { api } = await loadI18n({ languages: ['uk'] });
  assert.equal(api.tn('catalog.lessonCount', 1), '1 урок');
  assert.equal(api.tn('catalog.lessonCount', 3), '3 уроки');
  assert.equal(api.tn('catalog.lessonCount', 5), '5 уроків');
  assert.equal(api.tn('catalog.lessonCount', 21), '21 урок');
});

test('setLang stores the choice, sets <html lang> and saves to the account only when asked', async () => {
  const calls = [];
  const { api, storage, documentElement } = await loadI18n({ languages: ['en'], updateCurrentUser: async (body) => { calls.push(body); } });
  await api.setLang('uk');
  assert.equal(storage.get('fleng.lang'), 'uk');
  assert.equal(documentElement.lang, 'uk');
  assert.equal(calls.length, 0);
  assert.equal(storage.get('fleng.lang.pending'), '1');
  await api.setLang('en', { persistToAccount: true });
  assert.equal(JSON.stringify(calls), '[{"preferredLanguage":"English"}]');
  assert.equal(storage.get('fleng.lang.pending') ?? null, null);
});

test('account preference wins unless a signed-out choice is pending', async () => {
  const a = await loadI18n({ languages: ['en'] });
  await a.api.applyUserLanguage({ preferredLanguage: 'Ukrainian' });
  assert.equal(a.api.getLang(), 'uk');
  const saved = [];
  const b = await loadI18n({ languages: ['en'], updateCurrentUser: async (body) => { saved.push(body); } });
  await b.api.setLang('uk');
  await b.api.applyUserLanguage({ preferredLanguage: 'English' });
  assert.equal(b.api.getLang(), 'uk');
  assert.equal(JSON.stringify(saved), '[{"preferredLanguage":"Ukrainian"}]');
});
