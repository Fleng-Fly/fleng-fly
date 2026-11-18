import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import english from '../frontend/js/i18n/en.js';

class ClassList {
  constructor(initial = []) { this.set = new Set(initial); }
  add(v) { this.set.add(v); }
  remove(v) { this.set.delete(v); }
  contains(v) { return this.set.has(v); }
}

async function load({ user, providers = { google: true }, search = '', error } = {}) {
  const root = { classList: new ClassList(['session-pending']) };
  const block = { classList: new ClassList(['hidden']) };
  const location = { search, replaced: null, replace(url) { this.replaced = url; } };
  const api = {
    getCurrentUser: async () => { if (error) throw error; return user; },
    getAuthProviders: async () => providers,
    setAccessToken: () => {},
  };
  const context = vm.createContext({
    document: { documentElement: root, getElementById: (id) => (id === 'google-block' ? block : null) },
    window: { location }, URLSearchParams,
  });
  const module = new vm.SourceTextModule(await readFile('frontend/js/session.js', 'utf8'), { context });
  await module.link((spec) => {
    const values = spec === './api.js' ? api : { t: (key) => english[key] ?? key };
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [k, v] of Object.entries(values)) this.setExport(k, v);
    }, { context });
  });
  await module.evaluate();
  return { session: module.namespace, root, block, location };
}

test('signed-in visitors of entry pages go straight to the dashboard without revealing the page', async () => {
  const { session, root, location } = await load({ user: { email: 'a@b.co' } });
  assert.ok(await session.redirectIfSignedIn());
  assert.equal(location.replaced, '/dashboard.html');
  assert.ok(root.classList.contains('session-pending'));
});

test('signed-out visitors see the page; a 401 or outage never blocks it', async () => {
  for (const error of [Object.assign(new Error('x'), { status: 401 }), new Error('offline')]) {
    const { session, root, location } = await load({ error });
    assert.equal(await session.redirectIfSignedIn(), null);
    assert.equal(location.replaced, null);
    assert.ok(!root.classList.contains('session-pending'));
  }
});

test('Google button appears only when the server has Google configured', async () => {
  const on = await load({ providers: { google: true } });
  assert.equal(await on.session.setupGoogleSignIn(), '');
  assert.ok(!on.block.classList.contains('hidden'));
  const off = await load({ providers: { google: false } });
  await off.session.setupGoogleSignIn();
  assert.ok(off.block.classList.contains('hidden'));
});

test('failed Google attempts explain themselves; unrelated error codes are ignored', async () => {
  const denied = await load({ search: '?error=google_denied' });
  assert.equal(await denied.session.setupGoogleSignIn(), english['auth.googleDenied']);
  const unknown = await load({ search: '?error=google_weird' });
  assert.equal(await unknown.session.setupGoogleSignIn(), english['auth.googleFailed']);
  const other = await load({ search: '?error=something' });
  assert.equal(await other.session.setupGoogleSignIn(), '');
});
