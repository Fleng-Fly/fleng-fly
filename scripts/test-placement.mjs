import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';
import en from '../frontend/js/i18n/en.js';
import uk from '../frontend/js/i18n/uk.js';

class Element {
  constructor(tag = 'div', text = '') { this.tag = tag; this.text = text; this.children = []; this.events = {}; this.dataset = {}; this.disabled = false; this.hidden = false; this.value = ''; this.style = { setProperty() {} }; }
  set innerHTML(_) { throw new Error('Raw HTML is forbidden'); }
  set textContent(value) { this.text = value; this.children = []; }
  get textContent() { return this.text + this.children.map((node) => node.textContent).join(' '); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.text = ''; this.children = nodes; }
  addEventListener(name, fn) { this.events[name] = fn; }
  setAttribute() {}
  querySelectorAll(selector) { return this.children.flatMap((node) => [...(node.tag === selector ? [node] : []), ...node.querySelectorAll(selector)]); }
  querySelector(selector) { return this.querySelectorAll('input').find((node) => selector === 'input:checked' && node.checked); }
  focus() { this.focused = true; }
}
const copy = (value) => JSON.parse(JSON.stringify(value));
const questions = [1, 2].map((n) => ({ id: `q${n}`, prompt: `Question ${n} <img onerror=bad>`, level: 'A1', options: [{ id: 'a', text: 'First' }, { id: 'b', text: 'Second' }] }));
const fresh = (id) => ({ id, questions, status: 'in_progress', total: 2, answered: 0, answers: {}, result: null, recommendedCourses: [], startedAt: '2026-11-16T12:00:00Z' });

