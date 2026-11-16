// State/API checks for the new course-library → cards → test flow.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

class Element {
  constructor(tag = 'div', text = '') {
    this.tagName = tag; this.children = []; this.attributes = {}; this.events = {}; this.dataset = {}; this.style = {}; this.value = ''; this.hidden = false; this.disabled = false; this._text = text; this.className = '';
    const names = () => new Set(this.className.split(' ').filter(Boolean));
    this.classList = { contains: (name) => names().has(name), add: (name) => { const set = names(); set.add(name); this.className = [...set].join(' '); }, toggle: (name, on = !names().has(name)) => { const set = names(); if (on) set.add(name); else set.delete(name); this.className = [...set].join(' '); } };
  }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map((node) => node.textContent).join(' '); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this._text = ''; this.children = nodes; }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(name, action) { this.events[name] = action; }
  querySelectorAll(selector) {
    const match = (node) => selector.split(',').some((part) => { const s = part.trim(); return s.startsWith('.') ? node.className.split(' ').includes(s.slice(1)) : node.tagName === s; });
    return this.children.flatMap((node) => [...(match(node) ? [node] : []), ...node.querySelectorAll(selector)]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  focus() {} reportValidity() { return true; }
  async click() { if (!this.disabled) return this.events.click?.({ preventDefault() {} }); }
}
const cards = [{ wordId: 'one', word: 'hello', translation: 'привіт', example: 'Hello there.' }, { wordId: 'two', word: 'bye', translation: 'бувай', example: 'Bye for now.' }];
async function runtime(file, { source = 'course_words', failComplete = false, failReview = false, mode = 'write' } = {}) {
  const nodes = new Map(); const calls = []; const flags = { failComplete, failReview };
  let session = { sessionId: 'session', source, cards, total: cards.length, status: 'active', testReady: false };
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  for (const id of ['library-limit', 'study-limit']) node(id).value = '10';
  for (const id of ['library-mode', 'study-mode']) node(id).value = 'choice';
  node('library-sort').value = 'az';
  const levels = ['', 'A0', 'A1', 'B2'].map((level) => { const n = new Element('button'); n.dataset.level = level; return n; });
  const location = { search: file === 'practice' ? `?session=session&mode=${mode}` : '', href: `http://localhost/${file}.html${file === 'practice' ? `?session=session&mode=${mode}` : ''}`, assign(value) { this.assigned = value; }, replace(value) { this.assigned = value; } };
  const document = { body: new Element('body'), getElementById: node, createElement: (tag) => new Element(tag), addEventListener() {}, querySelectorAll: (selector) => selector === '[data-level]' ? levels : [] };
  const context = vm.createContext({ document, location, history: { replaceState: (_a, _b, value) => { location.href = String(value); } }, window: { addEventListener() {} }, URL, URLSearchParams, console, setTimeout, clearTimeout });
  const api = {
    listCourses: async () => [{ id: 'course', level: 'A1', title: 'First course' }],
    listCourseWords: async ({ offset }) => offset ? [] : cards.map((card) => ({ id: card.wordId, courseId: 'course', ...card })),
    listVocabulary: async () => [], addVocabulary: async (input) => { calls.push({ add: input }); return { id: 'saved', ...input }; },
    createFlashcardSession: async (input) => { calls.push({ create: input }); return session; },
    getFlashcardSession: async () => session,
    completeFlashcardSession: async () => { calls.push({ complete: true }); if (flags.failComplete) throw new Error('Offline'); session = { ...session, testReady: true, status: 'completed' }; return session; },
    getFlashcardTestWords: async () => { assert.equal(session.testReady, true); calls.push({ handoff: true }); return session; },
    reviewVocabulary: async (id, remembered) => { calls.push({ review: id, remembered }); if (flags.failReview) throw new Error('Offline'); return {}; },
  };
  const modules = new Map();
  const mock = (name, values) => modules.set(name, new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context, identifier: name }));
  mock('./api.js', api); mock('./layout.js', { el: (tag, cls, text) => { const n = new Element(tag, text); n.className = cls || ''; return n; } });
  mock('./session.js', { requireSession: async () => ({ id: 'learner', displayName: 'Learner' }) }); mock('./errors.js', { describeApiError: (error) => error.message });
  mock('./workspace.js', { mountWorkspace() {}, setWorkspaceUser() {} });
  async function resolve(name) {
    if (modules.has(name)) return modules.get(name);
    const module = new vm.SourceTextModule(await readFile(`frontend/js/${name.slice(2)}`, 'utf8'), { context, identifier: name }); modules.set(name, module); await module.link(resolve); return module;
  }
  const main = await resolve(`./${file}.js`); await main.evaluate();
  const flush = async () => { for (let i = 0; i < 50; i++) await Promise.resolve(); }; await flush();
  const click = async (element) => { assert.ok(element, 'control exists'); await element.click(); await flush(); };
  const find = (text) => node('study-stage-content').querySelectorAll('button').find((b) => b.textContent.includes(text));
  return { node, calls, flags, click, find, levels, location, flush };
}

