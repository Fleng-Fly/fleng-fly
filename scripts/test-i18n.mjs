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