async function page({ resume = false, unavailable = false, history: rows = null, lang = 'en' } = {}) {
  const nodes = new Map(), calls = [], urls = [], workspace = [];
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const levels = ['A1', 'A2', 'B1', 'B2'].map((level) => { const card = new Element('li'); card.dataset = { level }; card.names = new Set(); card.classList = { toggle: (name, on) => (on ? card.names.add(name) : card.names.delete(name)) }; card.querySelector = () => null; card.prepend = (...nodes) => card.children.unshift(...nodes); return card; });
  let stored = resume ? fresh('resume-id') : null, failSave = false;
  if (stored) { stored.answers.q1 = 'b'; stored.answered = 1; }
  const api = {
    startPlacement: async () => { calls.push('start'); stored = fresh('new-id'); return copy(stored); },
    listPlacements: async () => { calls.push('history'); return rows ?? (stored ? [copy(stored)] : []); },
    getPlacement: async (id) => { calls.push(['get', id]); return copy(stored); },
    savePlacementAnswer: async (id, questionId, optionId) => {
      calls.push(['save', id, questionId, optionId]);
      if (failSave) throw new Error('Offline');
      stored.answers[questionId] = optionId; stored.answered = Object.keys(stored.answers).length;
      return copy(stored);
    },
    retryPlacementMistakes: async () => { throw new Error("Not used by this fixture"); },
    completePlacement: async () => {
      calls.push('complete'); assert.equal(stored.answered, 2);
      stored.status = 'completed';
      stored.result = { label: 'Approximate A1', estimatedLevel: 'A1', correct: 1, total: 2, assessmentRange: 'A1–B2', limitations: ['Not certified', en['pt.limit.1']], bands: [{ level: 'A1', correct: 1, total: 2 }], review: questions.map((q) => ({ questionId: q.id, selectedOptionId: stored.answers[q.id], correctOptionId: 'a', isCorrect: stored.answers[q.id] === 'a', explanation: 'Explanation after completion', explanationUk: 'Пояснення після завершення' })) };
      stored.recommendationNote = 'Published A1 courses'; stored.recommendedCourses = [{ level: 'A1', title: 'Real course', slug: 'real-course' }];
      return copy(stored);
    },
  };
  const context = vm.createContext({ document: { getElementById: node, querySelectorAll: (selector) => selector === '#placement-levels li' ? levels : [] }, URL, URLSearchParams,
    location: { href: `https://fleng.test/placement-test.html${resume ? '?attempt=resume-id' : ''}`, search: resume ? '?attempt=resume-id' : '' },
    history: { replaceState: (_a, _b, url) => urls.push(String(url)) },
  });
  const module = new vm.SourceTextModule(await readFile('frontend/js/placement-test.js', 'utf8'), { context });
  const imports = new Map();
  const i18n = lang === 'uk' ? {
    ...i18nStub, getLang: () => lang,
    t: (key, params) => (uk[key] ?? key).replace(/\{(\w+)\}/g, (match, name) => params?.[name] ?? match),
  } : i18nStub;
  const link = (name) => {
    if (imports.has(name)) return imports.get(name);
    const values = name === './placement-api.js' ? api
      : name === './layout.js' ? { el: (tag, cls, text) => { const n = new Element(tag, text || ''); n.className = cls; return n; } }
      : name === './workspace.js' ? { mountWorkspace: (active) => { workspace.push(active); }, setWorkspaceUser() {} }
      : name === './i18n.js' ? i18n
      : name === './i18n/en.js' ? { default: en }
      : name === './session.js' ? { requireSession: async () => { if (unavailable) throw new Error('Backend unavailable'); return { id: 'user' }; } }
      : { describeApiError: (error) => error.message };
    const dependency = new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
    imports.set(name, dependency);
    return dependency;
  };
  const completion = new vm.SourceTextModule(await readFile('frontend/js/test-completion.js', 'utf8'), { context });
  imports.set('./test-completion.js', completion);
  await completion.link(link);
  const copyModule = new vm.SourceTextModule(await readFile('frontend/js/placement-copy.js', 'utf8'), { context });
  await copyModule.link(link);
  imports.set('./placement-copy.js', copyModule);
  await module.link(link);
  await module.evaluate();
  const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
  await flush();
  const click = async (id) => { await node(id).events.click?.(); await flush(); };
  const choose = async (option = 0) => { const inputs = node('placement-question').querySelectorAll('input'); await inputs[option].events.change(); await flush(); };
  return { node, calls, urls, workspace, levels, click, choose, fail: (on) => { failSave = on; }, submit: async () => { await node('placement-form').events.submit({ preventDefault() {} }); await flush(); } };
}

test('start, autosave, server result, review and retake use only placement endpoints', async () => {
  const app = await page();
  await app.click('placement-start');
  assert.match(app.urls.at(-1), /attempt=new-id/);
  assert.equal(app.node('placement-skip').disabled, false);
  assert.doesNotMatch(app.node('placement-question').textContent, /Explanation/);
  assert.match(app.node('placement-question').textContent, /<img onerror=bad>/);
  await app.choose();
  assert.match(app.node('placement-saved').textContent, /1 of 2/);
  await app.choose(1);
  assert.equal(app.node('placement-player').hidden, true);
  assert.equal(app.node('placement-result').hidden, false);
  assert.match(app.node('placement-result').textContent, /Not certified/);
  assert.match(app.node('placement-result').textContent, /Explanation after completion/);
  assert.equal(app.node('placement-result').querySelectorAll('a')[0].href, '/course.html?slug=real-course');
  await app.click('placement-start');
  assert.equal(app.node('placement-result').hidden, true);
  assert.equal(app.node('placement-skip').disabled, false);
  assert.equal(app.calls.filter((call) => call === 'start').length, 2);
  assert.equal(app.calls.filter((call) => call === 'complete').length, 1);
});

test('URL resume loads saved choices without starting a new attempt', async () => {
  const app = await page({ resume: true });
  assert.equal(app.calls.includes('start'), false);
  assert.equal(app.node('placement-question').querySelectorAll('input')[1].checked, false);
  assert.match(app.node('placement-count').textContent, /Question 2/);
});

