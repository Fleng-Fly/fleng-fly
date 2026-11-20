import './require-vm-modules.mjs';
// DOM-level regression checks, not a replacement for browser/layout verification.
// Run: node --experimental-vm-modules --test scripts/test-courses.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';
import { i18nStub } from './i18n-stub.mjs';

class Node {
  constructor(tag = 'div', text) {
    this.tagName = tag;
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.classList = { add() {}, remove() {}, toggle() {}, contains: () => false };
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
    'i18n.js': i18nStub,
    'placement-api.js': { listPlacements: async () => [], getPlacement: async () => { throw new Error('unused'); } },
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

test('finished course offers the next main-line course; unfinished shows none', async () => {
  const done = freshProgress();
  done.courses[0].lessonsStarted = 3;
  done.courses[0].lessonsCompleted = 3;
  const p = await page('course', { progress: done });
  assert.match(p.get('course-body').textContent, /Course completed/);
  assert.match(p.get('course-body').textContent, /Everyday Conversations/);
  assert.ok(p.get('course-body').querySelectorAll('a').some((a) => a.href === '/course.html?slug=everyday'));
  const open = await page('course');
  assert.doesNotMatch(open.get('course-body').textContent, /Course completed/);
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
async function lessonPage(search = '?slug=first', overrides = {}) {
  class LessonNode extends Node {
    get firstElementChild() { return this.children[0]; }
    querySelector(selector) {
      return this.children.flatMap((child) => [child, ...child.querySelectorAll('*')])
        .find((child) => selector === 'input:checked' ? child.tagName === 'input' && child.checked
          : selector.startsWith('.')
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
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  let vocabularyReads = 0;
  const aiContexts = [];
  const aiAsks = [];
  const exercise = { id: 'exercise', type: 'single_choice', prompt: 'Choose a word', points: 1, options: [{ id: 'a', text: 'Hello' }, { id: 'b', text: 'Bye' }], ...overrides.exercise };
  const progress = {
    startedAt: '2026-01-01', completed: false, exercisesTotal: 1, exercisesCompleted: 0,
    xpEarned: 0, exercises: [{ exerciseId: 'exercise', attempts: 0, completed: false }],
  };
  const stubs = {
    'api.js': {
      getLesson: async () => ({ id: 'lesson', slug: 'first', title: 'First', theory: overrides.theory ?? 'Study words.', guide: overrides.guide, exercises: [exercise] }),
      getLessonProgress: async () => overrides.progress ?? progress,
      startLesson: async () => overrides.progress ?? progress,
      submitAnswer: overrides.submit ?? (async () => { throw new Error('Navigation must not submit answers'); }),
      getCourse: async () => ({ lessons: [] }),
      listCourses: async () => [],
      getLessonVocabulary: async () => { vocabularyReads++; return [{ word: 'hello', translation: 'привіт' }]; },
    },
    'errors.js': { describeApiError: (error) => error.message },
    'i18n.js': i18nStub,
    'session.js': { requireSession: async () => ({ displayName: 'Learner' }) },
    'workspace.js': { mountWorkspace() {}, setWorkspaceUser() {}, setWorkspaceAIContext(callback) { aiContexts.push(callback); }, askWorkspaceAI: (detail) => { aiAsks.push(detail); return overrides.aiMounted ?? true; } },
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
  return { get: (id) => nodes.get(id), window, settle, vocabularyReads: () => vocabularyReads, aiContext: () => aiContexts.at(-1)?.(), aiAsks };
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

test('lesson valid links and click/keyboard navigation use the three tabs', async () => {
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
  p.get('tab-vocabulary').events.click();
  await p.settle();
  assert.equal(p.vocabularyReads(), 1);
  const linked = await lessonPage('?slug=first&tab=vocabulary');
  assert.equal(linked.get('panel-vocabulary').hidden, false);
  assert.match(linked.get('panel-vocabulary').textContent, /hello/);
});

test('Dashboard shows continue-learning, next-step and progress sections without duplicate navigation cards', async () => {
  const html = await readFile(new URL('../frontend/dashboard.html', import.meta.url), 'utf8');
  for (const id of ['current-course-body', 'placement-guidance', 'progress-body', 'your-progress']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.doesNotMatch(html, /quick-grid|quick-card|welcome-card|quick-course-link/);
});

test('hint stays hidden until requested and uses the interface language', async () => {
  const hint = { en: 'Think about the first sound.', uk: 'Подумай про перший звук.' };
  const p = await lessonPage('?slug=first&tab=practice', { exercise: { hint } });
  const panel = p.get('panel-practice');
  const note = panel.querySelector('.lesson-hint-text');
  const toggle = panel.querySelector('.lesson-hint-toggle');
  assert.equal(note.hidden, true);
  assert.equal(toggle.attributes['aria-expanded'], 'false');
  assert.match(note.textContent, /first sound/);
  toggle.events.click();
  assert.equal(note.hidden, false);
  assert.equal(toggle.attributes['aria-expanded'], 'true');
  toggle.events.click();
  assert.equal(note.hidden, true);
});

test('no hint control is shown when the API provides no hint', async () => {
  const p = await lessonPage('?slug=first&tab=practice');
  assert.equal(p.get('panel-practice').querySelector('.lesson-hint-toggle'), undefined);
});

test('wrong answer shows the localized explanation, wrong-answer note and the correct option', async () => {
  let calls = 0;
  const submit = async (_slug, payload) => {
    calls++;
    return {
      exerciseId: 'exercise', type: 'single_choice', isCorrect: false, completed: false, points: 1, xpAwarded: 0,
      correctOptionId: 'a', explanation: 'Correct choice: Hello.',
      explanationLocalized: { en: 'Greet people with “Hello”.', uk: 'Вітайся словом “Hello”.' },
      wrongAnswerNote: { en: '“Bye” is for leaving.', uk: '“Bye” — для прощання.' },
      lesson: { startedAt: '2026-01-01', completed: false, exercisesTotal: 1, exercisesCompleted: 0, xpEarned: 0, exercises: [{ exerciseId: 'exercise', attempts: 1, completed: false, isCorrect: false }] },
    };
  };
  const p = await lessonPage('?slug=first&tab=practice', { submit });
  const panel = p.get('panel-practice');
  const wrong = panel.querySelectorAll('input')[1];
  wrong.value = 'b'; wrong.checked = true;
  await panel.querySelector('form').events.submit({ preventDefault() {} });
  await p.settle();
  assert.equal(calls, 1);
  const text = panel.textContent;
  assert.match(text, /Why this does not fit:\s*“Bye” is for leaving\./);
  assert.match(text, /Explanation:\s*Greet people with “Hello”\./);
  assert.doesNotMatch(text, /Correct choice: Hello/);
  assert.match(text, /Correct answer:\s*Hello/);
});

test('lesson guide shows the rule and English examples', async () => {
  const guide = { explanation: { en: 'Use “am” with I.', uk: 'Вживай “am” з I.' }, examples: [{ en: 'I am Eva.', uk: 'Я Єва.' }, { en: 'I am happy.', uk: 'Я щасливий.' }] };
  const p = await lessonPage('?slug=first', { guide });
  const text = p.get('panel-theory').textContent;
  assert.match(text, /Explanation/);
  assert.match(text, /Use “am” with I\./);
  assert.match(text, /I am Eva\./);
  assert.match(text, /Study words\./);
});

test('completion screen shows only real counts from lesson progress', async () => {
  const done = {
    startedAt: '2026-01-01', completed: true, exercisesTotal: 3, exercisesCompleted: 3, xpEarned: 3,
    exercises: [
      { exerciseId: 'exercise', attempts: 1, completed: true, isCorrect: true },
      { exerciseId: 'x2', attempts: 2, completed: true, isCorrect: true },
      { exerciseId: 'x3', attempts: 1, completed: true, isCorrect: true },
    ],
  };
  const p = await lessonPage('?slug=first', { progress: done });
  const text = p.get('lesson-completed').textContent;
  assert.match(text, /3 \/ 3 activities/);
  assert.match(text, /Correct on the first try: 2 \/ 3/);
  assert.match(text, /Result: 67%/);
  assert.match(text, /3 XP earned/);
});

test('every exercise shows its task before the prompt, linked for screen readers', async () => {
  const instruction = { en: 'Choose the one correct answer.', uk: 'Виберіть одну правильну відповідь.' };
  const p = await lessonPage('?slug=first&tab=practice', { exercise: { instruction } });
  const card = p.get('panel-practice').querySelector('article');
  const task = card.querySelector('.lesson-instruction');
  const heading = card.querySelector('h2');
  assert.match(task.textContent, /Choose the one correct answer/);
  assert.ok(card.children.indexOf(task) < card.children.indexOf(heading));
  assert.equal(heading.attributes['aria-describedby'], task.id);
});

test('theory shows the rule as steps first and folds reading and word list away', async () => {
  const theory = [
    '## Learning goals', '- Ask about habits.',
    '## Present simple questions',
    'Use do or does before the subject. Does goes with he, she and it. After does, the verb has no -s.',
    '## Read in context', 'A: Do you walk? B: Yes, I do.',
    '## Vocabulary', '- usually — зазвичай',
  ].join('\n\n');
  const p = await lessonPage('?slug=first', { theory });
  const panel = p.get('panel-theory');
  const steps = panel.querySelector('.lesson-rule-steps');
  assert.ok(steps, 'rule steps rendered');
  assert.equal(steps.querySelectorAll('li').length, 3);
  const more = panel.querySelector('.lesson-theory-more');
  assert.equal(more.tagName, 'details');
  assert.match(more.textContent, /Do you walk/);
  assert.match(more.textContent, /usually/);
  assert.doesNotMatch(steps.textContent, /Do you walk/);
});

test('"I don\'t understand" opens Fleng AI about this exercise and keeps the draft answer', async () => {
  const exercise = { type: 'text', prompt: 'She ___ tea every day.', options: undefined };
  const p = await lessonPage('?slug=first&tab=practice', { exercise });
  const card = p.get('panel-practice').querySelector('article');
  const input = card.querySelector('input');
  input.value = 'drink';
  input.events.input();
  const button = card.querySelector('.lesson-not-clear');
  assert.match(button.textContent, /I don't understand/);
  button.events.click();
  assert.equal(p.aiAsks.length, 1);
  const [ask] = p.aiAsks;
  assert.match(ask.message, /don't understand this exercise/);
  assert.match(ask.label, /Question 1: “She ___ tea every day\.”/);
  assert.equal(ask.returnFocus, button);
  assert.deepEqual(JSON.parse(JSON.stringify(p.aiContext())), { lessonId: 'lesson', exerciseId: 'exercise', currentAnswer: 'drink' });
  // The page itself is untouched: the draft is still in the field.
  assert.equal(p.get('panel-practice').querySelector('article').querySelector('input').value, 'drink');
});

test('"I don\'t understand" explains when the assistant is not mounted', async () => {
  const p = await lessonPage('?slug=first&tab=practice', { aiMounted: false });
  const button = p.get('panel-practice').querySelector('.lesson-not-clear');
  button.events.click();
  assert.equal(button.disabled, true);
  assert.match(button.textContent, /not available/);
});
