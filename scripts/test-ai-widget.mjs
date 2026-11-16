// Run with node --experimental-vm-modules scripts/test-ai-widget.mjs.
// Minimal DOM checks execute the production widget/workspace; CSS requires browser QA.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

class Node extends EventTarget {
  constructor(tag = 'div', text = '') {
    super(); this.tagName = tag; this.children = []; this.attributes = {}; this.dataset = {};
    this.style = { setProperty() {} }; this.className = ''; this.textContent = text;
    this.value = ''; this.hidden = false;
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
    createElement: (tag) => new Node(tag), getElementById: (id) => ids.get(id),
  };
  class Option extends Node { constructor(text, value) { super('option', text); this.value = value; } }
  let available = true, fail = false, owner = 'A', saved = false;
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
      return new Response(
        'event: delta\ndata: ' + JSON.stringify({ content: '<img src=x onerror=alert(1)>' }) + '\n\n' +
        'event: done\ndata: ' + JSON.stringify({ conversationId: `chat-${owner}`, message: { content: '<script>alert(1)</script>' } }) + '\n\n',
      );
    },
  };
  const context = vm.createContext({
    window, document, Option, Event, AbortController, TextDecoder, URLSearchParams, console,
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
    set: (values) => { if ('available' in values) available = values.available; if ('fail' in values) fail = values.fail; if ('owner' in values) owner = values.owner; },
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
  find(e.root(), 'ai-tools').children[2].dispatchEvent(new Event('click'));
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
