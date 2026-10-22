import { getLesson, getLessonProgress, getLessonVocabulary, startLesson, submitAnswer } from './api.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
const tabs = ['theory', 'practice', 'test', 'vocabulary'];
const labels = { single_choice: 'Multiple choice', text: 'Short answer', self_check: 'Self-check' };
const state = {
  lesson: null, progress: null, tab: 'test', index: 0, busy: false,
  drafts: new Map(), results: new Map(), errors: new Map(),
  vocabulary: { items: [], loaded: false, loading: false, more: false, error: null },
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
      container.append(el('h3', undefined, block.slice(3)));
    } else {
      container.append(el('p', undefined, lines.join(' ')));
    }
  }
}

function exerciseState(exercise) {
  return state.progress.exercises.find((item) => item.exerciseId === exercise.id);
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
  box.replaceChildren(el('h1', undefined, 'Lesson unavailable'), el('p', undefined, describeApiError(error)));
  const retry = el('button', 'lesson-button lesson-button-primary', 'Try again');
  retry.type = 'button';
  retry.addEventListener('click', loadLesson);
  const catalog = el('a', 'lesson-button lesson-button-secondary', 'Browse lessons');
  catalog.href = '/courses.html';
  box.append(retry, catalog);
}

function renderHero() {
  const { lesson, progress } = state;
  $('lesson-number').textContent = Number.isInteger(lesson.position) ? `LESSON ${lesson.position}` : 'LESSON';
  $('lesson-level').textContent = lesson.level || 'Course lesson';
  $('lesson-duration').textContent = lesson.estimatedMinutes ? `${lesson.estimatedMinutes} min` : 'Self-paced';
  $('lesson-title').textContent = lesson.title;
  $('lesson-subtitle').textContent = lesson.summary || 'Continue your English practice.';
  $('lesson-course-link').textContent = lesson.courseTitle;
  $('lesson-course-link').href = `/course.html?slug=${encodeURIComponent(lesson.courseSlug)}`;
  $('lesson-activity-count').textContent = `${progress.exercisesCompleted} / ${progress.exercisesTotal} activities`;
  $('lesson-xp').textContent = `${progress.xpEarned} XP earned`;
  setProgressBar($('lesson-progress'), progress.exercisesCompleted, progress.exercisesTotal);
  const completed = $('lesson-completed');
  completed.hidden = !progress.completed;
  if (progress.completed) {
    const course = el('a', undefined, 'Continue in course →');
    course.href = $('lesson-course-link').href;
    completed.replaceChildren(el('strong', undefined, 'Lesson completed'), el('p', undefined, 'You have finished every activity in this lesson.'), course);
  }
  document.title = `${lesson.title} — Fleng`;
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
    box.classList.add(result.isCorrect ? 'is-correct' : 'is-incorrect');
    let headline = exercise.type === 'self_check'
      ? (result.isCorrect ? 'Marked as correct' : 'Marked for more practice')
      : (result.isCorrect ? 'Correct' : 'Try again');
    if (result.xpAwarded) headline += ` · +${result.xpAwarded} XP`;
    box.append(el('strong', undefined, headline));
    if (result.feedback) box.append(el('p', undefined, result.feedback));
    if (exercise.type === 'single_choice' && result.correctOptionId) {
      const option = exercise.options?.find((item) => item.id === result.correctOptionId);
      if (option) box.append(el('p', undefined, `Correct answer: ${option.text}`));
    }
    if (exercise.type === 'text' && result.acceptedAnswers?.length) {
      box.append(el('p', undefined, `Accepted answer: ${result.acceptedAnswers[0]}`));
    }
    if (result.modelAnswer) box.append(el('p', undefined, `Model answer: ${result.modelAnswer}`));
    if (result.explanation) box.append(el('p', undefined, result.explanation));
  } else if (record?.attempts) {
    const status = record.completed ? 'Completed' : 'Previous attempt saved';
    box.append(el('strong', undefined, status));
    if (record.answer) {
      const option = exercise.options?.find((item) => item.id === record.answer);
      box.append(el('p', undefined, `Your latest answer: ${option?.text || record.answer}`));
    }
    if (!record.completed) box.append(el('p', undefined, 'Submit another answer to see feedback.'));
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
    state.errors.set(exercise.id, exercise.type === 'single_choice' ? 'Choose an answer first.' : 'Write an answer first.');
    renderQuestions();
    return;
  }
  state.busy = true;
  state.errors.delete(exercise.id);
  setBusy(true);
  const pending = document.querySelector(`[data-exercise-id="${exercise.id}"] .lesson-feedback`);
  if (pending) pending.replaceChildren(el('strong', undefined, 'Checking answer…'));
  try {
    const result = await submitAnswer(state.lesson.slug, {
      exerciseId: exercise.id, answer,
      ...(assessment ? { selfAssessment: assessment } : {}),
    });
    state.progress = result.lesson;
    state.results.set(exercise.id, result);
    state.drafts.set(exercise.id, answer);
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
    card?.querySelector('.lesson-feedback')?.focus();
  }
}

