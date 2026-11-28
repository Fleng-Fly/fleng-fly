import { addVocabulary, getCourse, listCourses, listCourseWords } from './api.js';
import { el } from './layout.js';
import { t, tn } from './i18n.js';
import { requireSession } from './session.js';
import { describeApiError } from './errors.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
let courses = new Map(), words = [], total = 0;
const pageSize = 50;
let pageIndex = 0, pending, timer;
const saved = new Set();
const englishKeys = "qwertyuiop[]asdfghjkl;'zxcvbnm,.";
const ukrainianKeys = 'йцукенгшщзхїфівапролджєячсмитьбю';

function alternateLayout(query) {
  const ukrainian = /[а-яіїєґ]/u.test(query);
  if (ukrainian === /[a-z]/.test(query)) return '';
  const [source, target] = ukrainian ? [ukrainianKeys, englishKeys] : [englishKeys, ukrainianKeys];
  return [...query].map((key) => target[source.indexOf(key)] ?? key).join('');
}

function render() {
  const target = $('course-word-list');
  target.replaceChildren();
  const start = pageIndex * pageSize;
  const end = start + words.length;
  $('course-word-count').textContent = tn('vocab.count', total);
  $('course-word-pages').hidden = total <= pageSize;
  $('course-word-previous').disabled = pageIndex === 0;
  $('course-word-next').disabled = end >= total;
  $('course-word-range').textContent = words.length ? `${start + 1}–${end}` : '';
  if (!words.length) {
    target.append(el('p', 'word-empty', t($('course-word-search').value.trim() ? 'cw.noMatch' : 'cw.none')));
    return;
  }
  for (const word of words) {
    const row = el('article', 'word-row course-word-row');
    const copy = el('div', 'word-copy');
    const course = courses.get(word.courseId);
    copy.append(el('small', undefined, [course ? `${course.level} · ${course.title}` : t('cw.course'), word.lessonTitle].filter(Boolean).join(' · ')), el('h3', undefined, word.word), el('p', undefined, word.translation));
    const details = word.lexicalDetails;
    const metadata = [word.pronunciation, details?.part_of_speech, details?.category].filter(Boolean);
    if (metadata.length) copy.append(el('small', undefined, metadata.join(' · ')));
    if (details?.alternative_translations?.length) {
      copy.append(el('p', undefined, details.alternative_translations.join(', ')));
    }
    if (word.example) copy.append(el('small', undefined, word.example));
    if (details?.example_translation) copy.append(el('small', undefined, details.example_translation));
    if (details?.source_url && /^https?:\/\//i.test(details.source_url)) {
      const source = el('a', 'dashboard-text-button', details.license_id);
      source.href = details.source_url;
      copy.append(source);
    }
    if (word.lessonSlug) {
      const link = el('a', 'dashboard-text-button', t('cw.openLesson', { lesson: word.lessonTitle || word.lessonSlug }));
      link.href = `/lesson.html?slug=${encodeURIComponent(word.lessonSlug)}`;
      copy.append(link);
    }
    const actions = el('div', 'word-row-actions');
    const save = el('button', 'lesson-button lesson-button-secondary', saved.has(word.id) ? t('cw.saved') : t('cw.save'));
    save.type = 'button'; save.disabled = saved.has(word.id);
    const practice = el('button', 'lesson-button lesson-button-primary', t('cw.savePractise'));
    practice.type = 'button';
    async function persist(startPractice) {
      save.disabled = practice.disabled = true;
      $('course-word-feedback').textContent = '';
      try {
        if (!saved.has(word.id)) {
          try { await addVocabulary({ word: word.word, translation: word.translation, example: word.example || '', lessonId: word.lessonId }); }
          catch (error) { if (error.code !== 'WORD_EXISTS') throw error; }
        }
        saved.add(word.id);
        save.textContent = t('cw.saved');
        $('course-word-feedback').textContent = t('cw.ready');
        if (startPractice) location.assign(`/vocabulary.html?${new URLSearchParams({ mode: 'flashcards', word: word.word })}`);
      } catch (error) {
        $('course-word-feedback').textContent = describeApiError(error);
      } finally {
        save.disabled = saved.has(word.id); practice.disabled = false;
      }
    }
    save.addEventListener('click', () => persist(false));
    practice.addEventListener('click', () => persist(true));
    actions.append(save, practice); row.append(copy, actions); target.append(row);
  }
}

