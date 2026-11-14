// DOM-level regression checks, not a replacement for browser/layout verification.
// Run: node --experimental-vm-modules --test scripts/test-courses.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

class Node {
  constructor(tag = 'div', text) {
    this.tagName = tag;
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.events = {};
    this.value = '';
    this.textContent = text ?? '';
  }
  set textContent(value) {
    this.text = value;
    this.children = [];
  }
  get textContent() {
    return this.text + this.children.map((node) => node.textContent).join(' ');
  }
  append(...nodes) {
    this.children.push(...nodes);
  }
  prepend(...nodes) {
    this.children.unshift(...nodes);
  }
  replaceChildren(...nodes) {
    this.text = '';
    this.children = nodes;
  }
  setAttribute(key, value) {
    this.attributes[key] = value;
  }
  addEventListener(key, callback) {
    this.events[key] = callback;
  }
  focus() {}
  querySelectorAll(tag) {
    return this.children.flatMap((node) => [
      ...(node.tagName === tag ? [node] : []),
      ...node.querySelectorAll(tag),
    ]);
  }
  closest() {
    return this;
  }
}

const catalog = [
  {
    id: 'one',
    slug: 'foundations',
    title: 'English Foundations',
    description: 'Learn greetings',
    level: 'A1',
    lessonCount: 3,
  },
  {
    id: 'two',
    slug: 'everyday',
    title: 'Everyday Conversations',
    description: 'Everyday speaking',
    level: 'B1',
    lessonCount: 2,
  },
];
const freshProgress = () => ({
  courses: catalog.map((course) => ({
    courseId: course.id,
    lessonsTotal: course.lessonCount,
    lessonsStarted: 0,
    lessonsCompleted: 0,
  })),
});

async function page(name, options = {}) {
  const nodes = new Map();
  const documentEvents = {};
  const windowEvents = {};
  let progress = options.progress ?? freshProgress();
  let failure = options.failure;
  const reads = [];
  const document = {
    hidden: false,
    createElement: (tag) => new Node(tag),
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, new Node());
      return nodes.get(id);
    },
    addEventListener: (key, callback) => {
      documentEvents[key] = callback;
    },
  };
  const window = {
    location: {
      search: '?slug=foundations',
      replace: (url) => {
        window.redirect = url;
      },
    },
    addEventListener: (key, callback) => {
      windowEvents[key] = callback;
    },
  };
  const filters = document.getElementById('course-filters');
  for (const level of ['All', 'A0', 'A1', 'A2', 'B1', 'B2']) {
    const button = new Node('button');
    button.dataset.level = level;
    filters.append(button);
  }
  const detail = {
    ...catalog[0],
    lessons: ['First', 'Second', 'Third'].map((title, index) => ({
      title,
      slug: `lesson-${index}`,
      summary: 'Practice English',
      estimatedMinutes: 10,
      position: index + 1,
    })),
  };
  const api = {
    listCourses: async () => (options.empty ? [] : options.catalog ?? catalog),
    getMyProgress: async () => {
      if (failure) throw failure;
      reads.push('progress');
      return progress;
    },
    getCourse: async () => {
      if (options.notFound) throw { status: 404 };
      return options.noLessons ? { ...detail, lessons: [] } : detail;
    },
    getLessonProgress: async (slug) => ({
      startedAt: slug === 'lesson-1' ? '2026-01-01' : null,
      completed: slug === 'lesson-0',
    }),
  };
  const context = vm.createContext({ document, window, URLSearchParams, Error, console });
  const modules = new Map();
  const stubs = {
    'api.js': api,
    'session.js': {
      requireSession: async () => {
        if (options.unauthorized) {
          window.location.replace('/login.html');
          return null;
        }
        return { displayName: 'Learner' };
      },
    },
    'workspace.js': {
      mountWorkspace: (active) => {
        assert.equal(active, 'courses');
      },
      setWorkspaceUser() {},
    },
    'errors.js': { describeApiError: (error) => error.message ?? 'Service unavailable' },
  };
  async function module(file) {
    if (modules.has(file)) return modules.get(file);
    let result;
    if (stubs[file]) {
      const values = stubs[file];
      result = new vm.SyntheticModule(
        Object.keys(values),
        function () {
          for (const [key, value] of Object.entries(values)) this.setExport(key, value);
        },
        { context },
      );
    } else if (file === 'layout.js') {
      // Use the production DOM/query helpers without unrelated header API dependencies.
      const source = await readFile(new URL('../frontend/js/layout.js', import.meta.url), 'utf8');
      result = new vm.SourceTextModule(
        source.slice(source.indexOf('/** Small DOM'), source.indexOf('/**\n * Render a card')),
        { context },
      );
    } else {
      result = new vm.SourceTextModule(
        await readFile(new URL(`../frontend/js/${file}`, import.meta.url), 'utf8'),
        { context },
      );
    }
    modules.set(file, result);
    await result.link((specifier) => module(specifier.replace('./', '')));
    return result;
  }
  const main = await module(`${name}.js`);
  await main.evaluate();
  const settle = () => new Promise((resolve) => setImmediate(resolve));
  await settle();
  return {
    get: (id) => document.getElementById(id),
    window,
    reads,
    settle,
    async refresh(nextProgress, nextFailure) {
      progress = nextProgress ?? progress;
      failure = nextFailure;
      windowEvents.pageshow({ persisted: true });
      await settle();
    },
  };
}

