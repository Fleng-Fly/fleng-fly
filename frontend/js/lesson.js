import { getCourse, getLesson, getLessonProgress, getLessonVocabulary, listCourses, startLesson, submitAnswer } from './api.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { t } from './i18n.js';
import { letterTiles } from './letter-tiles.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser, setWorkspaceAIContext } from './workspace.js';

const $ = (id) => document.getElementById(id);
const tabs = ['theory', 'practice', 'vocabulary'];
const requestedTab = queryParam('tab');
const typeLabel = (type) => ['letter_tiles', 'single_choice', 'text', 'self_check'].includes(type) ? t(`lesson.type.${type}`) : type;
const state = {
  lesson: null, progress: null, tab: tabs.includes(requestedTab) ? requestedTab : 'theory', index: 0, busy: false,
  drafts: new Map(), tileDrafts: new Map(), results: new Map(), errors: new Map(),
  vocabulary: { items: [], loaded: false, loading: false, more: false, error: null },
  nextStep: null, nextStepFor: null,
};

function renderTheory(container, theory) {
  container.textContent = '';
  for (const raw of theory.split(/\n\s*\n/)) {
    const block = raw.trim();
    if (!block) continue;
    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean);
    if (lines.every((line) => line.startsWith('- '))) {
      const list = el('ul');
      for (const line of lines) list.append(el('li', undefined, line.slice(2)));
      container.append(list);
    } else if (block.startsWith('## ')) {
      const heading = block.slice(3).trim();
      const key = `lesson.heading.${heading.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '')}`;
      container.append(el('h3', undefined, t(key) === key ? heading : t(key)));
    } else {
      container.append(el('p', undefined, lines.join(' ')));
    }
  }
}

function exerciseState(exercise) {
  return state.progress.exercises.find((item) => item.exerciseId === exercise.id);
}

function exerciseType(exercise) {
  return exercise.letterTiles ? 'letter_tiles' : exercise.type;
}

function nextUnfinished(after = -1) {
  const exercises = state.lesson.exercises;
  const records = new Map(state.progress.exercises.map((record) => [record.exerciseId, record]));
  const indices = exercises.map((_, index) => (after + 1 + index) % exercises.length);
  const unfinished = indices.filter((index) => !records.get(exercises[index].id)?.completed);
  return unfinished.find((index) => !records.get(exercises[index].id)?.attempts)
    ?? unfinished[0] ?? -1;
}

function pct(done, total) {
  return total ? Math.round((done / total) * 100) : 0;
}

function setProgressBar(node, done, total) {
  const percent = pct(done, total);
  node.setAttribute('aria-valuenow', String(percent));
  node.querySelector('.lesson-fill').style.width = `${percent}%`;
}

function showError(error) {
  $('lesson-loading').hidden = true;
  $('lesson-content').hidden = true;
  const box = $('lesson-error');
  box.hidden = false;
  box.replaceChildren(el('h1', undefined, t('lesson.unavailable')), el('p', undefined, describeApiError(error)));
  const retry = el('button', 'lesson-button lesson-button-primary', t('common.tryAgain'));
  retry.type = 'button';
  retry.addEventListener('click', loadLesson);
  const catalog = el('a', 'lesson-button lesson-button-secondary', t('dashboard.browse'));
  catalog.href = '/courses.html';
  box.append(retry, catalog);
}

function renderHero() {
  const { lesson, progress } = state;
  $('lesson-number').textContent = Number.isInteger(lesson.position) ? t('lesson.number', { n: lesson.position }) : t('lesson.numberless');
  $('lesson-level').textContent = lesson.level || t('lesson.courseLesson');
  $('lesson-duration').textContent = lesson.estimatedMinutes ? t('catalog.minutes', { n: lesson.estimatedMinutes }) : t('lesson.selfPaced');
  $('lesson-title').textContent = lesson.title;
  $('lesson-subtitle').textContent = lesson.summary || t('lesson.continuePractice');
  $('lesson-course-link').textContent = lesson.courseTitle;
  $('lesson-course-link').href = `/course.html?slug=${encodeURIComponent(lesson.courseSlug)}`;
  $('lesson-activity-count').textContent = t('lesson.activities', { done: progress.exercisesCompleted, total: progress.exercisesTotal });
  $('lesson-xp').textContent = t('lesson.xpEarned', { xp: progress.xpEarned });
  setProgressBar($('lesson-progress'), progress.exercisesCompleted, progress.exercisesTotal);
  renderCompleted();
  document.title = `${lesson.title} — Fleng`;
}