function setBusy(busy) {
  document.querySelectorAll('.lesson-tabs button, #use-template, #template-preview button, #template-structure button, .lesson-answer-form button, .lesson-question-navigation button').forEach((button) => {
    if (busy) {
      button.dataset.disabledBeforeSubmit = String(button.disabled);
      button.disabled = true;
    } else if (button.dataset.disabledBeforeSubmit !== undefined) {
      button.disabled = button.dataset.disabledBeforeSubmit === 'true';
      delete button.dataset.disabledBeforeSubmit;
    }
  });
}

function questionCard(exercise, index, mode) {
  const record = exerciseState(exercise);
  const result = state.results.get(exercise.id);
  const card = el('article', 'lesson-card lesson-question lesson-reveal');
  card.dataset.exerciseId = exercise.id;
  const meta = el('div', 'lesson-question-meta');
  meta.append(el('span', 'lesson-chip', `Question ${index + 1} / ${state.lesson.exercises.length}`), el('span', undefined, `${labels[exercise.type] || exercise.type} · ${exercise.points} XP`));
  card.append(meta);
  const track = el('div', 'lesson-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', 'Completed lesson questions');
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.append(el('span', 'lesson-fill'));
  card.append(track);
  setProgressBar(track, state.progress.exercisesCompleted, state.progress.exercisesTotal);
  const prompt = el('h2', undefined, exercise.prompt);
  prompt.tabIndex = -1;
  card.append(prompt);
  const form = el('form', 'lesson-answer-form');
  let readAnswer;
  if (exercise.type === 'single_choice') {
    const field = el('fieldset', 'lesson-options');
    field.append(el('legend', 'sr-only', 'Choose one answer'));
    for (const option of exercise.options || []) {
      const label = el('label', 'lesson-option');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `answer-${exercise.id}`;
      input.value = option.id;
      input.checked = (state.drafts.has(exercise.id) ? state.drafts.get(exercise.id) : record?.answer) === option.id;
      input.addEventListener('change', () => { state.drafts.set(exercise.id, input.value); markEdited(exercise); });
      label.append(input, el('span', undefined, option.text));
      if (result?.correctOptionId === option.id) label.classList.add('is-correct');
      else if (result && !result.isCorrect && input.checked) label.classList.add('is-incorrect');
      field.append(label);
    }
    form.append(field);
    readAnswer = () => field.querySelector('input:checked')?.value || '';
  } else if (exercise.type === 'text' || exercise.type === 'self_check') {
    const label = el('label', 'lesson-answer-label', 'Your answer');
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
    form.append(el('p', 'lesson-muted', 'This activity type is not available in the current lesson player.'));
  }
  const actions = el('div', 'lesson-answer-actions');
  if (exercise.type === 'self_check') {
    for (const [assessment, title] of [['correct', 'I got it right'], ['incorrect', 'I need practice']]) {
      const button = el('button', 'lesson-button lesson-button-secondary', title);
      button.type = 'button';
      button.addEventListener('click', () => submit(exercise, readAnswer(), assessment));
      actions.append(button);
    }
  } else if (readAnswer) {
    const button = el('button', 'lesson-button lesson-button-primary', 'Check answer');
    button.type = 'submit';
    actions.append(button);
    form.addEventListener('submit', (event) => { event.preventDefault(); submit(exercise, readAnswer()); });
  }
  form.append(actions);
  card.append(form, feedback(exercise, record));
  if (mode === 'test') {
    const nav = el('div', 'lesson-question-navigation');
    const previous = el('button', 'lesson-button lesson-button-secondary', '← Previous');
    previous.type = 'button';
    previous.disabled = index === 0;
    previous.addEventListener('click', () => goQuestion(index - 1));
    const next = el('button', 'lesson-button lesson-button-primary', 'Next →');
    next.type = 'button';
    next.disabled = index === state.lesson.exercises.length - 1;
    next.addEventListener('click', () => goQuestion(index + 1));
    nav.append(previous, el('span', undefined, 'Your answers are saved when you check them.'), next);
    card.append(nav);
  }
  return card;
}

function renderQuestions() {
  if (!state.lesson) return;
  const practice = $('panel-practice');
  const test = $('panel-test');
  practice.textContent = '';
  test.textContent = '';
  const exercises = state.lesson.exercises;
  if (!exercises.length) {
    const empty = el('div', 'lesson-card lesson-empty');
    empty.append(el('h2', undefined, 'No activities yet'), el('p', undefined, 'This lesson does not have activities to complete.'));
    $(state.tab === 'practice' ? 'panel-practice' : 'panel-test').append(empty);
    return;
  }
  if (state.tab === 'practice') {
    for (let index = 0; index < exercises.length; index++) practice.append(questionCard(exercises[index], index, 'practice'));
  } else if (state.tab === 'test') {
    test.append(questionCard(exercises[state.index], state.index, 'test'));
  }
}

