import { elapsedSeconds, TestCompletionScreen } from './test-completion.js';
import { addVocabulary, deleteVocabulary, getVocabularyGroups, listVocabulary, reviewVocabulary, updateVocabulary } from './api.js';
import { el } from './layout.js';
import { t, tn } from './i18n.js';
import { describeApiError } from './errors.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { letterTiles } from './letter-tiles.js';
import { autoCheckText } from './auto-check.js';

const $ = (id) => document.getElementById(id);
const taskTypes = ['flashcards', 'choice', 'write', 'letters'];
const initialMode = new URLSearchParams(location.search).get('mode');
const state = {
  words: [], groups: [], course: '', lesson: '', expanded: new Set(), filter: 'all',
  mode: initialMode === 'mixed' || taskTypes.includes(initialMode) ? 'mixed' : 'list',
  loading: false, busy: false, request: 0, session: null, storageKey: null, reviewError: '',
};
const normalize = (value) => value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('en');
const isDue = (word) => new Date(word.dueAt).getTime() <= Date.now();

function control(text, action, className = 'lesson-button lesson-button-secondary') {
  const node = el('button', className, text);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}

function feedback(text = '', error = false) {
  $('word-feedback').textContent = text;
  $('word-feedback').classList.toggle('is-error', error);
}

function speak(word) {
  if (!('speechSynthesis' in window)) {
    feedback(t('vocab.noSpeech'), true);
    return;
  }
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(word);
  utterance.lang = 'en-US';
  utterance.rate = .85;
  utterance.onerror = () => feedback(t('vocab.speechFailed'), true);
  speechSynthesis.speak(utterance);
}

function speakButton(word) {
  const node = control('', () => speak(word), 'word-speak');
  node.setAttribute('aria-label', t('vocab.listen', { word }));
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', 'M11 5 6 9H3v6h3l5 4V5ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14');
  svg.append(path);
  node.append(svg);
  return node;
}

function filteredWords() {
  const query = normalize($('word-search').value);
  return state.words.filter((word) => (
    (state.filter === 'all' || (state.filter === 'learned' ? word.learned : state.filter === 'learning' ? !word.learned : isDue(word))) &&
    (!state.course || word.courseId === state.course) &&
    (!state.lesson || word.lessonId === state.lesson) &&
    (!query || normalize(`${word.word} ${word.translation} ${word.example}`).includes(query))
  ));
}

/** Courses/lessons that hold words, in curriculum order (server groups), else first-seen order. */
function sourceGroups() {
  if (state.groups.length) return state.groups;
  const courses = new Map();
  for (const word of state.words) {
    if (!word.courseId) continue;
    if (!courses.has(word.courseId)) courses.set(word.courseId, { id: word.courseId, title: word.courseTitle || '', lessons: [] });
    const course = courses.get(word.courseId);
    if (word.lessonId && !course.lessons.some((lesson) => lesson.id === word.lessonId)) course.lessons.push({ id: word.lessonId, title: word.lessonTitle || '' });
  }
  return [...courses.values()];
}

function option(value, label) {
  const node = el('option', undefined, label);
  node.value = value;
  return node;
}

function renderSourceFilters() {
  const groups = sourceGroups();
  const courseSelect = $('word-course');
  const lessonSelect = $('word-lesson');
  if (!groups.some((course) => course.id === state.course)) state.course = '';
  courseSelect.replaceChildren(option('', t('vocab.allCourses')), ...groups.map((course) => option(course.id, course.title)));
  courseSelect.value = state.course;
  courseSelect.disabled = !groups.length;
  const lessons = groups.find((course) => course.id === state.course)?.lessons ?? [];
  if (!lessons.some((lesson) => lesson.id === state.lesson)) state.lesson = '';
  lessonSelect.replaceChildren(option('', t('vocab.allLessons')), ...lessons.map((lesson) => option(lesson.id, lesson.title)));
  lessonSelect.value = state.lesson;
  lessonSelect.disabled = !lessons.length;
}