function renderCompleted() {
  const { progress } = state;
  const completed = $('lesson-completed');
  completed.hidden = !progress.completed;
  if (!progress.completed) return;
  const metrics = el('div', 'lesson-finish-metrics');
  metrics.append(
    el('span', undefined, t('lesson.activities', { done: progress.exercisesCompleted, total: progress.exercisesTotal })),
    el('span', undefined, t('lesson.xpEarned', { xp: progress.xpEarned })),
  );
  const actions = el('div', 'lesson-finish-actions');
  const next = state.nextStep;
  if (next?.href) {
    const go = el('a', 'lesson-button lesson-button-primary', next.label);
    go.href = next.href;
    actions.append(go);
  }
  const course = el('a', 'lesson-button lesson-button-secondary', t('lesson.backToCourse'));
  course.href = $('lesson-course-link').href;
  const words = el('button', 'lesson-button lesson-button-secondary', t('lesson.reviewWords'));
  words.type = 'button';
  words.addEventListener('click', () => switchTab('vocabulary'));
  actions.append(course, words);
  completed.replaceChildren(
    el('strong', undefined, `✦ ${t('lesson.completedTitle')}`),
    el('p', undefined, t('lesson.completedText')),
    metrics,
    actions,
  );
  loadNextStep();
}

/** Real catalog data only: the next lesson of this course, else the next course. */
async function loadNextStep() {
  const { lesson } = state;
  if (!lesson || state.nextStepFor === lesson.slug) return;
  state.nextStepFor = lesson.slug;
  try {
    const course = await getCourse(lesson.courseSlug);
    const position = course.lessons.findIndex((item) => item.slug === lesson.slug);
    const nextLesson = position >= 0 ? course.lessons[position + 1] : null;
    if (nextLesson) {
      state.nextStep = { href: `/lesson.html?slug=${encodeURIComponent(nextLesson.slug)}`, label: t('lesson.nextLesson') };
    } else {
      const all = await listCourses();
      const index = all.findIndex((item) => item.slug === lesson.courseSlug);
      const nextCourse = index >= 0 ? all[index + 1] : null;
      state.nextStep = nextCourse
        ? { href: `/course.html?slug=${encodeURIComponent(nextCourse.slug)}`, label: t('lesson.nextCourse', { title: nextCourse.title }) }
        : null;
    }
  } catch {
    state.nextStep = null; // The completion card still offers the way back to the course.
  }
  if (state.progress?.completed && state.lesson === lesson) renderCompleted();
}

function labelled(label, text) {
  const row = el('p', 'lesson-feedback-line');
  row.append(el('span', 'lesson-feedback-label', `${label}: `), text);
  return row;
}