function goQuestion(index) {
  if (state.busy || index < 0 || index >= state.lesson.exercises.length) return;
  state.index = index;
  switchTab('test');
  $('panel-test').querySelector('h2')?.focus();
  renderPreview();
}

function renderPreview() {
  const { lesson, progress } = state;
  const target = $('template-preview');
  target.textContent = '';
  if (!lesson.exercises.length) {
    target.append(el('p', 'lesson-muted', 'No test activities are available.'));
    $('use-template').disabled = true;
    return;
  }
  const mini = el('div', 'template-mini');
  const meta = el('div', 'template-mini-meta');
  meta.append(el('span', undefined, `Question ${state.index + 1} / ${lesson.exercises.length}`), el('span', undefined, `${progress.exercisesCompleted} complete`));
  mini.append(meta, el('p', undefined, lesson.exercises[state.index].prompt));
  const bar = el('div', 'lesson-track');
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', 'Test preview progress');
  bar.setAttribute('aria-valuemin', '0');
  bar.setAttribute('aria-valuemax', '100');
  bar.append(el('span', 'lesson-fill'));
  setProgressBar(bar, progress.exercisesCompleted, progress.exercisesTotal);
  mini.append(bar);
  const questions = el('div', 'template-questions');
  for (let index = 0; index < lesson.exercises.length; index++) {
    const button = el('button', exerciseState(lesson.exercises[index])?.completed ? 'is-done' : '', String(index + 1));
    button.type = 'button';
    button.setAttribute('aria-label', `Open question ${index + 1}`);
    if (index === state.index) button.setAttribute('aria-current', 'step');
    button.addEventListener('click', () => goQuestion(index));
    questions.append(button);
  }
  mini.append(questions);
  target.append(mini);
}

function renderStructure() {
  const target = $('template-structure');
  target.textContent = '';
  for (const [type, label] of [
    ['single_choice', 'Multiple choice'], ['true_false', 'True / False'],
    ['fill_blank', 'Fill in the blank'], ['match_pairs', 'Match the pairs'],
    ['text', 'Short answer'], ['self_check', 'Self-check'],
  ]) {
    const indices = state.lesson.exercises.flatMap((item, index) => item.type === type ? [index] : []);
    const row = el('li');
    if (indices.length) {
      const button = el('button', undefined, label);
      button.type = 'button';
      button.addEventListener('click', () => goQuestion(indices[0]));
      row.append(button, el('small', undefined, String(indices.length)));
    } else {
      row.append(el('span', undefined, label), el('small', undefined, 'Not in this lesson'));
    }
    target.append(row);
  }
}

function switchTab(tab) {
  if (!tabs.includes(tab) || state.busy) return;
  state.tab = tab;
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
  card.append(el('h2', undefined, 'Vocabulary'), el('p', 'lesson-muted', 'Words you saved for this lesson.'));
  if (data.loading && !data.items.length) card.append(el('p', undefined, 'Loading vocabulary…'));
  if (!data.loading && !data.items.length && !data.error) card.append(el('p', undefined, 'You have not saved any words for this lesson yet.'));
  const list = el('div', 'lesson-word-list');
  for (const item of data.items) {
    const word = el('article', 'lesson-word');
    const heading = el('h3');
    heading.append(el('span', undefined, item.word), el('span', 'lesson-chip', item.learned ? 'Learned' : 'Learning'));
    word.append(heading, el('p', undefined, item.translation));
    if (item.example) word.append(el('p', 'lesson-muted', item.example));
    list.append(word);
  }
  card.append(list);
  if (data.error) card.append(el('p', 'lesson-feedback is-error', data.error));
  if (data.error || data.more) {
    const more = el('button', 'lesson-button lesson-button-secondary', data.error ? 'Try again' : 'Load more words');
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
    if (!slug) throw new Error('Choose a lesson from the catalog to continue.');
    const [lesson, current] = await Promise.all([getLesson(slug), getLessonProgress(slug)]);
    const progress = current.startedAt ? current : await startLesson(slug);
    state.lesson = lesson;
    state.progress = progress;
    state.index = Math.max(0, lesson.exercises.findIndex((item) => !progress.exercises.some((entry) => entry.exerciseId === item.id && entry.completed)));
    state.drafts.clear();
    state.results.clear();
    state.errors.clear();
    state.vocabulary = { items: [], loaded: false, loading: false, more: false, error: null };
    for (const entry of progress.exercises) if (entry.answer) state.drafts.set(entry.exerciseId, entry.answer);
    const theory = $('panel-theory');
    theory.replaceChildren(el('div', 'lesson-card lesson-theory'));
    const body = theory.firstElementChild;
    body.append(el('h2', undefined, 'Theory'));
    if (lesson.theory?.trim()) renderTheory(body, `## Theory\n\n${lesson.theory}`);
    else body.append(el('p', undefined, 'Theory is not available for this lesson yet.'));
    renderHero();
    renderStructure();
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
$('use-template').addEventListener('click', () => { switchTab('test'); $('panel-test').focus(); });
loadLesson();
