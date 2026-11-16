// Behaviour checks with the existing project's dependency-free VM/DOM approach.
// These check state transitions/API writes; they do not verify browser rendering.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

class Element {
  constructor(tag = 'div', text = '') {
    this.tagName = tag; this.children = []; this.attributes = {}; this.events = {};
    this.dataset = {}; this.style = {}; this.value = ''; this.hidden = false;
    this.disabled = false; this._text = text;
    this.classList = { add: (name) => { this.className = `${this.className || ''} ${name}`; }, toggle: (name, on) => { const set = new Set((this.className || '').split(' ')); if (on) set.add(name); else set.delete(name); this.className = [...set].join(' '); } };
  }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, action) { this.events[name] = action; }
  querySelectorAll(selector) { const tags = selector.split(',').map((s) => s.trim()); return this.children.flatMap((node) => [...(tags.includes(node.tagName) ? [node] : []), ...node.querySelectorAll(selector)]); }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  focus() {} reportValidity() { return true; } reset() {} close() { this.open = false; } showModal() { this.open = true; }
}

const makeWord = (id = 'one', word = 'resilience', translation = 'стійкість') => ({ id, word, translation, example: 'Keep going.', learned: false, dueAt: '2020-01-01T00:00:00Z' });

async function page({ words = [makeWord()], mode = '', reviewError = false } = {}) {
  const nodes = new Map(); const events = {}; const writes = [];
  const modeButtons = ['list', 'flashcards', 'choice', 'write', 'letters'].map((mode) => { const n = new Element('button'); n.dataset.mode = mode; return n; });
  const filters = ['all', 'learning', 'learned', 'due'].map((filter) => { const n = new Element('button'); n.dataset.filter = filter; return n; });
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const location = { href: `http://localhost/vocabulary.html${mode ? '?mode=' + mode : ''}`, search: mode ? '?mode=' + mode : '' };
  const document = {
    getElementById: node, createElement: (tag) => new Element(tag),
    createElementNS: (ns, tag) => { const n = new Element(tag); n.namespaceURI = ns; return n; },
    querySelectorAll: (selector) => selector === '[data-mode]' ? modeButtons : selector === '[data-filter]' ? filters : selector.includes('#word-search') ? [...modeButtons, ...filters, node('word-search'), node('add-word')] : [],
  };
  let failReview = reviewError;
  const helpers = {
    listVocabulary: async (offset) => words.slice(offset, offset + 100),
    addVocabulary: async (input) => { writes.push({ add: input }); const word = { ...makeWord('added'), ...input }; words.push(word); return word; },
    updateVocabulary: async (id, learned) => { writes.push({ update: id, learned }); const word = words.find((w) => w.id === id); word.learned = learned; return { ...word }; },
    reviewVocabulary: async (id, remembered) => { writes.push({ review: id, remembered }); if (failReview) throw new Error('Offline'); const word = words.find((w) => w.id === id); word.learned = remembered; word.dueAt = new Date(Date.now() + 86400000).toISOString(); return { ...word }; },
  };
  const context = vm.createContext({ document, location, history: { replaceState: (_a, _b, url) => { location.href = url.toString(); } }, window: { addEventListener: (name, action) => { events[name] = action; } }, URL, URLSearchParams, console, setTimeout });
  const modules = new Map();
  function mock(name, values) { const mod = new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context, identifier: name }); modules.set(name, mod); }
  const el = (tag, cls, text) => { const n = new Element(tag, text); n.className = cls; return n; };
  mock('./api.js', helpers); mock('./layout.js', { el });
  mock('./errors.js', { describeApiError: (e) => e.message });
  mock('./session.js', { requireSession: async () => ({ id: 'user', displayName: 'Learner' }) });
  mock('./workspace.js', { mountWorkspace: () => {}, setWorkspaceUser: () => {} });
  const tiles = new vm.SourceTextModule(await readFile('frontend/js/letter-tiles.js', 'utf8'), { context, identifier: './letter-tiles.js' });
  modules.set('./letter-tiles.js', tiles);
  await tiles.link((name) => modules.get(name));
  const main = new vm.SourceTextModule(await readFile('frontend/js/vocabulary.js', 'utf8'), { context });
  await main.link((name) => modules.get(name)); await main.evaluate();
  const flush = async () => { for (let i = 0; i < 10; i++) await Promise.resolve(); };
  await flush();
  const click = async (element) => { assert.ok(element, 'control exists'); if (!element.disabled) await element.events.click?.({ preventDefault() {} }); await flush(); };
  const byText = (id, text) => node(id).querySelectorAll('button').find((n) => n.textContent.includes(text));
  return { node, mode: async (value) => click(modeButtons.find((n) => n.dataset.mode === value)), filter: async (value) => click(filters.find((n) => n.dataset.filter === value)), click, byText, writes, words, flush, fail: (value) => { failReview = value; } };
}

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