function onSourceChange(courseChanged) {
  if (state.busy) return;
  state.course = $('word-course').value;
  state.lesson = courseChanged ? '' : $('word-lesson').value;
  renderSourceFilters();
  renderWords();
}

function renderStats() {
  const stats = [[t('vocab.saved'), state.words.length], [t('vocab.learning'), state.words.filter((w) => !w.learned).length], [t('vocab.learned'), state.words.filter((w) => w.learned).length], [t('vocab.due'), state.words.filter(isDue).length]];
  $('words-stats').replaceChildren(...stats.map(([label, value]) => {
    const card = el('div', 'word-stat');
    const copy = el('div');
    copy.append(el('strong', undefined, String(value)), el('span', undefined, label));
    card.append(copy);
    return card;
  }));
}

function empty(target, title, description) {
  const card = el('div', 'word-empty');
  card.append(el('h2', undefined, title), el('p', 'dashboard-muted', description));
  target.replaceChildren(card);
  return card;
}

function updateWord(updated) {
  const index = state.words.findIndex((word) => word.id === updated.id);
  if (index !== -1) state.words[index] = updated;
  renderStats();
}

function renderWords() {
  const words = filteredWords();
  const target = $('word-list');
  target.replaceChildren();
  $('word-count').textContent = tn('vocab.count', words.length);
  if (!words.length) {
    const card = empty(target, state.words.length ? t('vocab.noMatch') : t('vocab.emptyTitle'), state.words.length ? t('vocab.noMatchText') : t('vocab.emptyText'));
    if (!state.words.length) {
      const actions = el('div', 'word-practice-actions');
      const courses = el('a', 'lesson-button lesson-button-primary', t('vocab.goToCourses'));
      courses.href = '/courses.html';
      actions.append(courses, control(t('vocab.addFirst'), openAddDialog));
      card.append(actions);
    }
    return;
  }
  for (const word of words) {
    const row = el('article', 'word-row');
    const copy = el('div', 'word-copy');
    const title = el('h3', undefined, word.word);
    if (word.pronunciation) title.append(el('span', 'word-pronunciation', ` ${word.pronunciation}`));
    copy.append(title, el('p', undefined, word.translation));
    if (word.courseTitle || word.lessonTitle) {
      copy.append(el('small', 'word-source', [word.courseTitle, word.lessonTitle].filter(Boolean).join(' · ')));
    }
    const open = state.expanded.has(word.id);
    const details = el('div', 'word-details');
    details.id = `word-details-${word.id}`;
    details.hidden = !open;
    details.append(el('p', 'word-detail-label', t('vocab.example')), el('p', 'word-example', word.example || t('vocab.noExample')));
    if (word.lessonSlug) {
      const link = el('a', 'dashboard-text-button', t('vocab.openLesson', { lesson: word.lessonTitle || word.lessonSlug }));
      link.href = `/lesson.html?slug=${encodeURIComponent(word.lessonSlug)}`;
      details.append(link);
    }
    details.append(el('p', 'dashboard-muted', word.source === 'lesson' ? t('vocab.fromLesson') : t('vocab.addedByYou')));
    const more = control(open ? t('vocab.hideDetails') : t('vocab.details'), () => {
      if (state.expanded.has(word.id)) state.expanded.delete(word.id); else state.expanded.add(word.id);
      renderWords();
    }, 'word-details-toggle');
    more.setAttribute('aria-expanded', String(open));
    more.setAttribute('aria-controls', details.id);
    copy.append(more, details);
    const status = el('span', `word-status${word.learned ? ' is-learned' : ''}`, word.learned ? `✓ ${t('vocab.learned')}` : isDue(word) ? t('vocab.due') : t('vocab.learning'));
    const actions = el('div', 'word-row-actions');
    const toggle = control(word.learned ? t('vocab.keepLearning') : t('vocab.markLearned'), async () => {
      toggle.disabled = true;
      try {
        updateWord(await updateVocabulary(word.id, !word.learned));
        renderWords();
        feedback(t('vocab.updated'));
      } catch (error) {
        feedback(describeApiError(error), true);
        toggle.disabled = false;
      }
    });
    const remove = control(t('vocab.remove'), async () => {
      if (!window.confirm(t('vocab.removeConfirm', { word: word.word }))) return;
      remove.disabled = true;
      try {
        await deleteVocabulary(word.id);
        state.words = state.words.filter((item) => item.id !== word.id);
        state.session = reconcilePractice(state.session);
        savePractice();
        state.expanded.delete(word.id);
        renderStats();
        renderWords();
        feedback(t('vocab.removed'));
      } catch (error) {
        feedback(describeApiError(error), true);
        remove.disabled = false;
      }
    }, 'lesson-button lesson-button-secondary word-remove');
    actions.append(toggle, control(t('vocab.practise'), () => setMode('mixed', word.id), 'lesson-button lesson-button-primary'), remove);
    row.append(speakButton(word.word), copy, status, actions);
    target.append(row);
  }
}