test('catalog combines case-insensitive title/description search and CEFR; clear/reset works', async () => {
  const p = await page('courses');
  assert.equal(p.get('courses-body').querySelectorAll('article').length, 2);
  const search = p.get('course-search');
  search.value = 'GREETINGS';
  search.events.input();
  assert.match(p.get('courses-body').textContent, /English Foundations/);
  assert.doesNotMatch(p.get('courses-body').textContent, /Everyday Conversations/);
  const filters = p.get('course-filters');
  const b1Filter = filters.children.find((button) => button.dataset.level === 'B1');
  filters.events.click({ target: b1Filter });
  assert.match(p.get('courses-body').textContent, /No courses found/);
  assert.equal(b1Filter.attributes['aria-pressed'], 'true');
  p.get('course-search-clear').events.click();
  assert.match(p.get('courses-body').textContent, /Everyday Conversations/);
  search.value = 'nothing';
  search.events.input();
  p.get('courses-body').querySelectorAll('button')[0].events.click();
  assert.equal(search.value, '');
  assert.equal(p.get('courses-body').querySelectorAll('article').length, 2);
});

test('catalog Start/Continue/Review and completion use API counts; return refreshes them', async () => {
  const p = await page('courses');
  assert.equal(p.get('courses-body').querySelectorAll('a')[0].textContent, 'Start Course');
  const progress = freshProgress();
  progress.courses[0].lessonsStarted = 1;
  await p.refresh(progress);
  assert.equal(p.get('courses-body').querySelectorAll('a')[0].textContent, 'Continue Course');
  progress.courses[0].lessonsCompleted = 3;
  await p.refresh(progress);
  assert.equal(p.get('courses-body').querySelectorAll('a')[0].textContent, 'Review Course');
  assert.match(p.get('courses-body').textContent, /3 of 3 lessons completed/);
  assert.equal(
    p.get('courses-body').querySelectorAll('a')[0].href,
    '/course.html?slug=foundations',
  );
});

test('empty catalog and service failure never render fake courses; retry recovers', async () => {
  const empty = await page('courses', { empty: true });
  assert.match(empty.get('courses-body').textContent, /No courses yet/);
  const p = await page('courses', { failure: new Error('Offline') });
  assert.match(p.get('courses-body').textContent, /Could not load courses/);
  assert.equal(p.get('courses-body').querySelectorAll('article').length, 0);
  await p.refresh();
  assert.equal(p.get('courses-body').querySelectorAll('article').length, 2);
});

test('course details show three real statuses and lesson routes', async () => {
  const p = await page('course');
  const body = p.get('course-body');
  assert.match(body.textContent, /Review Lesson/);
  assert.match(body.textContent, /Continue Lesson/);
  assert.match(body.textContent, /Start Lesson/);
  assert.match(body.textContent, /Not Started/);
  assert.match(body.textContent, /In Progress/);
  assert.deepEqual(
    body.querySelectorAll('a').map((link) => link.href),
    [
      '/courses.html',
      '/lesson.html?slug=lesson-0',
      '/lesson.html?slug=lesson-1',
      '/lesson.html?slug=lesson-2',
    ],
  );
  assert.equal(body.attributes['aria-busy'], 'false');
});