async function finishCards(app) {
  for (let i = 0; i < cards.length; i++) {
    await app.click(app.node('study-stage-content').querySelector('.flashcard-turn'));
    await app.click(app.find(i === cards.length - 1 ? 'Test my memory' : 'Next word'));
  }
}
test('course library combines filters, selects exact words and creates only on explicit start', async () => {
  const app = await runtime('course-words');
  assert.equal(app.node('library-total').textContent, '2'); assert.equal(app.calls.length, 0);
  app.node('library-search').value = 'привіт'; app.node('library-search').events.input();
  assert.match(app.node('library-visible-count').textContent, /1 word/);
  await app.click(app.node('library-select')); assert.equal(app.node('library-selected-count').textContent, '1');
  await app.node('library-start-form').events.submit({ preventDefault() {} }); await app.flush();
  assert.equal(app.calls[0].create.source, 'course_words'); assert.equal(app.calls[0].create.limit, 1);
  assert.deepEqual([...app.calls[0].create.wordIds], ['one']); assert.match(app.location.assigned, /session=session/);
  await app.click(app.levels.find((n) => n.dataset.level === 'B2'));
  assert.match(app.node('library-words').textContent, /different course/);
});
test('course word save uses the existing personal-vocabulary API', async () => {
  const app = await runtime('course-words');
  await app.click(app.node('library-words').querySelectorAll('button').find((n) => n.textContent.includes('Save')));
  assert.equal(app.calls[0].add.word, 'bye'); assert.match(app.node('library-feedback').textContent, /My Words/);
});
test('card reveals gate navigation; completion failure remains retryable before the test', async () => {
  const app = await runtime('practice', { failComplete: true });
  assert.equal(app.find('Next word').disabled, true);
  await finishCards(app);
  assert.match(app.node('study-error-text').textContent, /Offline/); assert.equal(app.calls.some((c) => c.handoff), false);
  assert.ok(app.node('study-stage-content').querySelector('.flashcard-turn'));
  app.flags.failComplete = false; await app.click(app.find('Test my memory'));
  assert.ok(app.calls.find((c) => c.handoff)); assert.ok(app.node('study-stage-content').querySelector('form'));
});
test('course test summary reflects actual answers and repeats only mistakes without personal writes', async () => {
  const app = await runtime('practice'); await finishCards(app);
  const stage = app.node('study-stage-content');
  stage.querySelector('input').value = ' WRONG '; await stage.querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  await app.click(app.find('Next word'));
  stage.querySelector('input').value = ' BYE '; await stage.querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  await app.click(app.find('See my results'));
  assert.match(stage.textContent, /50%/); assert.match(stage.textContent, /result for this run/);
  assert.equal(app.calls.some((c) => c.review), false);
  await app.click(app.find('Repeat mistakes')); assert.match(stage.textContent, /0 \/ 1/); assert.match(stage.textContent, /привіт/);
});
test('failed personal review never counts an answer and can be retried', async () => {
  const app = await runtime('practice', { source: 'my_words', failReview: true }); await finishCards(app);
  const stage = app.node('study-stage-content'); stage.querySelector('input').value = 'hello';
  await stage.querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.match(stage.textContent, /Review not saved/); assert.equal(app.find('Next word'), undefined);
  app.flags.failReview = false; await stage.querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.ok(app.find('Next word')); assert.equal(app.calls.filter((c) => c.review).length, 2);
});

test('answer normalization, letter eligibility and summary metrics handle edge cases', async () => {
  const context = vm.createContext({});
  const module = new vm.SourceTextModule(await readFile('frontend/js/practice-utils.js', 'utf8'), { context }); await module.link(() => {}); await module.evaluate();
  const rules = module.namespace;
  assert.equal(rules.normalizeAnswer('  HELLO   THERE '), 'hello there');
  assert.equal(rules.testCards([{ word: 'hello there' }, { word: 'a' }, { word: 'be' }], 'letters').length, 1);
  assert.equal(rules.translationChoices(cards[0], [...cards, { translation: ' ПРИВІТ ' }]).length, 2);
  assert.equal(rules.sessionMetrics([], 100, 0).accuracy, 0);
  assert.equal(rules.sessionMetrics([{ correct: false }, { correct: true }], 0, 61000).time, '1:01');
});

// Selecting a choice must never save a review until Check Answer is pressed.
test('reference choice tray requires explicit grading and keeps selection accessible', async () => {
  const app = await runtime('practice', { source: 'my_words', mode: 'choice' }); await finishCards(app);
  const stage = app.node('study-stage-content');
  assert.equal(app.find('Check Answer').disabled, true);
  const choice = stage.querySelectorAll('.word-choice').find((node) => node.textContent === 'привіт');
  await app.click(choice);
  assert.equal(choice.attributes['aria-pressed'], 'true');
  assert.equal(app.calls.some((call) => call.review), false);
  await app.click(app.find('Check Answer'));
  assert.equal(app.calls.find((call) => call.review).remembered, true);
  assert.ok(app.find('Next word'));
});