function setControlsDisabled(disabled) {
  for (const node of document.querySelectorAll('[data-mode], [data-filter], #word-search, #add-word')) node.disabled = disabled;
}

function shuffle(items) {
  const result = [...items];
  for (let index = result.length - 1; index > 0; index--) {
    const swap = Math.floor(Math.random() * (index + 1));
    [result[index], result[swap]] = [result[swap], result[index]];
  }
  return result;
}

function translations() {
  return [...new Map(state.words.map((word) => [normalize(word.translation), word.translation])).values()];
}

function availableTypes(word, canChoose) {
  return taskTypes.filter((type) => (type !== 'choice' || canChoose)
    && (type !== 'letters' || /^[a-zA-Z]{2,24}$/.test(word.word)));
}

function practiceSelection() {
  return JSON.stringify([state.filter, state.course, state.lesson, normalize($('word-search').value)]);
}

function savePractice() {
  if (!state.storageKey) return;
  try { window.sessionStorage.setItem(state.storageKey, JSON.stringify(state.session)); }
  catch { /* Practice is still available in memory. */ }
}

function reconcilePractice(session) {
  if (!Array.isArray(session?.tasks) || !Array.isArray(session.queue)
      || !Array.isArray(session.mistakes)) return null;
  const words = new Map(state.words.map((word) => [word.id, word]));
  const canChoose = translations().length > 1;
  const tasks = new Map(session.tasks.filter(({ wordId }) => words.has(wordId)).map((task) => {
    const types = availableTypes(words.get(task.wordId), canChoose);
    return [task.wordId, { ...task, type: types.includes(task.type) ? task.type : 'flashcards' }];
  }));
  if (!tasks.size) return null;
  const queue = [...new Set(session.queue)].filter((id) => tasks.has(id));
  if (!queue.length && session.finishedAt == null) return null;
  const pending = session.pending && session.pending.wordId === queue[0] ? session.pending : null;
  return { ...session, tasks: [...tasks.values()], queue, pending };
}

function restorePractice() {
  try { return reconcilePractice(JSON.parse(window.sessionStorage.getItem(state.storageKey))); }
  catch { return null; }
}

