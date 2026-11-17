import { addVocabulary, listCourses, listCourseWords } from './api.js';
import { el } from './layout.js';
import { t, tn } from './i18n.js';
import { requireSession } from './session.js';
import { describeApiError } from './errors.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
let courses = [], words = [], request = 0, sessionReady = false;
const saved = new Set();

function render() {
  const query = $('course-word-search').value.trim().toLocaleLowerCase();
  const visible = words.filter((word) => `${word.word} ${word.translation} ${word.example}`.toLocaleLowerCase().includes(query));
  $('course-word-count').textContent = tn('vocab.count', visible.length);
  const target = $('course-word-list');
  target.replaceChildren();
  if (!visible.length) {
    target.append(el('p', 'word-empty', query ? t('cw.noMatch') : t('cw.none')));
    return;
  }
  for (const word of visible) {
    const row = el('article', 'word-row course-word-row');
    const copy = el('div', 'word-copy');
    const course = courses.find((item) => item.id === word.courseId);
    copy.append(el('small', undefined, course ? `${course.level} · ${course.title}` : t('cw.course')), el('h3', undefined, word.word), el('p', undefined, word.translation));
    if (word.example) copy.append(el('small', undefined, word.example));
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
          try { await addVocabulary({ word: word.word, translation: word.translation, example: word.example || '' }); }
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

async function load() {
  const serial = ++request;
  words = [];
  $('course-words-loading').hidden = false;
  $('course-words-error').hidden = true;
  $('course-word-count').textContent = '';
  $('course-word-list').replaceChildren();
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (!user || serial !== request) return;
      setWorkspaceUser(user);
      courses = await listCourses();
      if (serial !== request) return;
      $('word-course').replaceChildren(new Option(t('cw.allCourses'), ''), ...courses.map((course) => new Option(`${course.level} · ${course.title}`, course.id)));
      sessionReady = true;
    }
    const courseId = $('word-course').value;
    const loaded = [];
    for (let offset = 0; ; offset += 100) {
      const page = await listCourseWords(courseId, offset);
      if (serial !== request) return;
      loaded.push(...page);
      if (page.length < 100) break;
    }
    words = loaded; render();
  } catch (error) {
    if (serial !== request) return;
    if (error.status === 401) { location.replace('/login.html'); return; }
    $('course-words-error-text').textContent = describeApiError(error);
    $('course-words-error').hidden = false;
  } finally {
    if (serial === request) $('course-words-loading').hidden = true;
  }
}

mountWorkspace('course-words');
$('word-course').addEventListener('change', load);
$('course-word-search').addEventListener('input', render);
$('course-words-retry').addEventListener('click', load);
load();
