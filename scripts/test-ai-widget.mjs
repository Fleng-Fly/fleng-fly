import './require-vm-modules.mjs';
// Run with node --experimental-vm-modules scripts/test-ai-widget.mjs.
// Minimal DOM checks execute the production widget/workspace; CSS requires browser QA.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Node extends EventTarget {
  constructor(tag = 'div', text = '') {
    super(); this.tagName = tag; this.children = []; this.attributes = {}; this.dataset = {};
    this.style = { setProperty() {} }; this.className = ''; this.textContent = text;
    this.value = ''; this.hidden = false;
    this.scrollHeight = 1000; this.clientHeight = 200; this.scrollTop = 800;
    this.classList = {
      contains: (value) => this.className.split(' ').includes(value),
      toggle: (value, enabled) => {
        const names = new Set(this.className.split(' '));
        if (enabled) names.add(value); else names.delete(value);
        this.className = [...names].join(' ');
      },
    };
  }
  set textContent(value) { this.text = value; this.children = []; }
  get textContent() { return this.text + this.children.map((node) => node.textContent).join(' '); }
  set innerHTML(_) { throw new Error('Unsafe HTML rendering'); }
  append(...nodes) { for (const node of nodes) { node.parent = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.text = ''; this.children = []; this.append(...nodes); }
  setAttribute(key, value) { this.attributes[key] = value; }
  get options() { return this.children; }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter((node) => node !== this); }
  focus() {}
  contains(node) { return this === node || this.children.some((child) => child.contains(node)); }
}
function all(root, predicate) {
  return [...(predicate(root) ? [root] : []), ...root.children.flatMap((node) => all(node, predicate))];
}
const find = (root, className) => all(root, (node) => node.className.split(' ').includes(className))[0];
const settle = () => new Promise((resolve) => setImmediate(resolve));

async function environment() {
  const storage = new Map();
  const ids = new Map(['profile-short-name', 'profile-avatar'].map((id) => [id, new Node()]));
  const window = new EventTarget(); window.innerHeight = 900;
  const document = {
    head: new Node('head'), body: new Node('body'),
    createElement: (tag) => new Node(tag), createTextNode: (text) => new Node('#text', text), getElementById: (id) => ids.get(id),
  };
  class Option extends Node { constructor(text, value) { super('option', text); this.value = value; } }
  let available = true, fail = false, owner = 'A', saved = false, pause, reply = '<script>alert(1)</script>';
  const calls = [];
  const api = {
    getAIStatus: async () => ({ available, maxInputChars: 4000 }),
    listAIConversations: async () => saved ? [{ id: `chat-${owner}`, createdAt: '2026-01-01' }] : [],
    getAIHistory: async (id) => {
      assert.equal(id, `chat-${owner}`);
      return [{ role: 'assistant', content: `History for ${owner}: <script>safe text</script>` }];
    },
    streamAIChat: async (payload, { signal }) => {
      calls.push({ payload, signal });
      if (fail) throw Object.assign(new Error('Offline'), { code: 'NETWORK_ERROR' });
      saved = true;
      if (pause) await pause;
      return new Response(
        'event: delta\ndata: ' + JSON.stringify({ content: '<img src=x onerror=alert(1)>' }) + '\n\n' +
        'event: done\ndata: ' + JSON.stringify({ conversationId: `chat-${owner}`, message: { content: reply } }) + '\n\n',
      );
    },
  };
  const context = vm.createContext({
    window, document, Option, Event, AbortController, TextDecoder, URLSearchParams, URL, console,
    crypto: { randomUUID: () => 'fake-request-id' },
    localStorage: {
      getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value),
      removeItem: (key) => storage.delete(key),
    },
  });
  const modules = new Map();
  async function module(file) {
    if (modules.has(file)) return modules.get(file);
    const stubs = {
      'api.js': api,
      'session.js': { requireSession: async () => ({ id: owner, displayName: owner }) },
      'errors.js': { describeApiError: () => 'Unavailable' },
      'i18n.js': i18nStub,
    };
    let result;
    if (stubs[file]) {
      const values = stubs[file];
      result = new vm.SyntheticModule(Object.keys(values), function () {
        for (const [key, value] of Object.entries(values)) this.setExport(key, value);
      }, { context });
    } else {
      let source = await readFile(new URL(`../frontend/js/${file}`, import.meta.url), 'utf8');
      if (file === 'layout.js') source = source.slice(source.indexOf('/** Small DOM'), source.indexOf('/**\n * Render a card'));
      // Navigation-only API imports are unused by setWorkspaceUser in this DOM test.
      if (file === 'workspace.js') source = source.replace(/^import .* from '.\/api.js';\n/, '');
      result = new vm.SourceTextModule(source, { context });
    }
    modules.set(file, result);
    await result.link((specifier) => module(specifier.replace('./', '')));
    return result;
  }
  const workspace = await module('workspace.js'); await workspace.evaluate();
  const widget = modules.get('ai-assistant.js').namespace;
  return {
    document, window, storage, calls, widget, workspace: workspace.namespace,
    set: (values) => { if ('available' in values) available = values.available; if ('fail' in values) fail = values.fail; if ('owner' in values) owner = values.owner; if ('pause' in values) pause = values.pause; if ('reply' in values) reply = values.reply; },
    root: () => find(document.body, 'fleng-ai'),
  };
}