function startPractice(firstId, selectedIds) {
  // Replay the same words even after review changes the due filter.
  const selected = selectedIds ? state.words.filter((word) => selectedIds.includes(word.id)) : filteredWords();
  const canChoose = translations().length > 1;
  const counts = new Map(taskTypes.map((type) => [type, 0]));
  const candidates = shuffle(selected).map((word) => ({ wordId: word.id, types: shuffle(availableTypes(word, canChoose)) }));
  // Allocate constrained words first so their limited types do not crowd out the others.
  candidates.sort((a, b) => a.types.length - b.types.length);
  const tasks = shuffle(candidates.map(({ wordId, types }) => {
    const type = selected.length === 1 ? 'flashcards'
      : types.reduce((best, candidate) => counts.get(candidate) < counts.get(best) ? candidate : best);
    counts.set(type, counts.get(type) + 1);
    return { wordId, type };
  }));
  const queue = tasks.map(({ wordId }) => wordId);
  if (firstId && queue.includes(firstId)) queue.unshift(...queue.splice(queue.indexOf(firstId), 1));
  const previous = state.session;
  const previousErrors = { ...previous?.previousErrors };
  if (previous?.finishedAt != null) {
    for (const id of previous.mistakes) {
      previousErrors[id] = [...(previousErrors[id] ?? []), ...(previous.errors?.[id] ?? [])];
    }
  }
  state.session = {
    tasks, queue, selection: practiceSelection(), mistakes: [], incorrect: 0,
    startedAt: Date.now(), finishedAt: null, pending: null, lastMistake: null,
    previousErrors,
  };
  state.reviewError = '';
  savePractice();
  renderPractice();
}

function reviewErrors(errors) {
  return errors?.map((error) => ({
    ...error, answer: error.selfRated ? t('vocab.needPractice') : error.answer,
  })).filter((error) => error.answer != null || error.expected != null);
}

function renderSummary(target) {
  const { tasks, mistakes, incorrect, finishedAt, startedAt, errors = {}, previousErrors = {} } = state.session;
  const ids = tasks.map(({ wordId }) => wordId);
  const wrong = mistakes.filter((id) => ids.includes(id));
  const words = new Map(state.words.map((word) => [word.id, word]));
  const heading = TestCompletionScreen(target, {
    headingId: 'practice-summary-title',
    title: t('vocab.complete'),
    subtitle: t('vocab.mixedTitle'),
    correct: ids.length,
    total: ids.length,
    firstTry: ids.length - wrong.length,
    mistakes: wrong.length,
    retries: mistakes.length === wrong.length ? incorrect : undefined,
    seconds: elapsedSeconds(startedAt, finishedAt),
    items: tasks.map(({ wordId: id, type }) => ({
      title: words.get(id).word,
      expected: type === 'letters' || type === 'write' ? words.get(id).word : words.get(id).translation,
      mistake: wrong.includes(id),
      errors: reviewErrors(errors[id]),
    })),
    previousItems: Object.entries(previousErrors).filter(([id]) => words.has(id)).map(([id, history]) => ({
      title: words.get(id).word, mistake: true, errors: reviewErrors(history),
    })),
    retryMistakes: wrong.length ? () => startPractice(undefined, wrong) : undefined,
    tryAgain: () => startPractice(undefined, ids),
    finish: () => setMode('list'),
    backToCourses: true,
  });
  heading.focus();
}

function setMode(mode, firstId, startAgain = false) {
  if (state.busy) return;
  state.mode = mode;
  const url = new URL(location.href);
  url.searchParams.delete('word');
  if (mode === 'list') url.searchParams.delete('mode');
  else url.searchParams.set('mode', mode);
  history.replaceState(null, '', url);
  for (const node of document.querySelectorAll('[data-mode]')) node.setAttribute('aria-pressed', String(node.dataset.mode === mode));
  for (const node of document.querySelectorAll('.sidebar-link[data-section]')) {
    const selected = node.dataset.section === 'words';
    node.classList.toggle('active', selected);
    if (selected) node.setAttribute('aria-current', 'page');
    else node.removeAttribute('aria-current');
  }
  $('word-list-panel').hidden = mode !== 'list';
  $('word-toolbar').hidden = mode !== 'list';
  $('word-practice-panel').hidden = mode === 'list';
  feedback();
  if (mode === 'list') renderWords();
  else if (firstId || startAgain || !state.session?.tasks.length) startPractice(firstId);
  else {
    renderPractice();
    if (state.session.pending) void saveReview();
  }
}