test('flashcards reveal before recording a review and persist remembered state', async () => {
  const app = await page(); await app.mode('flashcards');
  assert.equal(app.writes.length, 0);
  await app.click(app.byText('word-practice', 'Reveal translation'));
  await app.click(app.byText('word-practice', 'I knew it'));
  assert.equal(app.writes[0].remembered, true); assert.equal(app.words[0].learned, true);
  const progress = app.node('word-practice').querySelectorAll('div').find((n) => n.attributes.role === 'progressbar');
  assert.equal(progress.attributes['aria-valuenow'], '1');
  await app.click(app.byText('word-practice', 'See results'));
  assert.match(app.node('word-practice').textContent, /1 remembered/);
});

test('failed review does not advance or claim saved progress and allows retry', async () => {
  const app = await page({ mode: 'flashcards', reviewError: true });
  await app.click(app.byText('word-practice', 'Reveal translation'));
  await app.click(app.byText('word-practice', 'I knew it'));
  assert.match(app.node('word-practice').textContent, /not saved/);
  assert.equal(app.words[0].learned, false);
  assert.equal(app.byText('word-practice', 'See results'), undefined);
  app.fail(false); await app.click(app.byText('word-practice', 'I knew it'));
  assert.ok(app.byText('word-practice', 'See results'));
});

test('typed answers ignore casing and outer whitespace; wrong answers stay unlearned', async () => {
  const app = await page({ mode: 'write' });
  app.node('word-practice').querySelector('input').value = ' RESILIENCE ';
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.equal(app.writes[0].remembered, true);
  await app.mode('write');
  app.node('word-practice').querySelector('input').value = 'wrong';
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.equal(app.writes[1].remembered, false);
});

test('multiple choice submits the selected translation and handles insufficient words', async () => {
  const app = await page({ words: [makeWord('one', 'hello', 'привіт'), makeWord('two', 'bye', 'бувай')], mode: 'choice' });
  const current = app.node('word-practice').querySelector('h2').textContent;
  await app.click(app.byText('word-practice', current === 'hello' ? 'привіт' : 'бувай'));
  assert.equal(app.writes[0].remembered, true);
  const single = await page({ mode: 'choice' });
  assert.match(single.node('word-practice').textContent, /at least two words/);
  assert.equal(single.writes.length, 0);
});

test('missing-letter tiles are usable by clicking and submit the assembled word', async () => {
  const app = await page({ words: [makeWord('one', 'be', 'бути')], mode: 'letters' });
  const buttons = app.node('word-practice').querySelectorAll('button');
  const tile = buttons.find((n) => n.textContent === 'e');
  const slot = buttons.find((n) => n.className?.includes('lesson-tile-slot'));
  await app.click(tile); await app.click(slot);
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.equal(app.writes[0].remembered, true);
});

test('flashcard can turn both ways and hides assessment controls on its English face', async () => {
  const app = await page({ mode: 'flashcards' });
  const flip = app.node('word-practice').querySelectorAll('button').find((n) => n.className === 'flashcard-turn');
  assert.equal(flip.attributes['aria-pressed'], 'false');
  await app.click(flip);
  assert.equal(flip.attributes['aria-pressed'], 'true');
  assert.ok(app.byText('word-practice', 'I knew it'));
  await app.click(flip);
  assert.equal(flip.attributes['aria-pressed'], 'false');
  assert.equal(app.byText('word-practice', 'I knew it'), undefined);
  assert.equal(app.writes.length, 0);
});

test('session summary records only saved answers and repeats only the mistakes', async () => {
  const app = await page({ words: [makeWord('one', 'hello', 'привіт'), makeWord('two', 'bye', 'бувай')], mode: 'write' });
  app.node('word-practice').querySelector('input').value = 'wrong';
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  const failedId = app.writes[0].review;
  await app.click(app.byText('word-practice', 'Next word'));
  const translation = app.node('word-practice').querySelector('h2').textContent;
  app.node('word-practice').querySelector('input').value = app.words.find((w) => w.translation === translation).word;
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  await app.click(app.byText('word-practice', 'See results'));
  assert.match(app.node('word-practice').textContent, /50%/);
  assert.match(app.node('word-practice').textContent, /1 remembered · 1 to practise again/);
  await app.click(app.byText('word-practice', 'Repeat mistakes'));
  assert.match(app.node('word-practice').textContent, /1 \/ 1/);
  app.node('word-practice').querySelector('input').value = app.words.find((w) => w.id === failedId).word;
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  assert.equal(app.writes[2].review, failedId);
  assert.equal(app.writes[2].remembered, true);
});

test('replaying a due-only session keeps its words after their review dates move forward', async () => {
  const app = await page({ mode: 'write' });
  await app.filter('due');
  app.node('word-practice').querySelector('input').value = 'resilience';
  app.node('word-practice').querySelector('form').events.submit({ preventDefault() {} }); await app.flush();
  await app.click(app.byText('word-practice', 'See results'));
  await app.click(app.byText('word-practice', 'Practise again'));
  assert.ok(app.node('word-practice').querySelector('input'));
  assert.doesNotMatch(app.node('word-practice').textContent, /No words for this activity/);
});
