import { listCourses, listCourseWords, listVocabulary, addVocabulary, createFlashcardSession } from './api.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { describeApiError } from './errors.js';
import { normalizeAnswer, shuffleCopy } from './practice-utils.js';

const $ = (id) => document.getElementById(id);
const state = { words: [], courses: [], saved: new Set(), selected: new Set(), level: '', loading: false, starting: false };
const requestedCourse = new URLSearchParams(location.search).get('courseId');
function feedback(text = '', isError = false) {
  $('library-feedback').textContent = text;
  $('library-feedback').classList.toggle('is-error', isError);
}
function matchingWords() {
  const courseId = $('library-course').value;
  const query = normalizeAnswer($('library-search').value);
  const matches = state.words.filter((word) => {
    const course = state.courses.find((item) => item.id === word.courseId);
    return (!courseId || word.courseId === courseId) && (!state.level || course?.level === state.level)
      && (!query || normalizeAnswer(`${word.word} ${word.translation} ${word.example}`).includes(query));
  });
  return matches.sort((a, b) => ($('library-sort').value === 'za' ? -1 : 1) * a.word.localeCompare(b.word, 'en'));
}
function candidates() {
  return state.selected.size ? state.words.filter((word) => state.selected.has(word.id)) : matchingWords();
}
function updateSelection() {
  $('library-selected-count').textContent = String(state.selected.size);
  const count = Math.min(Number($('library-limit').value) || 10, 50, candidates().length);
  $('library-session-count').textContent = `${count} ${count === 1 ? 'word' : 'words'} from ${state.selected.size ? 'your selection' : 'the current filters'}.`;
  $('library-start').disabled = state.starting || count === 0;
}
function listen(text) {
  if (!('speechSynthesis' in window)) { feedback('Word playback is unavailable in this browser.', true); return; }
  window.speechSynthesis.cancel();
  const voice = new SpeechSynthesisUtterance(text);
  voice.lang = 'en-US'; voice.rate = .85;
  voice.onerror = () => feedback('Word playback is unavailable on this device.', true);
  window.speechSynthesis.speak(voice);
}
function renderWords() {
  const target = $('library-words');
  const words = matchingWords();
  $('library-visible-count').textContent = `${words.length} ${words.length === 1 ? 'word' : 'words'} found`;
  target.replaceChildren();
  if (!words.length) {
    const empty = el('div', 'library-empty');
    empty.append(el('h3', undefined, 'A new word is around the corner.'), el('p', undefined, 'Try a different course, level or search. Some courses do not have a word collection yet.'));
    target.append(empty);
  }
  for (const word of words) {
    const row = el('article', `library-word${state.selected.has(word.id) ? ' is-selected' : ''}`);
    const checkbox = el('input'); checkbox.type = 'checkbox'; checkbox.checked = state.selected.has(word.id);
    checkbox.setAttribute('aria-label', `Select ${word.word}`);
    checkbox.addEventListener('change', () => {
      if (checkbox.checked && state.selected.size >= 50) { checkbox.checked = false; feedback('Choose up to 50 words for one session.', true); return; }
      if (checkbox.checked) state.selected.add(word.id); else state.selected.delete(word.id);
      row.classList.toggle('is-selected', checkbox.checked); updateSelection();
    });
    const speak = el('button', 'word-speak', '◖))'); speak.type = 'button'; speak.setAttribute('aria-label', `Listen to ${word.word}`);
    speak.addEventListener('click', () => listen(word.word));
    const copy = el('div', 'word-copy'); copy.append(el('h3', undefined, word.word));
    const translation = el('div', 'library-translation'); translation.append(el('p', undefined, word.translation));
    if (word.example) translation.append(el('small', undefined, word.example));
    const course = state.courses.find((item) => item.id === word.courseId);
    if (course) { const label = el('span', 'library-word-course'); label.append(el('b', undefined, course.level), el('span', undefined, course.title)); copy.append(label); }
    const saved = state.saved.has(normalizeAnswer(word.word));
    const save = el('button', `lesson-button ${saved ? 'lesson-button-secondary' : 'lesson-button-primary'}`, saved ? '✓ Saved' : '＋ Save');
    save.type = 'button'; save.disabled = saved; save.setAttribute('aria-label', saved ? `${word.word} is in My Words` : `Save ${word.word} to My Words`);
    save.addEventListener('click', async () => {
      save.disabled = true;
      try {
        try { await addVocabulary({ word: word.word, translation: word.translation, example: word.example }); }
        catch (error) { if (error.code !== 'WORD_EXISTS') throw error; }
        state.saved.add(normalizeAnswer(word.word)); renderWords(); feedback(`“${word.word}” is in My Words.`);
      } catch (error) { feedback(describeApiError(error), true); save.disabled = false; }
    });
    row.append(checkbox, speak, copy, translation, save); target.append(row);
  }
  updateSelection();
}
async function allPages(loadPage) {
  const result = [];
  for (let offset = 0; ; offset += 100) {
    const page = await loadPage(offset); result.push(...page);
    if (page.length < 100) return result;
  }
}
async function load() {
  if (state.loading) return;
  state.loading = true; $('library-error').hidden = true; $('library-loading').hidden = false;
  try {
    const user = await requireSession({ throwOnUnavailable: true }); if (!user) return;
    setWorkspaceUser(user);
    const [courses, words, personal] = await Promise.all([listCourses(), allPages((offset) => listCourseWords({ offset })), allPages((offset) => listVocabulary(offset))]);
    state.courses = courses; state.words = words; state.saved = new Set(personal.map((word) => normalizeAnswer(word.word)));
    const select = $('library-course'); select.replaceChildren(); const all = el('option', undefined, 'All courses'); all.value = ''; select.append(all);
    for (const course of courses) { const option = el('option', undefined, `${course.level} · ${course.title}`); option.value = course.id; select.append(option); }
    if (requestedCourse && courses.some((course) => course.id === requestedCourse)) select.value = requestedCourse;
    $('library-total').textContent = String(words.length); $('library-course-count').textContent = String(courses.length);
    $('library-content').hidden = false; renderWords();
  } catch (error) {
    if (error.status === 401) { location.replace('/login.html'); return; }
    $('library-error-text').textContent = describeApiError(error); $('library-error').hidden = false;
  } finally { state.loading = false; $('library-loading').hidden = true; }
}
mountWorkspace('courseWords');
$('library-retry').addEventListener('click', load);
$('library-search').addEventListener('input', renderWords); $('library-sort').addEventListener('change', renderWords);
$('library-course').addEventListener('change', () => { state.selected.clear(); renderWords(); });
for (const button of document.querySelectorAll('[data-level]')) button.addEventListener('click', () => {
  state.level = button.dataset.level; state.selected.clear();
  for (const node of document.querySelectorAll('[data-level]')) node.setAttribute('aria-pressed', String(node === button));
  renderWords();
});
$('library-select').addEventListener('click', () => { state.selected = new Set(matchingWords().slice(0, 50).map((word) => word.id)); renderWords(); });
$('library-clear').addEventListener('click', () => { state.selected.clear(); renderWords(); });
$('library-limit').addEventListener('input', updateSelection);
$('library-start-form').addEventListener('submit', async (event) => {
  event.preventDefault(); if (state.starting || !$('library-start-form').reportValidity()) return;
  let words = candidates(); if ($('library-shuffle').checked) words = shuffleCopy(words);
  words = words.slice(0, Number($('library-limit').value)); if (!words.length) return;
  state.starting = true; updateSelection(); feedback();
  try {
    const session = await createFlashcardSession({ source: 'course_words', limit: words.length, wordIds: words.map((word) => word.id) });
    location.assign(`/practice.html?${new URLSearchParams({ session: session.sessionId, mode: $('library-mode').value })}`);
  } catch (error) { feedback(describeApiError(error), true); state.starting = false; updateSelection(); }
});
load();

for (const link of document.querySelectorAll('a[href="#library-builder"]')) link.addEventListener('click', () => { $('library-builder').open = true; });