async function saveReview() {
  const session = state.session;
  const pending = session?.pending;
  if (!pending || state.busy) return;
  state.busy = true;
  state.reviewError = '';
  setControlsDisabled(true);
  renderPractice();
  try {
    const { wordId, remembered, attemptId } = pending;
    const updated = await reviewVocabulary(wordId, remembered, attemptId);
    if (state.session !== session) return;
    updateWord(updated);
    session.queue.shift();
    session.lastMistake = remembered ? null : wordId;
    if (!remembered) {
      session.queue.push(wordId);
      session.incorrect++;
      session.errors ??= {};
      (session.errors[wordId] ??= []).push({
        answer: pending.answer,
        selfRated: pending.answer == null && pending.expected != null,
        expected: pending.expected,
      });
      if (!session.mistakes.includes(wordId)) session.mistakes.push(wordId);
    }
    session.pending = null;
    if (!session.queue.length) session.finishedAt = Date.now();
    savePractice();
  } catch (error) {
    if (state.session === session) state.reviewError = describeApiError(error);
  } finally {
    if (state.session === session) {
      state.busy = false;
      setControlsDisabled(false);
      renderPractice(true);
    }
  }
}

function renderPractice(focus = false) {
  const target = $('word-practice');
  target.replaceChildren();
  const session = state.session;
  if (!session?.tasks.length) {
    empty(target, t('vocab.noActivityWords'), t('vocab.beginHint'));
    return;
  }
  if (!session.queue.length && session.finishedAt != null) {
    renderSummary(target);
    return;
  }
  if (!session.queue.length) {
    empty(target, t('vocab.noActivityWords'), t('vocab.beginHint'));
    return;
  }
  const task = session.tasks.find(({ wordId }) => wordId === session.queue[0]);
  const word = state.words.find((item) => item.id === task.wordId);
  const { type } = task;
  const total = session.tasks.length;
  const correct = total - session.queue.length;
  const incorrect = session.incorrect;
  const modeLabels = { flashcards: t('vocab.modeFlash'), choice: t('vocab.modeChoice'), write: t('vocab.modeWrite'), letters: t('vocab.modeLetters') };
  const title = el('h2', undefined, t('vocab.mixedTitle'));
  title.tabIndex = -1;
  const meta = el('div', 'word-practice-meta');
  meta.append(el('span', undefined, modeLabels[type]), el('span', undefined, `${correct} / ${total}`));
  const track = el('div', 'word-run-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', t('vocab.runLabel'));
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', String(total));
  track.setAttribute('aria-valuenow', String(correct));
  const fill = el('span');
  fill.style.width = `${correct / total * 100}%`;
  track.append(fill);
  const card = el('div', 'word-practice-card');
  card.dataset.taskType = type;
  card.dataset.wordId = word.id;
  const heading = el('h2', undefined, type === 'write' || type === 'letters' ? word.translation : word.word);
  card.append(el('span', 'lesson-chip', type === 'flashcards' ? t('vocab.wordCard') : t('vocab.practiceChip')), heading);
  const result = el('p', 'word-practice-result');
  result.setAttribute('role', 'status');
  const actions = el('div', 'word-practice-actions');
  target.append(title, meta, track, el('p', 'dashboard-muted', t('vocab.mixedCounts', { correct, incorrect })));
  const mistake = state.words.find((item) => item.id === session.lastMistake);
  if (mistake) {
    const note = el('p', 'word-practice-result is-error', t('vocab.mixedCorrection', {
      word: mistake.word, translation: mistake.translation,
    }));
    note.setAttribute('role', 'status');
    target.append(note);
  }
  target.append(card);
  if (focus) title.focus();

  if (session.pending) {
    result.textContent = state.reviewError ? t('vocab.notSaved', { error: state.reviewError }) : t('vocab.mixedSaving');
    if (state.reviewError) result.classList.add('is-error');
    card.append(result);
    if (!state.busy) card.append(control(t('common.tryAgain'), saveReview));
    return;
  }

  function grade(remembered, answer, expected) {
    if (state.busy || state.loading || state.mode !== 'mixed' || state.session !== session
        || session.queue[0] !== word.id || session.pending || incorrect !== session.incorrect) return;
    session.pending = { wordId: word.id, remembered, answer, expected, attemptId: crypto.randomUUID() };
    savePractice();
    void saveReview();
  }

  if (type === 'flashcards') {
    heading.className = 'sr-only';
    const flip = control('', () => turnCard(!revealed), 'flashcard-turn');
    flip.setAttribute('aria-pressed', 'false');
    flip.setAttribute('aria-label', t('vocab.revealFor', { word: word.word }));
    const inner = el('span', 'flashcard-inner');
    const front = el('span', 'flashcard-face flashcard-front');
    front.append(el('span', 'flashcard-kicker', t('vocab.english')), el('span', 'flashcard-word', word.word), el('span', 'flashcard-hint', t('vocab.tapReveal')));
    const back = el('span', 'flashcard-face flashcard-back');
    back.setAttribute('aria-hidden', 'true');
    back.append(el('span', 'flashcard-kicker', t('vocab.translation')), el('span', 'flashcard-word', word.translation));
    if (word.example) back.append(el('span', 'flashcard-example', word.example));
    inner.append(front, back);
    flip.append(inner);
    let revealed = false;
    function turnCard(show) {
      if (state.busy || flip.disabled) return;
      revealed = show;
      flip.classList.toggle('is-flipped', show);
      flip.setAttribute('aria-pressed', String(show));
      flip.setAttribute('aria-label', show ? t('vocab.showEnglish') : t('vocab.revealFor', { word: word.word }));
      front.setAttribute('aria-hidden', String(show));
      back.setAttribute('aria-hidden', String(!show));
      if (show) {
        actions.replaceChildren(control(t('vocab.needPractice'), () => grade(false, undefined, word.translation)), control(t('vocab.knewIt'), () => grade(true), 'lesson-button lesson-button-primary'));
        actions.querySelector('button').focus();
      } else actions.replaceChildren(control(t('vocab.reveal'), () => turnCard(true), 'lesson-button lesson-button-primary'));
    }
    card.append(flip, speakButton(word.word), el('p', 'dashboard-muted', t('vocab.thinkFirst')));
    actions.append(control(t('vocab.reveal'), () => turnCard(true), 'lesson-button lesson-button-primary'));
  } else if (type === 'choice') {
    card.append(speakButton(word.word), el('p', 'dashboard-muted', t('vocab.chooseTranslation')));
    const alternatives = translations().filter((translation) => normalize(translation) !== normalize(word.translation));
    const choices = el('div', 'word-choice-list');
    for (const choice of shuffle([word.translation, ...shuffle(alternatives).slice(0, 3)])) choices.append(control(choice, () => grade(choice === word.translation, choice, word.translation), 'word-choice'));
    card.append(choices);
  } else {
    const form = el('form');
    const check = (answer) => grade(normalize(answer) === normalize(word.word), answer, word.word);
    const letters = [...word.word];
    if (type === 'write') {
      const label = el('label', 'lesson-answer-label', t('vocab.typeEnglish'));
      const input = el('input', 'lesson-answer');
      input.required = true;
      input.autocomplete = 'off';
      input.spellcheck = false;
      input.maxLength = 120;
      input.setAttribute('autocapitalize', 'none');
      label.append(input);
      form.append(label);
      form.append(el('p', 'dashboard-muted', t('lesson.autoCheckText')));
      autoCheckText(form, input, check);
    } else {
      const pattern = letters.map((letter, index) => index % 3 === 0 ? letter : '_').join('');
      const bank = shuffle(letters.filter((_, index) => index % 3 !== 0));
      const tiles = letterTiles({ pattern, letters: bank }, '', null, () => {
        const answer = tiles.readAnswer();
        if (answer) check(answer);
      });
      form.append(tiles.field);
    }
    card.append(form);
  }
  card.append(actions);
}

