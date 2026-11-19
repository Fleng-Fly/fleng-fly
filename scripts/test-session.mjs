import './require-vm-modules.mjs';
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
  const button = {
    attrs: {}, classList: new ClassList(), listeners: {},
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k] ?? null; },
    removeAttribute(k) { delete this.attrs[k]; },
    addEventListener(type, fn) { this.listeners[type] = fn; },
  };
  const pageshow = [];
  const location = { search, replaced: null, replace(url) { this.replaced = url; } };
  const api = {
    getCurrentUser: async () => { if (error) throw error; return user; },
    getAuthProviders: async () => providers,
    setAccessToken: () => {},
  };
  const context = vm.createContext({
    document: { documentElement: root, getElementById: (id) => (id === 'google-block' ? block : id === 'google-button' ? button : null) },
    window: { location, addEventListener: (type, fn) => { if (type === 'pageshow') pageshow.push(fn); } }, URLSearchParams,
  });
  const module = new vm.SourceTextModule(await readFile('frontend/js/session.js', 'utf8'), { context });
  await module.link((spec) => {
    const values = spec === './api.js' ? api : { t: (key) => english[key] ?? key };
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [k, v] of Object.entries(values)) this.setExport(k, v);
    }, { context });
  });
  await module.evaluate();
  return { session: module.namespace, root, block, location, button, pageshow };
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
  const needsLink = await load({ search: '?error=google_link_required' });
  assert.equal(await needsLink.session.setupGoogleSignIn(), english['auth.googleLinkRequired']);
  const unknown = await load({ search: '?error=google_weird' });
  assert.equal(await unknown.session.setupGoogleSignIn(), english['auth.googleFailed']);
  const other = await load({ search: '?error=something' });
  assert.equal(await other.session.setupGoogleSignIn(), '');
});

test('the Google button ignores repeated clicks while the browser redirects, and recovers on back', async () => {
  const { session, button, pageshow } = await load({ providers: { google: true } });
  await session.setupGoogleSignIn();
  let prevented = 0;
  const click = () => button.listeners.click({ preventDefault: () => { prevented += 1; } });
  click();
  assert.equal(prevented, 0, 'the first click follows the OAuth link');
  assert.equal(button.getAttribute('aria-disabled'), 'true');
  assert.ok(button.classList.contains('is-busy'));
  click();
  assert.equal(prevented, 1, 'a second click is cancelled');
  pageshow[0]({ persisted: true });
  assert.equal(button.getAttribute('aria-disabled'), null);
  click();
  assert.equal(prevented, 1);
});

test('the button stays unguarded and hidden when Google is unavailable', async () => {
  const { session, button } = await load({ providers: { google: false } });
  await session.setupGoogleSignIn();
  assert.equal(button.listeners.click, undefined);
});

for (const [page, file] of [['login', 'frontend/login.html'], ['register', 'frontend/register.html']]) {
  test(`${page} page: hidden Google block after the form, same OAuth route, no credentials`, async () => {
    const html = await readFile(file, 'utf8');
    const form = html.indexOf('</form>');
    const block = html.indexOf('id="google-block" class="hidden"');
    assert.ok(form > 0 && block > form, 'the Google block follows the main form');
    assert.match(html, new RegExp(`href="/api/v1/auth/google/start\\?page=${page}"`));
    assert.match(html.slice(block), /<svg viewBox="0 0 48 48"/); // the official four-colour G
    assert.doesNotMatch(html, /client_secret|GOOGLE_CLIENT|accounts\.google\.com/i);
  });
}