for (const page of ['dashboard', 'courses', 'course', 'lesson', 'leaderboard', 'settings']) {
  test(`${page}: authenticated workspace mounts exactly one shared assistant`, async () => {
    const source = await readFile(new URL(`../frontend/js/${page}.js`, import.meta.url), 'utf8');
    assert.match(source, /setWorkspaceUser\(/);
    const e = await environment();
    e.workspace.setWorkspaceUser({ id: 'A', displayName: 'Learner' });
    e.workspace.setWorkspaceUser({ id: 'A', displayName: 'Updated name' });
    assert.equal(all(e.document.body, (node) => node.className === 'fleng-ai').length, 1);
    assert.equal(e.document.head.children.length, 1);
    assert.equal(e.root().dataset.state, 'CLOSED');
  });
}

test('open/minimize/close, streaming XSS, context allowlist and navigation history', async () => {
  const e = await environment();
  e.workspace.setWorkspaceAIContext(() => ({ lessonId: 'lesson', exerciseId: 'exercise', system: 'ignored' }));
  e.workspace.setWorkspaceUser({ id: 'A', displayName: 'Learner' });
  const widget = e.widget.mountAIAssistant({ id: 'A' });
  await widget.open();
  const root = e.root();
  const input = find(root, 'ai-composer').children[0];
  input.value = '<svg onload=alert(1)>';
  find(root, 'ai-composer').dispatchEvent(new Event('submit', { cancelable: true }));
  await settle();
  assert.match(find(root, 'ai-messages').textContent, /<svg onload=alert\(1\)>/);
  assert.match(find(root, 'ai-messages').textContent, /<script>alert\(1\)<\/script>/);
  assert.equal(e.calls[0].payload.lessonId, 'lesson');
  assert.equal(e.calls[0].payload.exerciseId, 'exercise');
  assert.equal(e.calls[0].payload.system, undefined);
  assert.equal(e.storage.get('fleng.ai.conversation.A'), 'chat-A');
  find(root, 'ai-header').children[1].dispatchEvent(new Event('click'));
  assert.equal(root.dataset.state, 'MINIMIZED');
  await widget.open();
  find(root, 'ai-header').children[2].dispatchEvent(new Event('click'));
  assert.equal(root.dataset.state, 'CLOSED');
  await widget.open();
  assert.match(find(root, 'ai-messages').textContent, /<script>alert/);
  e.widget.unmountAIAssistant();
  e.workspace.setWorkspaceUser({ id: 'A', displayName: 'A' });
  await e.widget.mountAIAssistant({ id: 'A' }).open();
  assert.match(find(e.root(), 'ai-messages').textContent, /History for A/);
});

test('logout clears private DOM and selection, aborts streaming, and isolates next account', async () => {
  const e = await environment();
  e.workspace.setWorkspaceUser({ id: 'A', displayName: 'A' });
  await e.widget.mountAIAssistant({ id: 'A' }).open();
  find(e.root(), 'ai-composer').children[0].value = 'Hello';
  find(e.root(), 'ai-composer').dispatchEvent(new Event('submit', { cancelable: true }));
  e.window.dispatchEvent(new Event('fleng:session-ended'));
  await settle();
  assert.equal(e.calls[0].signal.aborted, true);
  assert.equal(e.root(), undefined);
  assert.equal(e.storage.has('fleng.ai.conversation.A'), false);
  e.set({ owner: 'B' });
  e.workspace.setWorkspaceUser({ id: 'B', displayName: 'B' });
  await e.widget.mountAIAssistant({ id: 'B' }).open();
  assert.doesNotMatch(find(e.root(), 'ai-messages').textContent, /History for A/);
});

test('unavailable and network errors disable sending without automatic paid retries', async () => {
  const e = await environment();
  e.set({ available: false });
  const widget = e.widget.mountAIAssistant({ id: 'A' });
  await widget.open();
  assert.equal(e.root().dataset.state, 'UNAVAILABLE');
  assert.equal(find(e.root(), 'ai-composer').children[1].disabled, true);
  e.set({ available: true, fail: true });
  find(e.root(), 'ai-refresh').dispatchEvent(new Event('click'));
  await settle();
  find(e.root(), 'ai-composer').children[0].value = 'Hi';
  find(e.root(), 'ai-composer').dispatchEvent(new Event('submit', { cancelable: true }));
  await settle();
  assert.equal(e.calls.length, 1);
  assert.equal(e.root().dataset.state, 'ERROR');
  assert.equal(find(e.root(), 'ai-composer').children[1].disabled, true);
});

test('public pages have no assistant/workspace initialization', async () => {
  for (const name of ['home', 'login', 'register']) {
    const source = await readFile(new URL(`../frontend/js/${name}.js`, import.meta.url), 'utf8');
    assert.doesNotMatch(source, /mountAIAssistant|mountWorkspace|setWorkspaceUser/);
  }
});


test('500-character cap, streamed Markdown and manual scroll are preserved', async () => {
  const e = await environment();
  const widget = e.widget.mountAIAssistant({ id: 'A' });
  await widget.open();
  const form = find(e.root(), 'ai-composer'), input = form.children[0];
  assert.equal(input.maxLength, 500); // status mock advertises 4000; UI remains capped.
  input.value = 'x'.repeat(501);
  input.dispatchEvent(new Event('input'));
  form.dispatchEvent(new Event('submit', { cancelable: true }));
  await settle();
  assert.equal(e.calls.length, 0);
  let resume;
  e.set({ pause: new Promise((resolve) => { resume = resolve; }), reply: '**Helpful** and *clear*' });
  input.value = '**plain user text**';
  input.dispatchEvent(new Event('input'));
  form.dispatchEvent(new Event('submit', { cancelable: true }));
  const messages = find(e.root(), 'ai-messages');
  assert.equal(find(e.root(), 'ai-typing').hidden, false);
  messages.scrollTop = 0;
  messages.dispatchEvent(new Event('scroll'));
  resume(); await settle();
  assert.equal(messages.scrollTop, 0);
  assert.equal(find(e.root(), 'ai-jump').hidden, false);
  assert.equal(all(find(e.root(), 'ai-assistant'), (node) => node.tagName === 'strong').length, 1);
  assert.equal(all(find(e.root(), 'ai-user'), (node) => node.tagName === 'strong').length, 0);
  find(e.root(), 'ai-jump').dispatchEvent(new Event('click'));
  assert.equal(messages.scrollTop, messages.scrollHeight);
  assert.equal(find(e.root(), 'ai-typing').hidden, true);
  assert.match(find(e.root(), 'ai-counter').textContent, /0 \/ 500/);
});

test('ask() opens the panel about one exercise, sends its context and returns focus', async () => {
  const e = await environment();
  let answer = 'drink';
  e.workspace.setWorkspaceAIContext(() => ({ lessonId: 'lesson', exerciseId: 'exercise', currentAnswer: answer }));
  e.workspace.setWorkspaceUser({ id: 'A', displayName: 'Learner' });
  let focused = 0;
  const returnFocus = { isConnected: true, focus: () => { focused++; } };
  assert.equal(e.workspace.askWorkspaceAI({ message: 'I do not understand', label: 'Question 3: “She ___ tea.”', backLabel: 'Back to the exercise', returnFocus }), true);
  for (let i = 0; i < 5; i++) await settle();
  const root = e.root();
  assert.equal(find(root, 'ai-panel').hidden, false);
  assert.match(find(root, 'ai-context').textContent, /Question 3/);
  assert.equal(e.calls.length, 1);
  assert.equal(e.calls[0].payload.message, 'I do not understand');
  assert.equal(e.calls[0].payload.exerciseId, 'exercise');
  assert.equal(e.calls[0].payload.currentAnswer, 'drink');
  // Follow-up questions keep the exercise context.
  answer = '';
  const input = find(root, 'ai-composer').children[0];
  input.value = 'Why does?';
  find(root, 'ai-composer').dispatchEvent(new Event('submit', { cancelable: true }));
  for (let i = 0; i < 5; i++) await settle();
  assert.equal(e.calls[1].payload.exerciseId, 'exercise');
  assert.equal('currentAnswer' in e.calls[1].payload, false);
  // "Back to the exercise" closes the panel and puts focus back on the exercise.
  const back = find(root, 'ai-back');
  assert.equal(back.hidden, false);
  back.dispatchEvent(new Event('click'));
  assert.equal(find(root, 'ai-panel').hidden, true);
  assert.equal(focused, 1);
});

test('ask() never sends when Fleng AI is unavailable', async () => {
  const e = await environment();
  e.set({ available: false });
  e.workspace.setWorkspaceAIContext(() => ({ lessonId: 'lesson', exerciseId: 'exercise' }));
  e.workspace.setWorkspaceUser({ id: 'A', displayName: 'Learner' });
  e.workspace.askWorkspaceAI({ message: 'Help', label: 'Question 1' });
  for (let i = 0; i < 5; i++) await settle();
  assert.equal(e.calls.length, 0);
  assert.equal(e.root().dataset.state, 'UNAVAILABLE');
});