function openAddDialog() {
  if (state.busy) return;
  $('word-form-error').hidden = true;
  $('word-dialog').showModal();
}

async function load() {
  if (state.loading) return;
  state.loading = true;
  const request = ++state.request;
  $('words-error').hidden = true;
  $('words-loading').hidden = false;
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user || request !== state.request) return;
    setWorkspaceUser(user);
    const words = [];
    // Filters only need course/lesson order; the dictionary still works without it.
    const groups = getVocabularyGroups().then((body) => body?.courses ?? [], () => []);
    for (let offset = 0; ; offset += 100) {
      const page = await listVocabulary(offset);
      if (request !== state.request) return;
      words.push(...page);
      if (page.length < 100) break;
    }
    state.words = words;
    state.storageKey = `fleng.mixed-practice.v1:${user.id}`;
    state.session = restorePractice();
    state.busy = false;
    setControlsDisabled(false);
    state.groups = await groups;
    if (request !== state.request) return;
    $('words-content').hidden = false;
    renderStats();
    renderSourceFilters();
    const selectedWord = new URLSearchParams(location.search).get('word');
    setMode(state.mode, words.find((word) => selectedWord && normalize(word.word) === normalize(selectedWord))?.id);
  } catch (error) {
    if (request !== state.request) return;
    $('words-error-text').textContent = describeApiError(error);
    $('words-error').hidden = false;
  } finally {
    if (request === state.request) { state.loading = false; $('words-loading').hidden = true; }
  }
}

