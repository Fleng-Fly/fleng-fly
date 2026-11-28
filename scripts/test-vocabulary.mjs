import './require-vm-modules.mjs';
// Behaviour checks with the existing project's dependency-free VM/DOM approach.
// These check state transitions/API writes; they do not verify browser rendering.
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Element {
  constructor(tag = 'div', text = '') {
    this.tagName = tag; this.children = []; this.attributes = {}; this.events = {};
    this.dataset = {}; this.style = { setProperty(name, value) { this[name] = value; } }; this.value = ''; this.hidden = false;
    this.disabled = false; this._text = text;
    this.classList = { add: (name) => { this.className = `${this.className || ''} ${name}`; }, toggle: (name, on) => { const set = new Set((this.className || '').split(' ')); if (on) set.add(name); else set.delete(name); this.className = [...set].join(' '); } };
  }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  setAttribute(name, value) { this.attributes[name] = value; }
  getAttribute(name) { return this.attributes[name]; }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, action) { this.events[name] = action; }
  querySelectorAll(selector) { const tags = selector.split(',').map((s) => s.trim()); return this.children.flatMap((node) => [...(tags.includes(node.tagName) ? [node] : []), ...node.querySelectorAll(selector)]); }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  focus() {} reportValidity() { return true; } reset() {} close() { this.open = false; } showModal() { this.open = true; }
}

const makeWord = (id = 'one', word = 'resilience', translation = 'стійкість') => ({ id, word, translation, example: 'Keep going.', learned: false, dueAt: '2020-01-01T00:00:00Z' });

async function page({ words = [makeWord()], mode = '', level = '', courseWords = [], reviewError = false, groups = [], storage = new Map() } = {}) {
  const nodes = new Map(); const events = {}; const writes = [], attempts = [];
  const modeButtons = ['list', 'mixed'].map((mode) => { const n = new Element('button'); n.dataset.mode = mode; return n; });
  const filters = ['all', 'learning', 'learned', 'due'].map((filter) => { const n = new Element('button'); n.dataset.filter = filter; return n; });
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const query = mode ? '?' + new URLSearchParams({ mode, ...(level ? { level } : {}) }) : '';
  const location = { href: `http://localhost/vocabulary.html${query}`, search: query };
  const document = {
    getElementById: node, createElement: (tag) => new Element(tag),
    createElementNS: (ns, tag) => { const n = new Element(tag); n.namespaceURI = ns; return n; },
    querySelectorAll: (selector) => selector === '[data-mode]' ? modeButtons : selector === '[data-filter]' ? filters : selector.includes('#word-search') ? [...modeButtons, ...filters, node('word-search'), node('add-word')] : [],
  };
  let failReview = reviewError;
  let confirmRemoval = true;
  const levelRequests = [];
  const helpers = {
    listCourseWords: async (_course, offset, limit, level) => {
      levelRequests.push(level);
      return courseWords.slice(offset, offset + limit);
    },
    getVocabularyGroups: async () => { if (groups === null) throw new Error('down'); return { courses: groups }; },
    listVocabulary: async (offset) => words.slice(offset, offset + 100),
    addVocabulary: async (input) => { writes.push({ add: input }); const word = { ...makeWord('added'), ...input }; words.push(word); return word; },
    updateVocabulary: async (id, learned) => { writes.push({ update: id, learned }); const word = words.find((w) => w.id === id); word.learned = learned; return { ...word }; },
    deleteVocabulary: async (id) => { writes.push({ remove: id }); words.splice(words.findIndex((w) => w.id === id), 1); },
    reviewVocabulary: async (id, remembered, attemptId) => { attempts.push(attemptId); writes.push({ review: id, remembered }); if (failReview) throw new Error('Offline'); const word = words.find((w) => w.id === id); word.learned = remembered; word.dueAt = new Date(Date.now() + 86400000).toISOString(); return { ...word }; },
  };
  const sessionStorage = { getItem: (key) => storage.get(key), setItem: (key, value) => storage.set(key, value) };
  const context = vm.createContext({ document, location, history: { replaceState: (_a, _b, url) => { location.href = url.toString(); } }, window: { sessionStorage, addEventListener: (name, action) => { events[name] = action; }, confirm: () => confirmRemoval }, crypto: { randomUUID }, URL, URLSearchParams, console, setTimeout, clearTimeout });
  const modules = new Map();
  function mock(name, values) { const mod = new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context, identifier: name }); modules.set(name, mod); }
  const el = (tag, cls, text) => {
    const n = new Element(tag, text);
    n.className = cls;
    if (tag === 'form') Object.defineProperty(n, 'isConnected', {
      get: () => node('word-practice').querySelectorAll('form').includes(n),
    });
    return n;
  };
  mock('./api.js', helpers); mock('./layout.js', { el });
  mock('./errors.js', { describeApiError: (e) => e.message });
  mock('./i18n.js', i18nStub);
  mock('./session.js', { requireSession: async () => ({ id: 'user', displayName: 'Learner' }) });
  mock('./workspace.js', { mountWorkspace: () => {}, setWorkspaceUser: () => {} });
  const tiles = new vm.SourceTextModule(await readFile('frontend/js/letter-tiles.js', 'utf8'), { context, identifier: './letter-tiles.js' });
  modules.set('./letter-tiles.js', tiles);
  await tiles.link((name) => modules.get(name));
  const autoCheck = new vm.SourceTextModule(await readFile('frontend/js/auto-check.js', 'utf8'), { context, identifier: './auto-check.js' });
  modules.set('./auto-check.js', autoCheck);
  await autoCheck.link((name) => modules.get(name));
  const completion = new vm.SourceTextModule(await readFile('frontend/js/test-completion.js', 'utf8'), { context });
  modules.set('./test-completion.js', completion);
  await completion.link((name) => modules.get(name));
  const main = new vm.SourceTextModule(await readFile('frontend/js/vocabulary.js', 'utf8'), { context });
  await main.link((name) => modules.get(name)); await main.evaluate();
  const flush = async () => { for (let i = 0; i < 10; i++) await Promise.resolve(); };
  await flush();
  const click = async (element) => { assert.ok(element, 'control exists'); if (!element.disabled) await element.events.click?.({ preventDefault() {} }); await flush(); };
  const byText = (id, text) => node(id).querySelectorAll('button').find((n) => n.textContent.includes(text));
  const session = () => JSON.parse(storage.get(level ? `fleng.level-test.v1:user:${level}` : 'fleng.mixed-practice.v1:user'));
  return { node, mode: async (value) => click(modeButtons.find((n) => n.dataset.mode === value)), filter: async (value) => click(filters.find((n) => n.dataset.filter === value)), click, byText, writes, words, attempts, levelRequests, session, flush, fail: (value) => { failReview = value; }, confirmRemoval: (value) => { confirmRemoval = value; } };
}