test('missing/unpublished courses and courses without lessons have honest states', async () => {
  const missing = await page('course', { notFound: true });
  assert.match(missing.get('course-body').textContent, /Course not found/);
  const empty = await page('course', { noLessons: true });
  assert.match(empty.get('course-body').textContent, /No lessons yet/);
});

test('both pages guard unauthenticated sessions and redirect expired sessions', async () => {
  for (const name of ['courses', 'course']) {
    const p = await page(name, { unauthorized: true });
    assert.equal(p.window.redirect, '/login.html');
    assert.equal(p.reads.length, 0);
    const expired = await page(name, { failure: { status: 401 } });
    assert.equal(expired.window.redirect, '/login.html');
  }
});


test('A0 uses the existing level filter and unchanged course links', async () => {
  const a0 = { ...catalog[0], id: 'a0', slug: 'fleng-a0', title: 'Absolute Beginner', level: 'A0' };
  const progress = { courses: [{ courseId: 'a0', lessonsTotal: 10, lessonsStarted: 0, lessonsCompleted: 0 }] };
  const p = await page('courses', { catalog: [a0], progress });
  const filters = p.get('course-filters');
  const a0Filter = filters.children.find((button) => button.dataset.level === 'A0');
  filters.events.click({ target: a0Filter });
  assert.match(p.get('courses-body').textContent, /Absolute Beginner/);
  assert.equal(p.get('courses-body').querySelectorAll('a')[0].href, '/course.html?slug=fleng-a0');
  assert.equal(a0Filter.attributes['aria-pressed'], 'true');
});

// Exercise the real lesson module with API fixtures; removed elements deliberately do not exist.
async function lessonPage(search = '?slug=first') {
  class LessonNode extends Node {
    get firstElementChild() { return this.children[0]; }
    querySelector(selector) {
      return this.children.flatMap((child) => [child, ...child.querySelectorAll('*')])
        .find((child) => selector.startsWith('.')
          ? child.className?.split(' ').includes(selector.slice(1)) : child.tagName === selector);
    }
    querySelectorAll(selector) {
      return this.children.flatMap((child) => [
        ...(selector === '*' || child.tagName === selector ? [child] : []),
        ...child.querySelectorAll(selector),
      ]);
    }
  }
  const nodes = new Map();
  const html = await readFile(new URL('../frontend/lesson.html', import.meta.url), 'utf8');
  for (const [, id] of html.matchAll(/\bid="([^"]+)"/g)) nodes.set(id, new LessonNode());
  const fill = new LessonNode('span');
  fill.className = 'lesson-fill';
  nodes.get('lesson-progress').append(fill);
  const window = {
    location: new URL('http://localhost/lesson.html' + search),
    history: { state: null, replaceState(_state, _title, url) { window.location = new URL(url); } },
  };
  const document = {
    getElementById: (id) => nodes.get(id) ?? null,
    createElement: (tag) => new LessonNode(tag),
  };
  let vocabularyReads = 0;
  const exercise = { id: 'exercise', type: 'single_choice', prompt: 'Choose a word', points: 1, options: [{ id: 'a', text: 'Hello' }] };
  const progress = {
    startedAt: '2026-01-01', completed: false, exercisesTotal: 1, exercisesCompleted: 0,
    xpEarned: 0, exercises: [{ exerciseId: 'exercise', attempts: 0, completed: false }],
  };
  const stubs = {
    'api.js': {
      getLesson: async () => ({ id: 'lesson', slug: 'first', title: 'First', theory: 'Study words.', exercises: [exercise] }),
      getLessonProgress: async () => progress,
      startLesson: async () => progress,
      submitAnswer: async () => { throw new Error('Navigation must not submit answers'); },
      getLessonVocabulary: async () => { vocabularyReads++; return [{ word: 'hello', translation: 'привіт' }]; },
    },
    'errors.js': { describeApiError: (error) => error.message },
    'session.js': { requireSession: async () => ({ displayName: 'Learner' }) },
    'workspace.js': { mountWorkspace() {}, setWorkspaceUser() {}, setWorkspaceAIContext() {} },
    'letter-tiles.js': { letterTiles() { throw new Error('Not used by this fixture'); } },
  };
  const context = vm.createContext({ window, document, URL, URLSearchParams, console });
  const modules = new Map();
  async function module(file) {
    if (modules.has(file)) return modules.get(file);
    let result;
    if (stubs[file]) {
      result = new vm.SyntheticModule(Object.keys(stubs[file]), function () {
        for (const [key, value] of Object.entries(stubs[file])) this.setExport(key, value);
      }, { context });
    } else {
      let source = await readFile(new URL(`../frontend/js/${file}`, import.meta.url), 'utf8');
      if (file === 'layout.js') source = source.slice(source.indexOf('/** Small DOM'), source.indexOf('/**\n * Render a card'));
      result = new vm.SourceTextModule(source, { context });
    }
    modules.set(file, result);
    await result.link((specifier) => module(specifier.replace('./', '')));
    return result;
  }
  await (await module('lesson.js')).evaluate();
  const settle = () => new Promise((resolve) => setImmediate(resolve));
  await settle();
  return { get: (id) => nodes.get(id), window, settle, vocabularyReads: () => vocabularyReads };
}

