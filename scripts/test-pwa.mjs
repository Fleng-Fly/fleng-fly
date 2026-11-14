// Functional worker tests, including private/API traffic bypass and cache isolation.
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';

const handlers = {};
const cached = [];
const deleted = [];
let networkFails = false;
const offline = new Response('offline page');
runInNewContext(readFileSync(new URL('../frontend/sw.js', import.meta.url), 'utf8'), {
  self: {
    location: { origin: 'https://fleng.test' },
    addEventListener: (name, fn) => { handlers[name] = fn; },
    skipWaiting() {}, clients: { claim: async () => {} },
  },
  URL, Response, Promise,
  caches: {
    open: async () => ({ add: async (path) => cached.push(path) }),
    keys: async () => ['fleng-offline-v0', 'fleng-offline-v1', 'fleng-offline-v2', 'unrelated-app'],
    delete: async (key) => deleted.push(key),
    match: async () => offline,
  },
  fetch: async () => {
    if (networkFails) throw new TypeError('Network unavailable');
    return new Response('live response');
  },
});
await new Promise((resolve, reject) => handlers.install({ waitUntil: (p) => p.then(resolve, reject) }));
assert.deepEqual(cached, ['/offline.html']);
await new Promise((resolve, reject) => handlers.activate({ waitUntil: (p) => p.then(resolve, reject) }));
assert.deepEqual(deleted, ['fleng-offline-v0', 'fleng-offline-v1']);
function navigate(path, mode = 'navigate', method = 'GET') {
  let result;
  handlers.fetch({ request: { url: new URL(path, 'https://fleng.test').href, mode, method },
    respondWith: (p) => { result = p; } });
  return result;
}
for (const path of ['/api/v1/users/me', '/api/v1/lessons/x/submit', '/api', '/docs', '/openapi.json', 'https://other.test/page']) {
  assert.equal(navigate(path), undefined, path);
}
assert.equal(navigate('/api/v1/auth/login', 'cors', 'POST'), undefined);
assert.equal(navigate('/js/api.js', 'cors'), undefined);
assert.equal(await (await navigate('/dashboard.html')).text(), 'live response');
networkFails = true;
assert.equal(await (await navigate('/dashboard.html')).text(), 'offline page');
assert.equal(navigate('/api/v1/progress/me'), undefined);
console.log('PWA worker: offline fallback, network-first pages, API bypass and cache isolation passed.');