mountWorkspace(state.mode === 'list' ? 'words' : 'practice');
$('add-word').addEventListener('click', openAddDialog);
$('word-dialog-close').addEventListener('click', () => $('word-dialog').close());
$('words-retry').addEventListener('click', load);
for (const button of document.querySelectorAll('[data-mode]')) button.addEventListener('click', () => {
  const startAgain = state.mode === 'list' && state.session
    && (state.session.finishedAt !== null || state.session.selection !== practiceSelection());
  setMode(button.dataset.mode, undefined, startAgain);
});
for (const button of document.querySelectorAll('[data-filter]')) button.addEventListener('click', () => {
  if (state.busy) return;
  state.filter = button.dataset.filter;
  for (const node of document.querySelectorAll('[data-filter]')) node.setAttribute('aria-pressed', String(node === button));
  renderWords();
});
$('word-course').addEventListener('change', () => onSourceChange(true));
$('word-lesson').addEventListener('change', () => onSourceChange(false));
$('word-search').addEventListener('input', renderWords);
$('word-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!$('word-form').reportValidity()) return;
  const save = $('word-save');
  save.disabled = true;
  $('word-form-error').hidden = true;
  try {
    const word = await addVocabulary({ word: $('new-word').value.trim(), translation: $('new-translation').value.trim(), example: $('new-example').value.trim() });
    state.words.push(word);
    $('word-dialog').close();
    $('word-form').reset();
    renderStats();
    renderSourceFilters();
    setMode('list');
    feedback(t('vocab.savedWord', { word: word.word }));
  } catch (error) {
    $('word-form-error').textContent = error.code === 'WORD_EXISTS' ? t('errors.WORD_EXISTS') : describeApiError(error);
    $('word-form-error').hidden = false;
  } finally { save.disabled = false; }
});
window.addEventListener('pagehide', () => { if ('speechSynthesis' in window) speechSynthesis.cancel(); });
window.addEventListener('fleng:session-ended', () => {
  state.request++;
  state.words = [];
  state.session = null;
  state.storageKey = null;
  state.busy = false;
  state.loading = false;
  $('words-content').hidden = true;
  $('word-dialog').close();
  if ('speechSynthesis' in window) speechSynthesis.cancel();
});
window.addEventListener('pageshow', (event) => { if (event.persisted) load(); });
load();
