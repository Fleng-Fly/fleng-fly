import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Element {
  constructor(tag = 'div', text = '') { this.tag = tag; this.text = text; this.children = []; this.events = {}; this.disabled = false; this.hidden = false; this.value = ''; }
  set innerHTML(_) { throw new Error('Raw HTML is forbidden'); }
  set textContent(value) { this.text = value; this.children = []; }
  get textContent() { return this.text + this.children.map((node) => node.textContent).join(' '); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.text = ''; this.children = nodes; }
  addEventListener(name, fn) { this.events[name] = fn; }
  querySelectorAll(selector) { return this.children.flatMap((node) => [...(node.tag === selector ? [node] : []), ...node.querySelectorAll(selector)]); }
  querySelector(selector) { return this.querySelectorAll('input').find((node) => selector === 'input:checked' && node.checked); }
  focus() { this.focused = true; }
}
const copy = (value) => JSON.parse(JSON.stringify(value));
const questions = [1, 2].map((n) => ({ id: `q${n}`, prompt: `Question ${n} <img onerror=bad>`, level: 'A1', options: [{ id: 'a', text: 'First' }, { id: 'b', text: 'Second' }] }));
const fresh = (id) => ({ id, questions, status: 'in_progress', total: 2, answered: 0, answers: {}, result: null, recommendedCourses: [], startedAt: '2026-11-16T12:00:00Z' });

async function page({ resume = false, unavailable = false } = {}) {
  const nodes = new Map(), calls = [], urls = [];
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  let stored = resume ? fresh('resume-id') : null, failSave = false;
  if (stored) { stored.answers.q1 = 'b'; stored.answered = 1; }
  const api = {
    startPlacement: async () => { calls.push('start'); stored = fresh('new-id'); return copy(stored); },
    listPlacements: async () => { calls.push('history'); return stored ? [copy(stored)] : []; },
    getPlacement: async (id) => { calls.push(['get', id]); return copy(stored); },
    savePlacementAnswer: async (id, questionId, optionId) => {
      calls.push(['save', id, questionId, optionId]);
      if (failSave) throw new Error('Offline');
      stored.answers[questionId] = optionId; stored.answered = Object.keys(stored.answers).length;
      return copy(stored);
    },
    completePlacement: async () => {
      calls.push('complete'); assert.equal(stored.answered, 2);
      stored.status = 'completed';
      stored.result = { label: 'Approximate A1', correct: 1, total: 2, assessmentRange: 'A1–B2', limitations: ['Not certified'], bands: [{ level: 'A1', correct: 1, total: 2 }], review: questions.map((q) => ({ questionId: q.id, selectedOptionId: stored.answers[q.id], correctOptionId: 'a', isCorrect: stored.answers[q.id] === 'a', explanation: 'Explanation after completion' })) };
      stored.recommendationNote = 'Published A1 courses'; stored.recommendedCourses = [{ level: 'A1', title: 'Real course', slug: 'real-course' }];
      return copy(stored);
    },
  };
  const context = vm.createContext({ document: { getElementById: node }, URL, URLSearchParams,
    location: { href: `https://fleng.test/placement-test.html${resume ? '?attempt=resume-id' : ''}`, search: resume ? '?attempt=resume-id' : '' },
    history: { replaceState: (_a, _b, url) => urls.push(String(url)) },
  });
  const module = new vm.SourceTextModule(await readFile('frontend/js/placement-test.js', 'utf8'), { context });
  await module.link((name) => {
    const values = name === './placement-api.js' ? api
      : name === './layout.js' ? { el: (tag, cls, text) => new Element(tag, text || ''), mountHeader() {} }
      : name === './i18n.js' ? i18nStub
      : name === './session.js' ? { requireSession: async () => { if (unavailable) throw new Error('Backend unavailable'); return { id: 'user' }; } }
      : { describeApiError: (error) => error.message };
    return new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
  await flush();
  const click = async (id) => { await node(id).events.click?.(); await flush(); };
  const choose = async (option = 0) => { const inputs = node('placement-question').querySelectorAll('input'); await inputs[option].events.change(); await flush(); };
  return { node, calls, urls, click, choose, fail: (on) => { failSave = on; }, submit: async () => { await node('placement-form').events.submit({ preventDefault() {} }); await flush(); } };
}

test('start, autosave, server result, review and retake use only placement endpoints', async () => {
  const app = await page();
  await app.click('placement-start');
  assert.match(app.urls.at(-1), /attempt=new-id/);
  assert.equal(app.node('placement-finish').disabled, true);
  assert.doesNotMatch(app.node('placement-question').textContent, /Explanation/);
  assert.match(app.node('placement-question').textContent, /<img onerror=bad>/);
  await app.choose();
  assert.match(app.node('placement-saved').textContent, /1 of 2/);
  await app.click('placement-next'); await app.choose(1);
  assert.equal(app.node('placement-finish').disabled, false);
  await app.submit();
  assert.equal(app.node('placement-player').hidden, true);
  assert.equal(app.node('placement-result').hidden, false);
  assert.match(app.node('placement-result').textContent, /Not certified/);
  assert.match(app.node('placement-result').textContent, /Explanation after completion/);
  assert.equal(app.node('placement-result').querySelectorAll('a')[0].href, '/course.html?slug=real-course');
  await app.click('placement-start');
  assert.equal(app.node('placement-result').hidden, true);
  assert.equal(app.node('placement-finish').disabled, true);
  assert.equal(app.calls.filter((call) => call === 'start').length, 2);
  assert.equal(app.calls.filter((call) => call === 'complete').length, 1);
});

test('URL resume loads saved choices without starting a new attempt', async () => {
  const app = await page({ resume: true });
  assert.equal(app.calls.includes('start'), false);
  assert.equal(app.node('placement-question').querySelectorAll('input')[1].checked, true);
  await app.click('placement-unanswered');
  assert.match(app.node('placement-count').textContent, /Question 2/);
});

test('failed save offers recovery without grading or advancing; session errors stay visible', async () => {
  const app = await page(); await app.click('placement-start'); app.fail(true);
  await app.choose();
  assert.equal(app.node('placement-error').hidden, false);
  assert.match(app.node('placement-error-text').textContent, /Offline/);
  assert.match(app.node('placement-count').textContent, /Question 1/);
  assert.equal(app.calls.includes('complete'), false);
  assert.equal(app.node('placement-finish').disabled, true);
  app.fail(false); await app.click('placement-retry');
  assert.equal(app.node('placement-error').hidden, true);
  const offline = await page({ unavailable: true });
  assert.match(offline.node('placement-error-text').textContent, /Backend unavailable/);
  assert.equal(offline.calls.length, 0);
});
