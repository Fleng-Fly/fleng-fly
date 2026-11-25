import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Node {
  constructor(tag = 'div', text = '') { this.tagName = tag; this.text = text; this.children = []; this.attributes = {}; this.events = {}; }
  set textContent(value) { this.text = value; this.children = []; }
  get textContent() { return [this.text, ...this.children.map(n => n.textContent)].join(' '); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.text = ''; this.children = nodes; }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(key, callback) { this.events[key] = callback; }
  all(tag) { return this.children.flatMap(n => [...(n.tagName === tag ? [n] : []), ...n.all(tag)]); }
}
const data = () => ({
  lessonsStarted: 4, lessonsCompleted: 3, activeCourses: 1, xp: 47,
  streak: { current: 2, longest: 8 },
  xpHistory: { available: false, last7Days: null, last30Days: null },
  courses: [
    { title: 'Everyday English', slug: 'daily', lessonsTotal: 3, lessonsCompleted: 1, completionPercent: 33.33 },
    { title: 'Completed', slug: 'done', lessonsTotal: 2, lessonsCompleted: 2, completionPercent: 100 },
    { title: 'New course', slug: 'new', lessonsTotal: 0, lessonsCompleted: 0, completionPercent: 0 },
  ],
});
const tick = () => new Promise(resolve => setImmediate(resolve));
async function page(options = {}) {
  const target = new Node();
  const nav = new Node();
  const events = {};
  const window = { location: { replace: url => { window.redirect = url; } },
    addEventListener: (name, fn) => { events[name] = fn; } };
  let value = options.data ?? data(), failure = options.failure;
  let calls = 0, sessions = 0;
  const context = vm.createContext({ Intl, Number, encodeURIComponent, document: {
    getElementById: () => target, querySelector: () => nav,
    createElement: tag => new Node(tag),
  }, window });
  const exports = {
    './api.js': {
      getMyProgress: async () => { calls++; if (options.pending) return options.pending; if (failure) throw failure; return value; },
      getMyAchievements: async () => [{ code: 'first_lesson', title: 'First Lesson', awardedAt: '2026-11-25' }],
    },
    './session.js': { requireSession: async () => { sessions++; return options.noSession ? null : { displayName: 'Learner' }; } },
    './workspace.js': { mountWorkspace() {}, setWorkspaceUser() {} },
    './errors.js': { describeApiError: error => error.message },
    './i18n.js': i18nStub,
  };
  const module = new vm.SourceTextModule(await readFile(new URL('../frontend/js/progress.js', import.meta.url), 'utf8'), { context });
  await module.link(async name => {
    if (name === './layout.js') {
      const layout = new vm.SourceTextModule(await readFile(new URL('../frontend/js/layout.js', import.meta.url), 'utf8'), { context });
      await layout.link((specifier) => specifier === './i18n.js'
        ? new vm.SyntheticModule(Object.keys(i18nStub), function () { for (const [key, value] of Object.entries(i18nStub)) this.setExport(key, value); }, { context })
        : new vm.SyntheticModule(['getCurrentUser', 'getHealth', 'logout', 'setAccessToken'], function () {
          for (const name of ['getCurrentUser', 'getHealth', 'logout', 'setAccessToken']) this.setExport(name, () => {});
        }, { context }));
      return layout;
    }
    const values = exports[name];
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value);
    }, { context });
  });
  await module.evaluate();
  await tick();
  return { target, nav, window, events, calls: () => calls, sessions: () => sessions,
    recover() { failure = null; value = data(); } };
}

test('renders backend metrics, course percentages and unavailable history without a chart', async () => {
  const app = await page();
  const text = app.target.textContent;
  for (const value of ['Completed lessons 3', 'Active courses 1', 'Total XP 47', 'Current streak 2', 'Best streak: 8 days', '33.33%', '100%', 'No published lessons yet.', 'last 7 and 30 days is unavailable']) assert.ok(text.includes(value), value);
  assert.equal(app.target.all('progress')[0].value, 33.33);
  assert.equal(app.target.all('progress')[0].max, 100);
  assert.equal(app.target.all('canvas').length, 0);
  assert.equal(app.target.all('svg').length, 0);
  assert.match(text, /Achievements.*First Lesson/);
  assert.equal(app.calls(), 1);
  assert.equal(app.target.attributes['aria-busy'], 'false');
  // Sidebar highlighting is owned by the shared workspace (mountWorkspace('progress')).
});

test('new user keeps real zero metrics and gets a lesson action', async () => {
  const empty = data();
  Object.assign(empty, { lessonsStarted: 0, lessonsCompleted: 0, activeCourses: 0, xp: 0, courses: [], streak: { current: 0, longest: 0 } });
  const app = await page({ data: empty });
  assert.ok(app.target.textContent.includes('Your progress starts here'));
  assert.ok(app.target.textContent.includes('No published courses'));
  assert.ok(app.target.textContent.includes('Total XP 0'));
  assert.ok(app.target.all('a').some(a => a.href === '/courses.html'));
});

test('loading has no made-up metrics; error retries and session errors redirect', async () => {
  const loading = await page({ pending: new Promise(() => {}) });
  assert.equal(loading.target.attributes['aria-busy'], 'true');
  assert.ok(loading.target.textContent.includes('Loading your progress'));
  assert.equal(loading.target.all('progress').length, 0);
  const app = await page({ failure: Object.assign(new Error('Backend unavailable'), { status: 503 }) });
  assert.ok(app.target.textContent.includes('Backend unavailable'));
  assert.equal(app.target.all('progress').length, 0);
  app.recover();
  await app.target.all('button')[0].events.click();
  assert.ok(app.target.textContent.includes('Total XP 47'));
  assert.equal(app.calls(), 2);
  assert.equal(app.sessions(), 1);
  const auth = await page({ failure: { status: 401 } });
  assert.equal(auth.window.redirect, '/login.html');
  assert.equal((await page({ noSession: true })).calls(), 0);
});

test('malformed metrics fail visibly instead of showing false zeroes', async () => {
  const invalid = data(); delete invalid.activeCourses;
  const app = await page({ data: invalid });
  assert.ok(app.target.textContent.includes('Progress data is incomplete'));
  assert.equal(app.target.all('progress').length, 0);
});

test('untrusted course labels remain text, links are encoded', async () => {
  const unsafe = data();
  unsafe.courses[0].title = '<img src=x onerror=alert(1)>';
  unsafe.courses[0].slug = 'a&next=/other';
  const app = await page({ data: unsafe });
  assert.ok(app.target.textContent.includes(unsafe.courses[0].title));
  assert.equal(app.target.all('img').length, 0);
  assert.equal(app.target.all('a')[0].href, '/course.html?slug=a%26next%3D%2Fother');
});

test('session end discards an outstanding response and BFCache reloads', async () => {
  let resolve;
  const pending = new Promise(done => { resolve = done; });
  const app = await page({ pending });
  app.events['fleng:session-ended']();
  assert.equal(app.window.redirect, '/login.html');
  resolve(data()); await tick();
  assert.ok(app.target.textContent.includes('Your progress is private'));
  assert.equal(app.target.all('progress').length, 0);
  app.events.pageshow({ persisted: true }); await tick();
  assert.equal(app.sessions(), 2);
  assert.ok(app.target.textContent.includes('Total XP 47'));
  app.events.pagehide();
  assert.equal(app.target.all('progress').length, 0);
});