test('lesson defaults and obsolete Test links open Theory without losing the lesson URL', async () => {
  for (const tab of ['', '&tab=test', '&tab=Test', '&tab=unknown']) {
    const p = await lessonPage('?slug=first&keep=yes' + tab + '#content');
    assert.equal(p.get('lesson-content').hidden, false);
    assert.equal(p.get('panel-theory').hidden, false);
    assert.equal(p.get('tab-theory').attributes['aria-selected'], 'true');
    assert.equal(p.window.location.searchParams.get('tab'), null);
    assert.equal(p.window.location.searchParams.get('slug'), 'first');
    assert.equal(p.window.location.searchParams.get('keep'), 'yes');
    assert.equal(p.window.location.hash, '#content');
    assert.equal(p.get('tab-test'), undefined);
    assert.equal(p.get('panel-test'), undefined);
  }
});

test('lesson valid links, click/keyboard navigation and template actions use the three remaining tabs', async () => {
  const p = await lessonPage('?slug=first&tab=practice');
  assert.equal(p.get('panel-practice').hidden, false);
  assert.match(p.get('panel-practice').textContent, /Choose a word/);
  p.get('tab-practice').events.keydown({ key: 'ArrowRight', preventDefault() {} });
  await p.settle();
  assert.equal(p.get('panel-vocabulary').hidden, false);
  assert.match(p.get('panel-vocabulary').textContent, /hello/);
  assert.equal(p.vocabularyReads(), 1);
  assert.equal(p.window.location.searchParams.get('tab'), 'vocabulary');
  p.get('tab-vocabulary').events.keydown({ key: 'ArrowRight', preventDefault() {} });
  assert.equal(p.get('panel-theory').hidden, false);
  p.get('tab-theory').events.keydown({ key: 'End', preventDefault() {} });
  assert.equal(p.get('panel-vocabulary').hidden, false);
  p.get('tab-vocabulary').events.keydown({ key: 'Home', preventDefault() {} });
  assert.equal(p.get('panel-theory').hidden, false);
  p.get('use-template').events.click();
  assert.equal(p.get('panel-practice').hidden, false);
  p.get('tab-vocabulary').events.click();
  await p.settle();
  assert.equal(p.vocabularyReads(), 1);
  const linked = await lessonPage('?slug=first&tab=vocabulary');
  assert.equal(linked.get('panel-vocabulary').hidden, false);
  assert.match(linked.get('panel-vocabulary').textContent, /hello/);
});

test('Dashboard Quick access retains three live destinations and no Course card', async () => {
  const html = await readFile(new URL('../frontend/dashboard.html', import.meta.url), 'utf8');
  const quick = html.split('<div class="quick-grid">')[1].split('</section>')[0];
  assert.deepEqual([...quick.matchAll(/<strong>([^<]+)<\/strong\s*>/g)].map((match) => match[1]), ['Lessons', 'Progress', 'Leaderboard']);
  assert.deepEqual([...quick.matchAll(/href="([^"]+)"/g)].map((match) => match[1]).filter((href) => !href.startsWith('#icon')), ['/courses.html', '#your-progress', '/leaderboard.html']);
  assert.match(html, /id="your-progress"/);
  assert.doesNotMatch(html, /quick-course-link/);
});