test('Ukrainian instructions and results preserve English tasks and keep explanations out of the question', async () => {
  const app = await page({ lang: 'uk' });
  await app.click('placement-start');
  const question = app.node('placement-question').textContent;
  assert.ok(question.includes(uk['pt.instruction']));
  assert.match(question, /Question 1.*First.*Second/);
  assert.doesNotMatch(question, /Пояснення|Explanation/);
  await app.choose();
  await app.choose(1);
  const result = app.node('placement-result').textContent;
  assert.ok(result.includes(uk['pt.limit.1']));
  assert.ok(result.includes(uk['pt.result.estimated'].replace('{level}', 'A1')));
  assert.match(result, /Пояснення після завершення/);
});

test('failed save offers recovery without grading or advancing; session errors stay visible', async () => {
  const app = await page(); await app.click('placement-start'); app.fail(true);
  await app.choose();
  assert.equal(app.node('placement-error').hidden, false);
  assert.match(app.node('placement-error-text').textContent, /Offline/);
  assert.match(app.node('placement-count').textContent, /Question 1/);
  assert.equal(app.calls.includes('complete'), false);
  assert.equal(app.node('placement-skip').disabled, false);
  app.fail(false); await app.click('placement-retry');
  assert.equal(app.node('placement-error').hidden, true);
  const offline = await page({ unavailable: true });
  assert.match(offline.node('placement-error-text').textContent, /Backend unavailable/);
  assert.equal(offline.calls.length, 0);
});

test('the page lives in the Courses area and shows the intro only while not answering', async () => {
  const app = await page();
  assert.deepEqual(app.workspace, ['placement']);
  assert.equal(app.node('placement-intro').hidden, false);
  await app.click('placement-start');
  assert.equal(app.node('placement-intro').hidden, true);
  assert.equal(app.node('placement-levels').hidden, true);
  await app.choose(); await app.choose(1);
  assert.equal(app.node('placement-intro').hidden, false);
  assert.equal(app.node('placement-levels').hidden, false);
});

test('history rows show level, date, score and a results link; the newest completed level is current', async () => {
  const done = (id, level, correct, startedAt) => ({ id, status: 'completed', startedAt, answered: 36, total: 36, estimatedLevel: level, resultLabel: `Approximate ${level}`, correct });
  const app = await page({ history: [
    done('new', 'B1', 25, '2026-11-18T10:00:00Z'),
    done('old', 'A2', 14, '2026-11-01T10:00:00Z'),
    { id: 'open', status: 'in_progress', startedAt: '2026-10-20T10:00:00Z', answered: 5, total: 36, estimatedLevel: null, resultLabel: null, correct: null },
  ] });
  const rows = app.node('placement-history-list').children;
  assert.equal(rows.length, 3);
  const text = (row) => row.children.map((child) => child.textContent);
  assert.deepEqual([text(rows[0])[0], text(rows[0])[2], text(rows[0])[3]], ['B1', '25 / 36', 'View results']);
  assert.match(text(rows[0])[1], /2026/);
  assert.equal(text(rows[1])[0], 'A2');
  assert.equal(text(rows[2])[0], '…');
  assert.match(text(rows[2])[3], /Resume · 5\/36/);
  // Only the latest completed estimate is marked as the current level.
  const current = app.levels.filter((card) => card.names.has('is-current')).map((card) => card.dataset.level);
  assert.deepEqual(current, ['B1']);
  // "View results" opens that very attempt through the existing API.
  await rows[1].children[3].events.click(); await Promise.resolve();
  assert.deepEqual(app.calls.find((call) => Array.isArray(call)), ['get', 'old']);
});

test('no completed attempt means no level is marked current', async () => {
  const app = await page({ history: [] });
  assert.equal(app.levels.some((card) => card.names.has('is-current')), false);
  assert.match(app.node('placement-history-status').textContent, /No attempts yet/);
});