function feedback(exercise, record) {
  const box = el('div', 'lesson-feedback');
  box.setAttribute('role', 'status');
  box.setAttribute('aria-live', 'polite');
  box.tabIndex = -1;
  const error = state.errors.get(exercise.id);
  if (error) {
    box.classList.add('is-error');
    box.append(el('strong', undefined, error));
    return box;
  }
  const result = state.results.get(exercise.id);
  if (result) {
    const ok = result.isCorrect;
    box.classList.add(ok ? 'is-correct' : 'is-incorrect');
    let headline = exercise.type === 'self_check'
      ? (ok ? t('lesson.selfCorrect') : t('lesson.selfIncorrect'))
      : (ok ? t('lesson.correct') : t('lesson.incorrect'));
    if (result.xpAwarded) headline += ` · +${result.xpAwarded} XP`;
    box.append(el('strong', undefined, headline));
    if (!ok && exercise.type !== 'self_check') box.append(el('p', undefined, t('lesson.mistakeHint')));
    if (!ok && !result.completed) {
      const remaining = state.progress.exercisesTotal - state.progress.exercisesCompleted;
      box.append(el('p', undefined, remaining > 1 ? t('lesson.returnsLater') : t('lesson.tryAgain')));
    }
    if (exercise.type === 'single_choice' && result.correctOptionId) {
      const option = exercise.options?.find((item) => item.id === result.correctOptionId);
      if (option) box.append(labelled(t('lesson.correctAnswer'), option.text));
    }
    if (exercise.type === 'text' && result.acceptedAnswers?.length) {
      box.append(labelled(t('lesson.acceptedAnswer'), result.acceptedAnswers[0]));
    }
    if (result.modelAnswer) box.append(labelled(t('lesson.modelAnswer'), result.modelAnswer));
    if (result.explanation) box.append(labelled(t('lesson.explanation'), result.explanation));
  } else if (record?.attempts) {
    const status = record.completed ? t('lesson.statusDone') : t('lesson.statusSaved');
    box.append(el('strong', undefined, status));
    if (record.answer) {
      const option = exercise.options?.find((item) => item.id === record.answer);
      box.append(labelled(t('lesson.latestAnswer'), option?.text || record.answer));
    }
    if (!record.completed) box.append(el('p', undefined, t('lesson.submitAgain')));
  }
  return box;
}

function markEdited(exercise) {
  state.results.delete(exercise.id);
  state.errors.delete(exercise.id);
  const card = document.querySelector(`[data-exercise-id="${exercise.id}"]`);
  if (card) {
    const box = card.querySelector('.lesson-feedback');
    if (box) box.replaceWith(feedback(exercise, null));
    card.querySelectorAll('.is-correct,.is-incorrect').forEach((node) => node.classList.remove('is-correct', 'is-incorrect'));
  }
}

