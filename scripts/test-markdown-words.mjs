import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Node {
  constructor(tag = 'div', text = '') {
    this.tagName = tag; this.children = []; this.text = text; this.attributes = {}; this.id = '';
    this.names = new Set();
    this.classList = { toggle: (name, on) => on ? this.names.add(name) : this.names.delete(name) };
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
  set textContent(value) { this.text = value; this.children = []; }
  get textContent() { return this.text + this.children.map((n) => n.textContent).join(''); }
  set innerHTML(_) { throw new Error('Raw HTML is forbidden'); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  getAttribute(name) { return this.attributes[name]; }
}
const all = (node, tag) => [...(node.tagName === tag ? [node] : []), ...node.children.flatMap((n) => all(n, tag))];
const context = vm.createContext({ URL, document: { createElement: (tag) => new Node(tag), createTextNode: (text) => new Node('#text', text) } });
const markdown = new vm.SourceTextModule(await readFile('frontend/js/markdown.js', 'utf8'), { context });
await markdown.link(() => { throw new Error('No dependencies expected'); }); await markdown.evaluate();
const { renderMarkdown, safeMarkdownURL } = markdown.namespace;

test('Markdown renders emphasis, paragraphs, breaks, nested and numbered lists, code and links', () => {
  const root = new Node();
  renderMarkdown(root, '**Bold** and *italic* with `inline`\nnext line\n\n- one\n  - nested\n- two\n\n3. third\n4. fourth\n\n```js\nconst x = "<img onerror=alert(1)>";\n```\n\n[Learn](https://example.com/lesson)');
  for (const tag of ['strong', 'em', 'br', 'ul', 'ol', 'li', 'pre', 'code', 'a']) assert.ok(all(root, tag).length, tag);
  assert.equal(all(root, 'ul').length, 2);
  assert.equal(all(root, 'ol')[0].attributes.start, '3');
  assert.equal(all(root, 'a')[0].attributes.rel, 'noopener noreferrer');
  assert.equal(all(root, 'img').length, 0);
  assert.match(all(root, 'pre')[0].textContent, /<img onerror/);
});

test('Markdown rejects HTML, events, SVG, unsafe links and obfuscated protocols', () => {
  const root = new Node();
  const payload = '<script>alert(1)</script><svg onload=alert(1)><img src=x onerror=alert(1)>';
  renderMarkdown(root, payload + '\n\n[x](javascript:evil) [x](data:text/html,evil) [x](vbscript:evil) [x](//evil.example) [x](JaVaScRiPt:evil)');
  for (const tag of ['script', 'svg', 'img', 'iframe', 'a']) assert.equal(all(root, tag).length, 0, tag);
  assert.ok(root.textContent.includes(payload));
  for (const value of ['java\nscript:evil', 'javascript:evil', 'data:text/html,evil', '//evil.example', '\\evil.example', 'https://user:password@example.com', 'java%73cript:evil']) assert.equal(safeMarkdownURL(value), null, value);
  for (const value of ['https://example.com', 'http://example.com', 'mailto:hello@example.com', '/courses.html', '#section']) assert.equal(safeMarkdownURL(value), value);
});

test('streaming rerenders unfinished Markdown safely and replaces the previous tree', () => {
  const root = new Node();
  for (const source of ['**Hel', '**Hello**\n\n```js\n<script>evil', '**Hello**\n\n```js\n<script>evil\n```']) {
    renderMarkdown(root, source);
    assert.equal(all(root, 'script').length, 0);
  }
  assert.equal(all(root, 'strong').length, 1);
  assert.equal(all(root, 'pre').length, 1);
  renderMarkdown(root, '[safe **label**](https://example.com)');
  assert.equal(all(root, 'pre').length, 0);
  assert.equal(all(root, 'strong').length, 1);
});

const workspace = new vm.SourceTextModule(await readFile('frontend/js/workspace.js', 'utf8'), { context });
await workspace.link((specifier) => {
  const exports = specifier === './api.js' ? ['getCourse', 'listCourses', 'logout', 'setAccessToken']
    : specifier === './ai-assistant.js' ? ['askAIAssistant', 'mountAIAssistant', 'unmountAIAssistant']
    : specifier === './session.js' ? ['requireSession']
    : specifier === './errors.js' ? ['describeApiError']
    : specifier === './i18n.js' ? Object.keys(i18nStub) : ['el'];
  return new vm.SyntheticModule(exports, function () { for (const name of exports) this.setExport(name, specifier === './i18n.js' ? i18nStub[name] : () => {}); }, { context });
}); await workspace.evaluate();

for (const active of ['words', 'practice', 'course-words', 'dashboard']) {
  test(`My Words is a single top-level link: ${active} selects it only on its own page`, () => {
    const destinations = ['/dashboard.html', '/courses.html', '/vocabulary.html'];
    const links = destinations.map((href) => { const node = new Node('a'); node.setAttribute('href', href); return node; });
    const scope = { querySelectorAll: () => links, querySelector: () => null };
    workspace.namespace.markWorkspaceNavigation(scope, active);
    const selected = links.filter((link) => link.attributes['aria-current'] === 'page');
    const expected = { words: '/vocabulary.html', practice: '/vocabulary.html', dashboard: '/dashboard.html' }[active];
    assert.deepEqual(selected.map((link) => link.attributes.href), expected ? [expected] : []);
  });
}

test('Course Words pages real API data, filters by course, saves and opens existing practice', async () => {
  const nodes = new Map(), calls = [], saves = [], navigations = [];
  class Element extends Node {
    constructor(tag = 'div', text = '') { super(tag, text); this.events = {}; this.value = ''; this.hidden = false; }
    addEventListener(name, fn) { this.events[name] = fn; }
  }
  class Option extends Element { constructor(text, value) { super('option', text); this.value = value; } }
  const node = (id) => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const words = Array.from({ length: 101 }, (_, i) => ({ id: String(i), courseId: 'course', word: `word${i}`, translation: `translation${i}`, example: '' }));
  let fail = false;
  const api = {
    listCourses: async () => [{ id: 'course', title: 'Course title', level: 'A1' }],
    listCourseWords: async (course, offset) => { calls.push([course, offset]); if (fail) throw new Error('Offline'); return words.slice(offset, offset + 100); },
    addVocabulary: async (payload) => { saves.push(payload); },
  };
  const courseContext = vm.createContext({
    document: { getElementById: node, createElement: (tag) => new Element(tag) }, Option, URLSearchParams,
    location: { assign: (url) => navigations.push(url), replace() {} },
  });
  const source = new vm.SourceTextModule(await readFile('frontend/js/course-words.js', 'utf8'), { context: courseContext });
  await source.link((specifier) => {
    const values = specifier === './api.js' ? api
      : specifier === './layout.js' ? { el: (tag, cls, text) => new Element(tag, text || '') }
      : specifier === './session.js' ? { requireSession: async () => ({ id: 'user' }) }
      : specifier === './errors.js' ? { describeApiError: (error) => error.message }
      : specifier === './i18n.js' ? i18nStub
      : { mountWorkspace: (section) => assert.equal(section, 'course-words'), setWorkspaceUser() {} };
    return new vm.SyntheticModule(Object.keys(values), function () { for (const [key, value] of Object.entries(values)) this.setExport(key, value); }, { context: courseContext });
  });
  await source.evaluate();
  for (let i = 0; i < 30; i++) await Promise.resolve();
  assert.equal(node('course-word-count').textContent, '101 words');
  assert.deepEqual(calls, [['', 0], ['', 100]]);
  node('course-word-search').value = 'translation100'; node('course-word-search').events.input();
  assert.equal(node('course-word-count').textContent, '1 word');
  const buttons = all(node('course-word-list'), 'button');
  await buttons[0].events.click();
  assert.equal(saves.length, 1);
  assert.equal(saves[0].word, 'word100');
  await buttons[1].events.click();
  assert.equal(saves.length, 1);
  assert.equal(navigations[0], '/vocabulary.html?mode=flashcards&word=word100');
  node('word-course').value = 'course';
  fail = true;
  await node('word-course').events.change();
  assert.equal(node('course-words-error').hidden, false);
  assert.match(node('course-words-error-text').textContent, /Offline/);
  fail = false;
  await node('course-words-retry').events.click();
  assert.equal(node('course-words-error').hidden, true);
  assert.deepEqual(calls.at(-1), ['course', 100]);
});