test('level tests use course words, resume locally and leave personal reviews untouched', async () => {
  const storage = new Map();
  const courseWords = [makeWord('course'), makeWord('duplicate')];
  const options = { mode: 'mixed', level: 'A1', courseWords, storage };
  const app = await page(options);
  assert.deepEqual(app.levelRequests, ['A1']);
  assert.equal(app.node('personal-words-heading').hidden, true);
  assert.deepEqual(app.session().queue, ['course']);
  await app.click(app.byText('word-practice', 'Reveal'));
  await app.click(app.byText('word-practice', 'I need practice'));
  assert.deepEqual(app.session().queue, []);
  assert.deepEqual(app.session().mistakes, ['course']);
  assert.deepEqual(app.writes, []);
  const reloaded = await page(options);
  assert.deepEqual(reloaded.session().mistakes, ['course']);
  assert.deepEqual(reloaded.writes, []);
});

test('loads every vocabulary page, searches translation and filters learned words', async () => {
  const words = Array.from({ length: 101 }, (_, i) => makeWord(String(i), 'word' + i, 'переклад' + i));
  words[100].learned = true;
  const app = await page({ words });
  assert.match(app.node('word-count').textContent, /101 words/);
  app.node('word-search').value = 'переклад100'; app.node('word-search').events.input();
  assert.match(app.node('word-count').textContent, /1 word/);
  await app.filter('learning'); assert.match(app.node('word-count').textContent, /0 words/);
  await app.filter('learned'); assert.match(app.node('word-list').textContent, /word100/);
});

test('adds a word through the API and shows it in the collection', async () => {
  const app = await page({ words: [] });
  await app.click(app.node('add-word')); assert.equal(app.node('word-dialog').open, true);
  app.node('new-word').value = '  hello  '; app.node('new-translation').value = 'привіт';
  await app.node('word-form').events.submit({ preventDefault() {} });
  assert.equal(app.writes[0].add.word, 'hello');
  assert.match(app.node('word-list').textContent, /hello/);
  assert.equal(app.node('word-dialog').open, false);
});

