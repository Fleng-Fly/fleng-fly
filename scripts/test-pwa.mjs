// Retiring legacy workers must preserve other apps and avoid intercepting traffic.
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';
const handlers = {};
const deleted = [];
let skipped = 0, claimed = 0, unregistered = 0;
runInNewContext(readFileSync(new URL('../frontend/sw.js', import.meta.url), 'utf8'), {
  self: {
    addEventListener: (name, fn) => { handlers[name] = fn; },
    skipWaiting: async () => { skipped++; },
    clients: { claim: async () => { claimed++; } },
    registration: { unregister: async () => { unregistered++; } },
  },
  caches: {
    keys: async () => ['fleng-offline-v0', 'fleng-offline-v1', 'other-app', 'unrelated-cache'],
    delete: async (key) => { deleted.push(key); },
  },
});
const run = (name) => new Promise((resolve, reject) => handlers[name]({ waitUntil: (p) => p.then(resolve, reject) }));
await run('install');
await run('activate');
assert.equal(skipped, 1);
assert.equal(claimed, 1);
assert.equal(unregistered, 1);
assert.deepEqual(deleted, ['fleng-offline-v0', 'fleng-offline-v1']);
assert.equal(handlers.fetch, undefined);
console.log('Legacy worker retirement: unregister, no fetch interception, isolated cache cleanup passed.');
