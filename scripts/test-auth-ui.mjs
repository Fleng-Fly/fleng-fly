import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import english from '../frontend/js/i18n/en.js';

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.dataset = {}; this.events = {}; this.value = '';
    this.disabled = false; this.hidden = false; this.textContent = '';
    const classes = new Set();
    this.classList = { add: (v) => classes.add(v), remove: (v) => classes.delete(v), contains: (v) => classes.has(v) };
  }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute() {}
  addEventListener(name, fn) { this.events[name] = fn; }
  reportValidity() { return true; }
  reset() { this.wasReset = true; }
}

async function page(name, api = {}, search = '?token=private-reset-secret') {
  const nodes = new Map();
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const location = { search, pathname: `/${name}.html`, href: 'unchanged' };
  const urls = [];
  const context = vm.createContext({
    document: { getElementById: node, createElement: (tag) => new Element(tag) },
    location, window: { location }, URLSearchParams,
    history: { replaceState: (_a, _b, url) => urls.push(url) },
  });
  const module = new vm.SourceTextModule(await readFile(`frontend/js/${name}.js`, 'utf8'), { context });
  await module.link((specifier) => {
    const values = specifier === './api.js' ? api
      : specifier === './errors.js' ? { describeApiError: (e) => e.message }
      : specifier === './i18n.js' ? { t: (key) => english[key] ?? key, applyUserLanguage: async () => {}, createLanguageSwitch: () => new Element() }
      : specifier === './session.js' ? { redirectIfSignedIn: async () => null, setupGoogleSignIn: async () => '' }
      : { mountHeader: () => {} };
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  return { node, location, urls, module, submit: async (id) => node(id).events.submit({ preventDefault() {} }) };
}

test('reset handles missing token, mismatch, retry, success and used token without storing secret', async () => {
  const calls = [];
  let failure = new Error('Network unavailable');
  const api = { confirmPasswordReset: async (...args) => { calls.push(args); if (failure) throw failure; }, setAccessToken: () => {} };
  const missing = await page('reset-password', api, '');
  assert.match(missing.node('reset-status').textContent, /missing/);
  const app = await page('reset-password', api);
  assert.deepEqual(app.urls, ['/reset-password.html']);
  app.node('new-password').value = 'new-password';
  app.node('confirm-password').value = 'different';
  await app.submit('reset-password-form');
  assert.equal(calls.length, 0);
  assert.match(app.node('reset-status').textContent, /do not match/);
  app.node('confirm-password').value = 'new-password';
  await app.submit('reset-password-form');
  assert.equal(app.node('reset-submit').disabled, false);
  assert.match(app.node('reset-status').textContent, /Network/);
  failure = null;
  await app.submit('reset-password-form');
  assert.deepEqual(calls[1], ['private-reset-secret', 'new-password']);
  assert.equal(app.node('reset-password-form').hidden, true);
  assert.equal(app.node('reset-password-form').wasReset, true);
  const used = await page('reset-password', {
    ...api, confirmPasswordReset: async () => { throw { code: 'INVALID_RESET_TOKEN' }; },
  });
  used.node('new-password').value = used.node('confirm-password').value = 'new-password';
  await used.submit('reset-password-form');
  assert.match(used.node('reset-status').textContent, /expired or has already been used/);
  assert.equal(used.node('reset-password-form').hidden, true);
});

test('login reset request shows generic success and recovers from failure', async () => {
  let failure = true;
  const app = await page('login', {
    login: async () => {}, setAccessToken: () => {},
    requestPasswordReset: async (email) => { assert.equal(email, 'me@example.com'); if (failure) throw new Error('Unavailable'); },
  });
  app.node('reset-email').value = ' me@example.com ';
  await app.submit('reset-request-form');
  assert.equal(app.node('reset-request-button').disabled, false);
  assert.match(app.node('reset-request-status').textContent, /Unavailable/);
  failure = false;
  await app.submit('reset-request-form');
  assert.match(app.node('reset-request-status').textContent, /If the account exists/);
});

test('header logout failure preserves session and permits retry; success redirects', async () => {
  let failure = true, cleared = 0;
  const app = await page('layout', {
    getCurrentUser: async () => {}, getHealth: async () => {},
    logout: async () => { if (failure) throw new Error('Network'); },
    setAccessToken: () => { cleared++; },
  });
  await app.module.namespace.mountHeader('home', { displayName: 'Me' });
  assert.equal(app.node('site-header').children[0].children[0].href, '/dashboard.html');
  const auth = app.node('site-header').children[0].children[2];
  const button = auth.children.find((n) => n.tag === 'button');
  await button.events.click();
  assert.equal(app.location.href, 'unchanged');
  assert.equal(cleared, 0);
  assert.equal(button.disabled, false);
  assert.match(auth.children.at(-1).textContent, /confirm logout/);
  failure = false;
  await button.events.click();
  assert.equal(app.location.href, '/index.html');
  assert.equal(cleared, 1);
});

test('independent tabs rotate a shared cookie sequentially and serialize logout', async () => {
  let cookie = 0, reused = false, refreshes = 0, active = 0, peak = 0;
  let queue = Promise.resolve();
  const locks = { request: (name, options, action) => {
    assert.equal(name, 'fleng.auth-cookie');
    assert.equal(options.mode, 'exclusive');
    const next = queue.then(action);
    queue = next.catch(() => {});
    return next;
  } };
  const fetch = async (url, init) => {
    if (url.endsWith('/users/me')) {
      return init.headers.Authorization ? Response.json({ id: 'user' }) : new Response('{}', { status: 401 });
    }
    if (url.endsWith('/auth/logout')) {
      assert.equal(active, 0);
      return new Response(null, { status: 204 });
    }
    assert.ok(url.endsWith('/auth/refresh'));
    const sentCookie = cookie;
    active++; peak = Math.max(peak, active);
    await new Promise((resolve) => setTimeout(resolve, 3));
    active--; refreshes++;
    if (sentCookie !== cookie) { reused = true; return new Response('{}', { status: 401 }); }
    cookie++;
    return Response.json({ accessToken: `access-${cookie}` });
  };
  const source = await readFile('frontend/js/api.js', 'utf8');
  const tabs = [];
  for (let i = 0; i < 4; i++) {
    const context = vm.createContext({ fetch, navigator: { locks }, URLSearchParams,
      crypto: { randomUUID: () => 'logout' }, localStorage: { setItem() {} } });
    const module = new vm.SourceTextModule(source, { context });
    await module.link(() => { throw new Error('Unexpected import'); });
    await module.evaluate();
    tabs.push(module.namespace);
  }
  const users = await Promise.all(tabs.map((api) => api.getCurrentUser()));
  assert.equal(users.length, 4);
  assert.equal(refreshes, 4);
  assert.equal(peak, 1);
  assert.equal(reused, false);
  tabs[0].setAccessToken(null);
  await Promise.all([tabs[0].getCurrentUser(), tabs[1].logout()]);
  assert.equal(reused, false);
});