test('removes a word from My Words only after confirmation', async () => {
  const app = await page({ words: [makeWord('1', 'alpha', 'один'), makeWord('2', 'beta', 'два')] });
  app.confirmRemoval(false);
  await app.click(app.byText('word-list', 'Remove'));
  assert.equal(app.writes.length, 0);
  app.confirmRemoval(true);
  await app.click(app.byText('word-list', 'Remove'));
  assert.deepEqual(app.writes, [{ remove: '1' }]);
  assert.doesNotMatch(app.node('word-list').textContent, /alpha/);
  assert.match(app.node('word-list').textContent, /beta/);
  assert.match(app.node('word-count').textContent, /1 word/);
});


const practiceWords = () => ['train', 'plant', 'stone', 'crown', 'place', 'share', 'flame', 'fruit']
  .map((word, i) => makeWord(String(i), word, 'translation ' + i));

async function answer(app, remembered, pause = false) {
  const session = app.session();
  const id = session.queue[0];
  const { type } = session.tasks.find(({ wordId }) => wordId === id);
  const word = app.words.find((item) => item.id === id);
  const target = app.node('word-practice');
  if (type === 'flashcards') {
    await app.click(app.byText('word-practice', 'Reveal translation'));
    await app.click(app.byText('word-practice', remembered ? 'I knew it' : 'I need practice'));
  } else if (type === 'choice') {
    const option = target.querySelectorAll('button').find((button) => button.className === 'word-choice'
      && (button.textContent === word.translation) === remembered);
    await app.click(option);
  } else if (type === 'write') {
    const input = target.querySelector('input');
    const form = target.querySelector('form');
    input.value = remembered ? `  ${word.word.toUpperCase()}  ` : 'wrong';
    input.events.input();
    if (pause) await new Promise((resolve) => setTimeout(resolve, 1600));
    else {
      form.events.submit({ preventDefault() {} });
      form.events.submit({ preventDefault() {} });
    }
    await app.flush();
  } else {
    const letters = [...word.word].filter((_, index) => index % 3 !== 0);
    if (!remembered) [letters[0], letters[1]] = [letters[1], letters[0]];
    const buttons = target.querySelectorAll('button');
    const slots = buttons.filter((button) => button.className?.includes('lesson-tile-slot'));
    for (const [index, letter] of letters.entries()) {
      await app.click(buttons.find((button) => !button.hidden && button.textContent === letter));
      await app.click(slots[index]);
    }
  }
}

test('Mixed Practice balances formats and never requeues wrong answers', async () => {
  const words = practiceWords();
  const storage = new Map();
  let app = await page({ words, storage });
  await app.mode('mixed');
  const initial = app.session();
  for (const type of ['flashcards', 'choice', 'write', 'letters']) {
    assert.equal(initial.tasks.filter((task) => task.type === type).length, 2);
  }
  for (const [index, id] of initial.queue.entries()) {
    assert.equal(app.session().queue[0], id);
    if (index === 2) await app.click(app.byText('word-practice', 'Skip'));
    else await answer(app, false);
    assert.deepEqual(app.session().queue, initial.queue.slice(index + 1));
    if (index === 3) app = await page({ words, storage, mode: 'mixed' });
  }
  assert.match(app.node('word-practice').textContent, /First-try accuracy 0%/);
  assert.match(app.node('word-practice').textContent, /Incorrect 7 Skipped 1/);
  await app.click(app.byText('word-practice', 'Retry Mistakes'));
  assert.equal(app.session().queue.length, 7);
});

test('one word uses reveal and self-assessment, repeats errors, and replays even when no longer due', async () => {
  const app = await page();
  await app.filter('due');
  await app.mode('mixed');
  const flip = app.node('word-practice').querySelectorAll('button').find((n) => n.className === 'flashcard-turn');
  assert.equal(flip.attributes['aria-pressed'], 'false');
  await app.click(flip);
  assert.equal(flip.attributes['aria-pressed'], 'true');
  assert.ok(app.byText('word-practice', 'I knew it'));
  await app.click(flip);
  assert.equal(app.byText('word-practice', 'I knew it'), undefined);
  assert.equal(app.writes.length, 0);
  await answer(app, false);
  assert.deepEqual(app.session().queue, []);
  await app.click(app.byText('word-practice', 'Retry Mistakes'));
  assert.deepEqual(app.session().queue, ['one']);
  await answer(app, true);
  assert.match(app.node('word-practice').textContent, /Perfect Score/);
  assert.match(app.node('word-practice').textContent, /Mistakes from earlier rounds.*Your answer: I need practice/);
});