async function submit(exercise, answer, assessment) {
  if (state.busy) return;
  if (!answer?.trim()) {
    const message = {
      single_choice: t('lesson.needChoice'),
      letter_tiles: t('lesson.needTiles'),
    }[exerciseType(exercise)] || t('lesson.needAnswer');
    state.errors.set(exercise.id, message);
    renderQuestions();
    return;
  }
  state.busy = true;
  let advanced = false;
  $('lesson-last-answer').replaceChildren();
  state.errors.delete(exercise.id);
  setBusy(true);
  const pending = document.querySelector(`[data-exercise-id="${exercise.id}"] .lesson-feedback`);
  if (pending) pending.replaceChildren(el('strong', undefined, t('lesson.checking')));
  try {
    const result = await submitAnswer(state.lesson.slug, {
      exerciseId: exercise.id, answer,
      ...(assessment ? { selfAssessment: assessment } : {}),
    });
    state.progress = result.lesson;
    state.results.set(exercise.id, result);
    state.drafts.set(exercise.id, result.completed ? answer : '');
    state.tileDrafts.delete(exercise.id);
    const next = nextUnfinished(state.index);
    if (next !== -1 && next !== state.index) {
      const review = feedback(exercise, null);
      review.prepend(el('p', 'lesson-muted', exercise.prompt));
      $('lesson-last-answer').append(review);
      state.index = next;
      advanced = true;
    }
    renderHero();
    renderPreview();
  } catch (error) {
    if (error?.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    state.errors.set(exercise.id, describeApiError(error));
  } finally {
    state.busy = false;
    renderQuestions();
    setBusy(false);
    const card = document.querySelector(`[data-exercise-id="${exercise.id}"]`);
    if (advanced) $(`panel-${state.tab}`).querySelector('h2')?.focus();
    else card?.querySelector('.lesson-feedback')?.focus();
  }
}

function setBusy(busy) {
  document.querySelectorAll('.lesson-tabs button, #template-preview button, .lesson-answer-form button, .lesson-answer-form input, .lesson-answer-form textarea, .lesson-question-navigation button').forEach((button) => {
    if (busy) {
      button.dataset.disabledBeforeSubmit = String(button.disabled);
      button.disabled = true;
    } else if (button.dataset.disabledBeforeSubmit !== undefined) {
      button.disabled = button.dataset.disabledBeforeSubmit === 'true';
      delete button.dataset.disabledBeforeSubmit;
    }
  });
}

function questionCard(exercise, index) {
  const record = exerciseState(exercise);
  const result = state.results.get(exercise.id);
  const card = el('article', 'lesson-card lesson-question lesson-reveal');
  card.dataset.exerciseId = exercise.id;
  const meta = el('div', 'lesson-question-meta');
  meta.append(el('span', 'lesson-chip', t('lesson.questionOf', { n: index + 1, total: state.lesson.exercises.length })), el('span', undefined, `${typeLabel(exerciseType(exercise))} · ${exercise.points} XP`));
  card.append(meta);
  const track = el('div', 'lesson-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', t('lesson.questionsDone'));
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.append(el('span', 'lesson-fill'));
  card.append(track);
  setProgressBar(track, state.progress.exercisesCompleted, state.progress.exercisesTotal);
  const prompt = el('h2', undefined, exercise.prompt);
  prompt.tabIndex = -1;
  card.append(prompt);
  const instructionKey = `lesson.instruction.${exerciseType(exercise)}`;
  if (t(instructionKey) !== instructionKey) card.append(el('p', 'lesson-instruction', t(instructionKey)));
  const form = el('form', 'lesson-answer-form');
  let readAnswer;
  if (exercise.type === 'single_choice') {
    const field = el('fieldset', 'lesson-options');
    field.append(el('legend', 'sr-only', t('lesson.chooseOne')));
    let optionIndex = 0;
    for (const option of exercise.options || []) {
      const label = el('label', 'lesson-option');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `answer-${exercise.id}`;
      input.value = option.id;
      input.checked = (state.drafts.has(exercise.id) ? state.drafts.get(exercise.id) : record?.answer) === option.id;
      input.addEventListener('change', () => { state.drafts.set(exercise.id, input.value); markEdited(exercise); });
      label.append(input, el('span', 'lesson-option-key', String.fromCharCode(65 + optionIndex++)), el('span', 'lesson-option-text', option.text));
      if (result?.correctOptionId === option.id) label.classList.add('is-correct');
      else if (result && !result.isCorrect && input.checked) label.classList.add('is-incorrect');
      field.append(label);
    }
    form.append(field);
    readAnswer = () => field.querySelector('input:checked')?.value || '';
  } else if (exercise.letterTiles) {
    const tiles = letterTiles(
      exercise.letterTiles,
      state.drafts.get(exercise.id),
      state.tileDrafts.get(exercise.id),
      (positions) => {
        state.tileDrafts.set(exercise.id, positions);
        markEdited(exercise);
      },
    );
    form.append(tiles.field);
    readAnswer = tiles.readAnswer;
  } else if (exercise.type === 'text' || exercise.type === 'self_check') {
    const label = el('label', 'lesson-answer-label', t('lesson.yourAnswer'));
    const input = document.createElement(exercise.type === 'text' ? 'input' : 'textarea');
    input.className = 'lesson-answer';
    if (input.tagName === 'INPUT') input.type = 'text';
    else input.rows = 4;
    input.maxLength = 2000;
    input.autocomplete = 'off';
    input.value = state.drafts.has(exercise.id) ? state.drafts.get(exercise.id) : record?.answer || '';
    input.addEventListener('input', () => { state.drafts.set(exercise.id, input.value); markEdited(exercise); });
    if (result) input.classList.add(result.isCorrect ? 'is-correct' : 'is-incorrect');
    label.append(input);
    form.append(label);
    readAnswer = () => input.value;
  } else {
    form.append(el('p', 'lesson-muted', t('lesson.unsupported')));
  }
  const actions = el('div', 'lesson-answer-actions');
  if (exercise.type === 'self_check') {
    for (const [assessment, title] of [['correct', t('lesson.gotRight')], ['incorrect', t('lesson.needPractice')]]) {
      const button = el('button', 'lesson-button lesson-button-secondary', title);
      button.type = 'button';
      button.addEventListener('click', () => submit(exercise, readAnswer(), assessment));
      actions.append(button);
    }
  } else if (readAnswer) {
    const button = el('button', 'lesson-button lesson-button-primary', t('lesson.check'));
    button.type = 'submit';
    actions.append(button);
    form.addEventListener('submit', (event) => { event.preventDefault(); submit(exercise, readAnswer()); });
  }
  form.append(actions);
  card.append(form, feedback(exercise, record));
  const nav = el('div', 'lesson-question-navigation');
  const previous = el('button', 'lesson-button lesson-button-secondary', `← ${t('lesson.previous')}`);
  previous.type = 'button';
  previous.disabled = index === 0;
  previous.addEventListener('click', () => goQuestion(index - 1, state.tab));
  const next = el('button', 'lesson-button lesson-button-primary', `${t('lesson.next')} →`);
  next.type = 'button';
  next.disabled = index === state.lesson.exercises.length - 1;
  next.addEventListener('click', () => goQuestion(index + 1, state.tab));
  nav.append(previous, el('span', undefined, t('lesson.savedWhenChecked')), next);
  card.append(nav);
  return card;
}

function renderQuestions() {
  if (!state.lesson) return;
  const practice = $('panel-practice');
  practice.textContent = '';
  const exercises = state.lesson.exercises;
  if (!exercises.length) {
    const empty = el('div', 'lesson-card lesson-empty');
    empty.append(el('h2', undefined, t('lesson.noActivities')), el('p', undefined, t('lesson.noActivitiesText')));
    practice.append(empty);
    return;
  }
  if (state.tab === 'practice') {
    practice.append(questionCard(exercises[state.index], state.index));
  }
}

function goQuestion(index, tab = 'practice') {
  if (state.busy || index < 0 || index >= state.lesson.exercises.length) return;
  state.index = index;
  switchTab(tab);
  $(`panel-${tab}`).querySelector('h2')?.focus();
  renderPreview();
}

function renderPreview() {
  const { lesson, progress } = state;
  const target = $('template-preview');
  target.textContent = '';
  if (!lesson.exercises.length) {
    target.append(el('p', 'lesson-muted', t('lesson.noActivities')));
    return;
  }
  const mini = el('div', 'template-mini');
  const meta = el('div', 'template-mini-meta');
  meta.append(el('span', undefined, t('lesson.questionOf', { n: state.index + 1, total: lesson.exercises.length })), el('span', undefined, t('lesson.nComplete', { n: progress.exercisesCompleted })));
  mini.append(meta, el('p', undefined, lesson.exercises[state.index].prompt));
  const bar = el('div', 'lesson-track');
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', t('lesson.questionsDone'));
  bar.setAttribute('aria-valuemin', '0');
  bar.setAttribute('aria-valuemax', '100');
  bar.append(el('span', 'lesson-fill'));
  setProgressBar(bar, progress.exercisesCompleted, progress.exercisesTotal);
  mini.append(bar);
  const questions = el('div', 'template-questions');
  for (let index = 0; index < lesson.exercises.length; index++) {
    const button = el('button', exerciseState(lesson.exercises[index])?.completed ? 'is-done' : '', String(index + 1));
    button.type = 'button';
    button.setAttribute('aria-label', t('lesson.openQuestion', { n: index + 1 }));
    if (index === state.index) button.setAttribute('aria-current', 'step');
    button.addEventListener('click', () => goQuestion(index));
    questions.append(button);
  }
  mini.append(questions);
  target.append(mini);
}

function switchTab(tab) {
  if (!tabs.includes(tab) || state.busy) return;
  state.tab = tab;
  const url = new URL(window.location.href);
  if (tab === 'theory') url.searchParams.delete('tab');
  else url.searchParams.set('tab', tab);
  window.history.replaceState(window.history.state, '', url);
  $('lesson-last-answer').replaceChildren();
  for (const name of tabs) {
    const active = name === tab;
    $(`tab-${name}`).setAttribute('aria-selected', String(active));
    $(`tab-${name}`).tabIndex = active ? 0 : -1;
    $(`panel-${name}`).hidden = !active;
  }
  renderQuestions();
  if (tab === 'vocabulary' && !state.vocabulary.loaded && !state.vocabulary.loading) loadVocabulary();
}

function renderVocabulary() {
  const target = $('panel-vocabulary');
  const data = state.vocabulary;
  target.textContent = '';
  const card = el('div', 'lesson-card');
  card.append(el('h2', undefined, t('lesson.tabVocabulary')), el('p', 'lesson-muted', t('lesson.vocabHint')));
  if (data.loading && !data.items.length) card.append(el('p', undefined, t('common.loading')));
  if (!data.loading && !data.items.length && !data.error) card.append(el('p', undefined, t('lesson.noWords')));
  const list = el('div', 'lesson-word-list');
  for (const item of data.items) {
    const word = el('article', 'lesson-word');
    const heading = el('h3');
    heading.append(el('span', undefined, item.word), el('span', 'lesson-chip', item.learned ? t('lesson.learned') : t('lesson.learning')));
    word.append(heading, el('p', undefined, item.translation));
    if (item.example) word.append(el('p', 'lesson-muted', item.example));
    list.append(word);
  }
  card.append(list);
  if (data.error) card.append(el('p', 'lesson-feedback is-error', data.error));
  if (data.error || data.more) {
    const more = el('button', 'lesson-button lesson-button-secondary', data.error ? t('common.tryAgain') : t('lesson.moreWords'));
    more.type = 'button';
    more.disabled = data.loading;
    more.addEventListener('click', loadVocabulary);
    card.append(more);
  }
  target.append(card);
}

async function loadVocabulary() {
  if (state.vocabulary.loading || !state.lesson) return;
  state.vocabulary.loading = true;
  state.vocabulary.error = null;
  renderVocabulary();
  try {
    const page = await getLessonVocabulary(state.lesson.id, state.vocabulary.items.length, 30);
    state.vocabulary.items.push(...page);
    state.vocabulary.more = page.length === 30;
    state.vocabulary.loaded = true;
  } catch (error) {
    if (error?.status === 401) { window.location.replace('/login.html'); return; }
    state.vocabulary.error = describeApiError(error);
  } finally {
    state.vocabulary.loading = false;
    renderVocabulary();
  }
}

async function loadLesson() {
  $('lesson-error').hidden = true;
  $('lesson-loading').hidden = false;
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    const slug = queryParam('slug');
    if (!slug) throw new Error(t('lesson.noSlug'));
    const [lesson, current] = await Promise.all([getLesson(slug), getLessonProgress(slug)]);
    const progress = current.startedAt ? current : await startLesson(slug);
    state.lesson = lesson;
    setWorkspaceAIContext(() => ({
      lessonId: state.lesson?.id,
      exerciseId: ['test', 'practice'].includes(state.tab) ? state.lesson?.exercises[state.index]?.id : undefined,
    }));
    state.progress = progress;
    state.index = Math.max(0, nextUnfinished());
    state.drafts.clear();
    state.tileDrafts.clear();
    state.results.clear();
    state.errors.clear();
    state.vocabulary = { items: [], loaded: false, loading: false, more: false, error: null };
    state.nextStep = null;
    state.nextStepFor = null;
    for (const entry of progress.exercises) {
      if (entry.attempts) state.drafts.set(entry.exerciseId, entry.completed ? entry.answer || '' : '');
    }
    const theory = $('panel-theory');
    theory.replaceChildren(el('div', 'lesson-card lesson-theory'));
    const body = theory.firstElementChild;
    body.append(el('h2', undefined, t('lesson.tabTheory')));
    if (lesson.theory?.trim()) renderTheory(body, `## Theory\n\n${lesson.theory}`);
    else body.append(el('p', undefined, t('lesson.noTheory')));
    renderHero();
    renderPreview();
    switchTab(state.tab);
    $('lesson-loading').hidden = true;
    $('lesson-content').hidden = false;
  } catch (error) {
    if (error?.status === 401) { window.location.replace('/login.html'); return; }
    showError(error);
  }
}

mountWorkspace('lessons');
for (const tab of tabs) {
  $(`tab-${tab}`).addEventListener('click', () => switchTab(tab));
  $(`tab-${tab}`).addEventListener('keydown', (event) => {
    const current = tabs.indexOf(tab);
    const next = event.key === 'ArrowRight' ? (current + 1) % tabs.length
      : event.key === 'ArrowLeft' ? (current + tabs.length - 1) % tabs.length
        : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1;
    if (next < 0) return;
    event.preventDefault();
    switchTab(tabs[next]);
    $(`tab-${tabs[next]}`).focus();
  });
}
loadLesson();
