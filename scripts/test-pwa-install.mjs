// Regression checks for removing installation from new and previously visited sites.
import { readFileSync, readdirSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';
const source = readFileSync(new URL('../frontend/js/pwa.js', import.meta.url), 'utf8');
async function setup({ unavailable = false, fail = false } = {}) {
  const events = {}, removed = [], deleted = [];
  const origin = 'https://fleng.test';
  const registration = (label, scriptURL, scope) => ({
    scope, active: { scriptURL }, unregister: async () => { removed.push(label); },
  });
  const registrations = [
    registration('fleng', `${origin}/sw.js`, `${origin}/`),
    registration('other-root', `${origin}/other-worker.js`, `${origin}/`),
    registration('nested', `${origin}/sw.js`, `${origin}/nested/`),
    registration('other-origin', 'https://other.test/sw.js', 'https://other.test/'),
  ];
  const caches = { keys: async () => ['fleng-offline-v1', 'other-app'], delete: async (key) => { deleted.push(key); } };
  runInNewContext(source, {
    window: { location: { origin }, caches, addEventListener: (name, fn) => { events[name] = fn; } },
    navigator: unavailable ? {} : { serviceWorker: { getRegistrations: async () => {
      if (fail) throw new Error('Unavailable');
      return registrations;
    } } },
    caches,
  });
  await new Promise((resolve) => setImmediate(resolve));
  return { events, removed, deleted };
}
const app = await setup();
assert.deepEqual(app.removed, ['fleng']);
assert.deepEqual(app.deleted, ['fleng-offline-v1']);
let prevented = false;
app.events.beforeinstallprompt({ preventDefault() { prevented = true; }, prompt() { throw new Error('Must never show installation'); } });
assert.equal(prevented, true);
assert.deepEqual((await setup({ unavailable: true })).removed, []);
assert.deepEqual((await setup({ fail: true })).deleted, ['fleng-offline-v1']);
const root = new URL('../frontend/', import.meta.url);
for (const file of readdirSync(root).filter((file) => file.endsWith('.html'))) {
  const html = readFileSync(new URL(file, root), 'utf8');
  assert.doesNotMatch(html, /rel=["']manifest["']|apple-mobile-web-app|href=["']\/install\.html["']|Встановити|Встановлення|Встанови Fleng/, file);
}
const redirect = readFileSync(new URL('install.html', root), 'utf8');
assert.match(redirect, /http-equiv="refresh" content="0; url=\/dashboard.html"/);
assert.deepEqual(JSON.parse(readFileSync(new URL('manifest.webmanifest', root), 'utf8')), {});
console.log('Installation removal: no UI/manifest links, legacy redirect, selective unregister, prompt suppression and failure tolerance passed.');