const courseFilter = $('word-course');
const levelFilter = $('word-level');
const lessonFilter = $('word-lesson');
const searchInput = $('course-word-search');
const loading = $('course-words-loading');
const errorBox = $('course-words-error');
const catalogDetails = new Map();

function fillCourses() {
  const choices = [...courses.values()].filter((course) => !levelFilter.value || course.level === levelFilter.value);
  courseFilter.replaceChildren(new Option(t('cw.allCourses'), ''), ...choices.map((course) =>
    new Option(`${course.level} · ${course.title}`, course.id)));
}

async function load() {
  pending?.abort();
  const controller = new AbortController();
  pending = controller;
  const signal = controller.signal;
  loading.hidden = false;
  errorBox.hidden = true;
  $('course-word-pages').hidden = true;
  try {
    const courseId = courseFilter.value;
    if (courseId && !catalogDetails.has(courseId)) {
      const detail = await getCourse(courses.get(courseId).slug);
      if (signal.aborted) return;
      catalogDetails.set(courseId, detail.lessons);
      lessonFilter.replaceChildren(new Option(t('cw.allLessons'), ''), ...detail.lessons.map((lesson) =>
        new Option(lesson.title, lesson.id)));
      lessonFilter.disabled = !detail.lessons.length;
    } else if (courseId && lessonFilter.options.length === 1) {
      const lessons = catalogDetails.get(courseId);
      lessonFilter.replaceChildren(new Option(t('cw.allLessons'), ''), ...lessons.map((lesson) =>
        new Option(lesson.title, lesson.id)));
      lessonFilter.disabled = !lessons.length;
    }
    const search = searchInput.value.normalize('NFKC').trim().slice(0, 120);
    const options = { courseId, lessonId: lessonFilter.value, level: levelFilter.value,
      search, offset: pageIndex * pageSize, limit: pageSize, signal };
    const test = new URLSearchParams({ mode: 'mixed' });
    if (options.courseId) test.set('courseId', options.courseId);
    if (options.level) test.set('level', options.level);
    if (options.lessonId) test.set('lessonId', options.lessonId);
    $('course-word-tests').href = `/vocabulary.html?${test}`;
    let page = await listCourseWords(options);
    const alternate = alternateLayout(search.toLowerCase());
    if (!page.total && alternate) page = await listCourseWords({ ...options, search: alternate });
    if (signal.aborted) return;
    ({ total, words } = page);
    render();
  } catch (error) {
    if (signal.aborted) return;
    if (error.status === 401) { location.replace('/login.html'); return; }
    $('course-words-error-text').textContent = describeApiError(error);
    errorBox.hidden = false;
  } finally {
    if (!signal.aborted) loading.hidden = true;
  }
}

function reload() {
  clearTimeout(timer);
  pageIndex = 0;
  load();
}

function changeCourse() {
  lessonFilter.replaceChildren(new Option(t('cw.allLessons'), ''));
  lessonFilter.disabled = true;
  reload();
}

async function init() {
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    const catalog = await listCourses();
    courses = new Map(catalog.map((course) => [course.id, course]));
    const levels = [...new Set(catalog.map((course) => course.level))].sort();
    levelFilter.replaceChildren(new Option(t('courses.all'), ''), ...levels.map((level) => new Option(level, level)));
    fillCourses();
    levelFilter.addEventListener('change', () => { fillCourses(); changeCourse(); });
    courseFilter.addEventListener('change', changeCourse);
    lessonFilter.addEventListener('change', reload);
    searchInput.addEventListener('input', () => {
      $('course-word-clear').hidden = !searchInput.value;
      pending?.abort();
      clearTimeout(timer);
      timer = setTimeout(reload, 200);
    });
    $('course-word-previous').addEventListener('click', () => { pageIndex -= 1; load(); });
    $('course-word-next').addEventListener('click', () => { pageIndex += 1; load(); });
    $('course-word-clear').addEventListener('click', () => {
      searchInput.value = '';
      $('course-word-clear').hidden = true;
      searchInput.focus();
      reload();
    });
    await load();
  } catch (error) {
    loading.hidden = true;
    $('course-words-error-text').textContent = describeApiError(error);
    errorBox.hidden = false;
  }
}

mountWorkspace('course-words');
$('course-words-retry').addEventListener('click', () => courses.size ? load() : init());
init();