test('empty practice does not call the review API', async () => {
  const app = await page({ words: [] });
  await app.mode('mixed');
  assert.match(app.node('word-practice').textContent, /No words for this activity/);
  assert.equal(app.writes.length, 0);
});

test('phrases with identical translations balance the compatible formats', async () => {
  const words = ['get back', 'come back', 'go back', 'turn back', 'head back']
    .map((word, index) => makeWord(String(index), word, 'повернутися'));
  const app = await page({ words, mode: 'mixed' });
  const types = app.session().tasks.map((task) => task.type);
  assert.ok(types.every((type) => ['flashcards', 'write'].includes(type)));
  assert.ok(Math.abs(types.filter((type) => type === 'flashcards').length
    - types.filter((type) => type === 'write').length) <= 1);
});

test('an unsaved review remains pending and reload retries the same attempt ID', async () => {
  const storage = new Map();
  const app = await page({ mode: 'flashcards', reviewError: true, storage });
  await answer(app, true);
  assert.match(app.node('word-practice').textContent, /not saved/);
  assert.equal(app.words[0].learned, false);
  const attemptId = app.session().pending.attemptId;
  const restored = await page({ words: app.words, mode: 'mixed', storage });
  assert.deepEqual(restored.attempts, [attemptId]);
  assert.deepEqual(restored.session().queue, []);
  assert.match(restored.node('word-practice').textContent, /Perfect Score/);
});

test('filters the dictionary by course and lesson and shows where each word came from', async () => {
  const words = [
    { ...makeWord('a', 'cat', 'кіт'), courseId: 'c1', courseTitle: 'A1', lessonId: 'l1', lessonTitle: 'Pets', lessonSlug: 'pets', source: 'lesson', pronunciation: '/kæt/' },
    { ...makeWord('b', 'ocean', 'океан'), courseId: 'c2', courseTitle: 'B1', lessonId: 'l2', lessonTitle: 'Travel', lessonSlug: 'travel', source: 'lesson' },
    { ...makeWord('c', 'mine', 'мій'), source: 'manual' },
  ];
  const groups = [
    { id: 'c1', title: 'A1', lessons: [{ id: 'l1', title: 'Pets' }] },
    { id: 'c2', title: 'B1', lessons: [{ id: 'l2', title: 'Travel' }] },
  ];
  const app = await page({ words, groups });
  assert.match(app.node('word-count').textContent, /3 words/);
  assert.equal(app.node('word-course').children.length, 3);
  assert.equal(app.node('word-lesson').disabled, true);
  app.node('word-course').value = 'c2';
  app.node('word-course').events.change();
  assert.match(app.node('word-count').textContent, /1 word/);
  assert.match(app.node('word-list').textContent, /ocean/);
  assert.equal(app.node('word-lesson').disabled, false);
  app.node('word-lesson').value = 'l2';
  app.node('word-lesson').events.change();
  assert.match(app.node('word-list').textContent, /B1 · Travel/);
  app.node('word-course').value = '';
  app.node('word-course').events.change();
  assert.equal(app.node('word-lesson').value, '');
  assert.match(app.node('word-count').textContent, /3 words/);
  assert.match(app.node('word-list').textContent, /\/kæt\//);
  const details = app.node('word-list').querySelectorAll('button').find((n) => n.className === 'word-details-toggle');
  assert.equal(details.attributes['aria-expanded'], 'false');
  await app.click(details);
  const opened = app.node('word-list').querySelectorAll('button').find((n) => n.className === 'word-details-toggle');
  assert.equal(opened.attributes['aria-expanded'], 'true');
  assert.match(app.node('word-list').textContent, /Keep going\./);
});

test('new learners see how words arrive and a way to the courses', async () => {
  const app = await page({ words: [] });
  assert.match(app.node('word-list').textContent, /Finish a lesson/);
  assert.equal(app.node('word-course').disabled, true);
});

test('the dictionary still loads when course groups are unavailable', async () => {
  const words = [{ ...makeWord('a', 'cat', 'кіт'), courseId: 'c1', courseTitle: 'A1', lessonId: 'l1', lessonTitle: 'Pets' }];
  const app = await page({ words, groups: null });
  assert.match(app.node('word-count').textContent, /1 word/);
  assert.equal(app.node('word-course').children.length, 2);
});
