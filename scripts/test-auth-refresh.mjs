import { readFileSync } from 'node:fs';
import { SourceTextModule, createContext } from 'node:vm';
import assert from 'node:assert/strict';

async function setup(locks, authorized = false) {
  const calls = [];
  const context = createContext({ navigator: locks ? { locks } : {}, fetch: async (url) => {
    calls.push(url);
    if (authorized && url.endsWith('/users/me')) return { ok: true, status: 200, json: async () => ({ email: 'me@example.com' }) };
    if (url.endsWith('/auth/refresh')) return { ok: true, status: 200, json: async () => ({ accessToken: 'new' }) };
    return { ok: false, status: 401, json: async () => ({}) };
  } });
  const module = new SourceTextModule(readFileSync(new URL('../frontend/js/api.js', import.meta.url), 'utf8'), { context });
  await module.link(() => {});
  await module.evaluate();
  return { api: module.namespace, calls };
}
const absent = await setup();
absent.api.setAccessToken('valid');
assert.equal(absent.api.getAccessToken(), 'valid');
assert.deepEqual(absent.calls, []);
await assert.rejects(absent.api.getCurrentUser(), (error) => error.status === 401);
assert.deepEqual(absent.calls, ['/api/v1/users/me']);
assert.equal(absent.api.getAccessToken(), null);
let held = false;
const coordinated = await setup({ request: async (name, action) => {
  assert.equal(name, 'fleng-auth-refresh');
  held = true;
  try { return await action(); } finally { held = false; }
} });
await assert.rejects(coordinated.api.getCurrentUser());
assert.equal(coordinated.calls.filter(url => url.endsWith('/auth/refresh')).length, 1);
assert.equal(held, false);
console.log('Refresh requires Web Locks only when needed; no unsafe fallback.');

const valid = await setup(undefined, true);
valid.api.setAccessToken('valid');
assert.equal((await valid.api.getCurrentUser()).email, 'me@example.com');
assert.equal(valid.api.getAccessToken(), 'valid');
const denied = await setup({ request: async () => { throw new Error('Locks unavailable'); } });
await assert.rejects(denied.api.getCurrentUser(), error => error.status === 401);
assert.deepEqual(denied.calls, ['/api/v1/users/me']);
