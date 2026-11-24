import { elapsedSeconds, TestCompletionScreen } from './test-completion.js';
import { getCourse, getLesson, getLessonProgress, getLessonVocabulary, listCourses, previewSelfCheck, startLesson, submitAnswer } from './api.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { getLang, t } from './i18n.js';
import { letterTiles } from './letter-tiles.js';
import { autoCheckText } from './auto-check.js';
import { requireSession } from './session.js';
import { askWorkspaceAI, mountWorkspace, setWorkspaceUser, setWorkspaceAIContext } from './workspace.js';

const $ = (id) => document.getElementById(id);
const tabs = ['theory', 'practice', 'vocabulary'];
const requestedTab = queryParam('tab');
const typeLabel = (type) => ['letter_tiles', 'single_choice', 'text', 'self_check'].includes(type) ? t(`lesson.type.${type}`) : type;
const state = {
  lesson: null, progress: null, tab: tabs.includes(requestedTab) ? requestedTab : 'theory', index: 0, busy: false,
  drafts: new Map(), tileDrafts: new Map(), results: new Map(), errors: new Map(),
  selfChecks: new Map(), cursorKey: null, pendingSubmit: null,
  vocabulary: { items: [], loaded: false, loading: false, more: false, error: null },
  completionErrors: {}, completionProgress: null, retryAttempts: null,
  hints: new Set(),
  // Reads the visible exercise's current (unsent) answer for Fleng AI context.
  readCurrent: null,
};

/** Pick the current interface language from an authored { en, uk } text (English fallback). */
function pick(text) {
  return text ? (text[getLang()] || text.en || '') : '';
}

// Sections that support the main rule; they are folded away so the rule stands out.
const EXTRA_SECTIONS = new Set(['read-in-context', 'vocabulary']);
const headingKey = (heading) => heading.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');

/** Split a dense rule paragraph into short steps (only when it has several sentences). */
export function ruleSteps(text) {
  const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z"“(])/).map((part) => part.trim()).filter(Boolean);
  // One- or two-word fragments ("Listen.", "Write.") are examples of the previous step, not steps.
  const steps = [];
  for (const sentence of sentences) {
    const words = sentence.replace(/[.!?"“”()]/g, '').split(/\s+/).filter(Boolean).length;
    if (words <= 2 && steps.length) steps[steps.length - 1] += ` ${sentence}`;
    else steps.push(sentence);
  }
  return steps.length >= 3 ? steps : null;
}

/**
 * Render lesson theory: the small documented markup (## headings, "- " lists,
 * paragraphs). Long rule paragraphs become numbered steps; "Read in context" and
 * "Vocabulary" go into a closed "More" section so the main rule comes first.
 */
export function renderTheory(container, theory) {
  container.textContent = '';
  let target = container;
  let extra = null;
  for (const raw of theory.split(/\n\s*\n/)) {
    const block = raw.trim();
    if (!block) continue;
    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean);
    if (lines.every((line) => line.startsWith('- '))) {
      const list = el('ul');
      for (const line of lines) list.append(el('li', undefined, line.slice(2)));
      target.append(list);
    } else if (block.startsWith('## ')) {
      const heading = block.slice(3).trim();
      const slug = headingKey(heading);
      const key = `lesson.heading.${slug}`;
      if (EXTRA_SECTIONS.has(slug)) {
        if (!extra) {
          extra = el('details', 'lesson-theory-more');
          extra.append(el('summary', undefined, t('lesson.moreTheory')));
          container.append(extra);
        }
        target = extra;
      } else {
        target = container;
      }
      target.append(el('h3', undefined, t(key) === key ? heading : t(key)));
    } else {
      const text = lines.join(' ');
      const steps = target === container ? ruleSteps(text) : null;
      if (steps) {
        const box = el('div', 'lesson-rule-steps');
        box.append(el('p', 'lesson-rule-label', t('lesson.stepByStep')));
        const list = el('ol');
        for (const step of steps) list.append(el('li', undefined, step));
        box.append(list);
        target.append(box);
      } else {
        target.append(el('p', undefined, text));
      }
    }
  }
}

/** Plain-language rule with English examples; Ukrainian explanation when the UI is Ukrainian. */
function guideCard(guide) {
  const card = el('section', 'lesson-card lesson-guide');
  card.append(el('h2', undefined, t('lesson.guideTitle')), el('p', 'lesson-guide-text', pick(guide.explanation)));
  const list = el('ul', 'lesson-guide-examples');
  for (const example of guide.examples) {
    const item = el('li');
    item.append(el('span', 'lesson-guide-en', example.en));
    if (getLang() !== 'en' && example.uk) item.append(el('span', 'lesson-guide-uk', example.uk));
    list.append(item);
  }
  card.append(el('h3', undefined, t('lesson.guideExamples')), list);
  return card;
}

function exerciseState(exercise) {
  return state.progress.exercises.find((item) => item.exerciseId === exercise.id);
}

function exerciseType(exercise) {
  return exercise.letterTiles ? 'letter_tiles' : exercise.type;
}

function nextUnfinished() {
  if (state.retryAttempts) {
    return state.lesson.exercises.findIndex((exercise) =>
      state.retryAttempts[exercise.id] === (exerciseState(exercise)?.attempts ?? 0));
  }
  const [first] = state.progress.pendingExerciseIds ?? state.progress.exercises
    .filter((record) => !record.attempts).map((record) => record.exerciseId);
  return state.lesson.exercises.findIndex((exercise) => exercise.id === first);
}

function saveCursor() {
  if (!state.cursorKey) return;
  try {
    if (!state.retryAttempts && !state.pendingSubmit) window.sessionStorage.removeItem(state.cursorKey);
    else window.sessionStorage.setItem(state.cursorKey, JSON.stringify({
      pending: state.pendingSubmit, retryAttempts: state.retryAttempts,
    }));
  } catch {
    // The server can still restore the main pass.
  }
}

function restoreCursor() {
  state.pendingSubmit = null;
  state.retryAttempts = null;
  if (state.cursorKey) {
    try {
      const cursor = JSON.parse(window.sessionStorage.getItem(state.cursorKey));
      state.retryAttempts = cursor?.retryAttempts ?? null;
      if (state.retryAttempts && nextUnfinished() === -1) state.retryAttempts = null;
      const pending = cursor?.pending;
      const record = state.progress.exercises.find(({ exerciseId }) => exerciseId === pending?.exerciseId);
      if (record?.attempts === pending?.expectedAttempts) state.pendingSubmit = pending ?? null;
    } catch {
      // Fall back to the first unvisited exercise from the server.
    }
  }
  return Math.max(0, nextUnfinished());
}

function startMistakeRetry(records) {
  state.retryAttempts = Object.fromEntries(records.map((record) => [record.exerciseId, record.attempts]));
  state.index = nextUnfinished();
  saveCursor();
  for (const { exerciseId } of records) {
    state.drafts.set(exerciseId, '');
    state.results.delete(exerciseId);
  }
  switchTab('practice');
  renderHero();
  renderPreview();
  $('panel-practice').querySelector('h2')?.focus();
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
  const finished = Boolean(progress.testFinishedAt || progress.completed);
  completed.hidden = !finished || Boolean(state.retryAttempts);
  if (completed.hidden) return;
  if (state.completionProgress === progress) return;
  state.completionProgress = progress;
  const records = progress.exercises;
  const byId = new Map(state.lesson.exercises.map((exercise) => [exercise.id, exercise]));
  const total = progress.exercisesTotal;
  const known = records.every((record) => record.firstOutcome != null);
  const correct = known ? records.filter((record) => record.firstOutcome === 'correct').length : undefined;
  const mistakes = known ? records.filter((record) => record.firstOutcome === 'incorrect').length : undefined;
  const skipped = known ? records.filter((record) => record.firstOutcome === 'skipped').length : undefined;
  const retries = records.reduce((count, record) => count + Math.max(0, record.attempts - 1), 0);
  const retryable = records.filter((record) => !record.completed && byId.has(record.exerciseId));
  const heading = TestCompletionScreen(completed, {
    headingId: 'lesson-completion-title',
    title: t(progress.completed ? 'lesson.completedTitle' : 'completion.lessonNotPassed'),
    subtitle: state.lesson.title,
    courseTitle: state.lesson.courseTitle,
    level: state.lesson.level,
    total, correct, firstTry: correct, mistakes, skipped, retries, xp: progress.xpEarned,
    seconds: elapsedSeconds(progress.startedAt, progress.testFinishedAt ?? progress.completedAt),
    items: records.filter((record) => record.attempts > 0 && byId.has(record.exerciseId)).map((record) => {
      const exercise = byId.get(record.exerciseId);
      const answer = optionText(exercise, record.firstAnswer);
      const errors = state.completionErrors[exercise.id] ?? [];
      const firstError = record.firstOutcome === 'incorrect' && !errors.some((item) => item.answer === answer)
        ? [{ answer, expected: record.expectedAnswer }]
        : [];
      return {
        title: exercise.prompt,
        mistake: record.firstOutcome === 'incorrect' || errors.length > 0
          || (!record.firstOutcome && record.isCorrect === false),
        skipped: record.firstOutcome === 'skipped',
        answer,
        expected: record.expectedAnswer,
        errors: [...firstError, ...errors],
      };
    }),
    backToCourses: true,
    retryMistakes: retryable.length ? () => startMistakeRetry(retryable) : undefined,
    continueLearning: progress.completed ? loadNextStep(state.lesson) : undefined,
  });
  if (state.busy || state.tab === 'practice' || queryParam('view') === 'results') heading.focus();
}

function optionText(exercise, answer) {
  return exercise.options?.find(({ id }) => id === answer)?.text ?? answer;
}

function rememberMistake(exercise, answer, result) {
  if (result.isCorrect !== false) return;
  const expected = result.correctOptionId
    ? optionText(exercise, result.correctOptionId)
    : result.acceptedAnswers?.[0] ?? result.modelAnswer;
  (state.completionErrors[exercise.id] ??= []).push({ answer: optionText(exercise, answer), expected });
  if (!state.cursorKey) return;
  try { sessionStorage.setItem(`${state.cursorKey}:completion-errors`, JSON.stringify(state.completionErrors)); }
  catch { /* Review remains available in this document. */ }
}

/** Real catalog data only: the next lesson of this course, else the next course. */
async function loadNextStep(lesson) {
  try {
    const course = await getCourse(lesson.courseSlug);
    const position = course.lessons.findIndex((item) => item.slug === lesson.slug);
    const nextLesson = position >= 0 ? course.lessons[position + 1] : null;
    if (nextLesson) return {
      href: `/lesson.html?slug=${encodeURIComponent(nextLesson.slug)}`,
      label: t('completion.nextLesson'),
    };
    const all = await listCourses();
    const index = all.findIndex((item) => item.slug === lesson.courseSlug);
    if (index >= 0 && all[index + 1]) return {
      href: `/course.html?slug=${encodeURIComponent(all[index + 1].slug)}`,
      label: t('completion.continue'),
    };
  } catch {
    // The course link remains available if recommendations cannot load.
  }
}

function labelled(label, text) {
  const row = el('p', 'lesson-feedback-line');
  row.append(el('span', 'lesson-feedback-label', `${label}: `), el('span', undefined, text));
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
    let headline = ok == null ? t('completion.skipped') : exercise.type === 'self_check'
      ? (ok ? t('lesson.selfCorrect') : t('lesson.selfIncorrect'))
      : (ok ? t('lesson.correct') : t('lesson.incorrect'));
    if (result.xpAwarded) headline += ` · +${result.xpAwarded} XP`;
    box.append(el('strong', undefined, headline));
    if (ok === false && exercise.type !== 'self_check') box.append(el('p', undefined, t('lesson.mistakeHint')));
    if (exercise.type === 'single_choice' && result.correctOptionId) {
      const option = exercise.options?.find((item) => item.id === result.correctOptionId);
      if (option) box.append(labelled(t('lesson.correctAnswer'), option.text));
    }
    if (exercise.type === 'text' && result.acceptedAnswers?.length) {
      box.append(labelled(t('lesson.acceptedAnswer'), result.acceptedAnswers[0]));
    }
    // Authored explanation (EN/UK) is preferred; the legacy English text is the fallback.
    if (result.wrongAnswerNote && !ok) box.append(labelled(t('lesson.whyNot'), pick(result.wrongAnswerNote)));
    const explanation = pick(result.explanationLocalized) || result.explanation;
    if (explanation) box.append(labelled(t('lesson.explanation'), explanation));
  } else if (record?.attempts) {
    const status = record.completed ? t('lesson.statusDone') : t('lesson.statusSaved');
    box.append(el('strong', undefined, status));
    if (record.answer) {
      const option = exercise.options?.find((item) => item.id === record.answer);
      box.append(labelled(t('lesson.latestAnswer'), option?.text || record.answer));
    }
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
  if (state.busy || nextUnfinished() !== state.index || state.lesson.exercises[state.index]?.id !== exercise.id) return;
  if (answer !== null && !answer?.trim()) {
    state.errors.set(exercise.id, t('lesson.needAnswer'));
    renderQuestions();
    return;
  }
  state.busy = true;
  const expectedAttempts = exerciseState(exercise)?.attempts ?? 0;
  state.pendingSubmit = { exerciseId: exercise.id, expectedAttempts };
  saveCursor();
  let advanced = false;
  $('lesson-last-answer').replaceChildren();
  state.errors.delete(exercise.id);
  setBusy(true);
  const pending = document.querySelector(`[data-exercise-id="${exercise.id}"] .lesson-feedback`);
  if (pending) pending.replaceChildren(el('strong', undefined, t('lesson.checking')));
  try {
    const result = await submitAnswer(state.lesson.slug, {
      exerciseId: exercise.id, answer, expectedAttempts,
      ...(assessment ? { selfAssessment: assessment } : {}),
    });
    rememberMistake(exercise, answer, result);
    state.progress = result.lesson;
    state.pendingSubmit = null;
    state.results.set(exercise.id, result);
    state.drafts.set(exercise.id, '');
    state.tileDrafts.delete(exercise.id);
    state.selfChecks.delete(exercise.id);
    const next = nextUnfinished();
    if (next === -1) state.retryAttempts = null;
    if (next !== -1 && next !== state.index) {
      $('lesson-last-answer').append(feedback(exercise, null));
      state.index = next;
      advanced = true;
    }
    saveCursor();
    renderHero();
    renderPreview();
  } catch (error) {
    if (error?.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    state.errors.set(exercise.id, describeApiError(error));
    if (!error?.status || error.code === 'INVALID_RESPONSE' || error.status === 409 || error.status >= 500) {
      // A lost response can follow a successful commit. Read before retrying.
      try {
        const progress = await getLessonProgress(state.lesson.slug);
        if (adoptSavedSubmission(progress, state.pendingSubmit)) {
          advanced = state.lesson.exercises[state.index]?.id !== exercise.id;
          if (advanced) $('lesson-last-answer').append(feedback(exercise, exerciseState(exercise)));
        }
      } catch {
        // Preserve the error and draft so the learner can retry.
      }
    } else {
      state.pendingSubmit = null;
      saveCursor();
    }
  } finally {
    state.busy = false;
    renderQuestions();
    setBusy(false);
    const card = document.querySelector(`[data-exercise-id="${exercise.id}"]`);
    if (advanced) $(`panel-${state.tab}`).querySelector('h2')?.focus();
    else if (nextUnfinished() !== -1) card?.querySelector('.lesson-feedback')?.focus();
  }
}

function adoptSavedSubmission(progress, pending) {
  const { exerciseId, expectedAttempts } = pending;
  const attempt = progress.exercises.find((record) => record.exerciseId === exerciseId);
  if (!attempt || attempt.attempts <= expectedAttempts) return false;
  const exercise = state.lesson.exercises.find((item) => item.id === exerciseId);
  if (exercise && attempt.answer != null) rememberMistake(exercise, attempt.answer, attempt);
  state.progress = progress;
  state.pendingSubmit = null;
  state.errors.delete(exerciseId);
  state.results.delete(exerciseId);
  state.drafts.set(exerciseId, attempt.completed ? attempt.answer || '' : '');
  state.tileDrafts.delete(exerciseId);
  state.selfChecks.delete(exerciseId);
  const next = nextUnfinished();
  if (next === -1) state.retryAttempts = null;
  else state.index = next;
  saveCursor();
  renderHero();
  renderPreview();
  return true;
}

async function restorePendingSubmission(slug) {
  const pending = state.pendingSubmit;
  if (!pending) return;
  // A reload can reach GET /progress while the previous document's POST is still committing.
  for (const delay of [250, 750, 1500, 3000]) {
    await new Promise((resolve) => setTimeout(resolve, delay));
    if (state.pendingSubmit !== pending || state.busy) return;
    try {
      const progress = await getLessonProgress(slug);
      if (state.pendingSubmit !== pending || state.busy) return;
      if (adoptSavedSubmission(progress, pending)) {
        renderQuestions();
        return;
      }
    } catch {
      // A failed GET does not replay the answer or override the rendered progress.
    }
  }
  if (state.pendingSubmit === pending) {
    state.pendingSubmit = null;
    saveCursor();
  }
}

async function revealModelAnswer(exercise, answer) {
  if (state.busy) return;
  if (!answer.trim()) {
    state.errors.set(exercise.id, t('lesson.needAnswer'));
    renderQuestions();
    return;
  }
  state.busy = true;
  state.errors.delete(exercise.id);
  setBusy(true);
  try {
    const { modelAnswer } = await previewSelfCheck(state.lesson.slug, { exerciseId: exercise.id, answer });
    state.selfChecks.set(exercise.id, { answer, modelAnswer });
  } catch (error) {
    if (error?.status === 401) window.location.replace('/login.html');
    else state.errors.set(exercise.id, describeApiError(error));
  } finally {
    state.busy = false;
    renderQuestions();
    setBusy(false);
    document.querySelector('.lesson-model-answer, .lesson-feedback.is-error')?.focus();
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

/** Hint toggle: authored text from the API, shown only on request, never the answer. */
function hintControl(exercise) {
  const text = pick(exercise.hint);
  const box = el('div', 'lesson-hint');
  const note = el('p', 'lesson-hint-text', text);
  note.setAttribute('role', 'note');
  note.id = `hint-${exercise.id}`;
  const toggle = el('button', 'lesson-hint-toggle', '');
  toggle.type = 'button';
  toggle.setAttribute('aria-controls', note.id);
  const sync = () => {
    const open = state.hints.has(exercise.id);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = `💡 ${open ? t('lesson.hideHint') : t('lesson.hint')}`;
    note.hidden = !open;
  };
  toggle.addEventListener('click', () => {
    if (state.hints.has(exercise.id)) state.hints.delete(exercise.id);
    else state.hints.add(exercise.id);
    sync();
  });
  sync();
  box.append(toggle, note);
  return box;
}

/**
 * "I don't understand": opens the existing Fleng AI panel about this exercise. The
 * page stays as it is, so drafts and progress are kept; closing the panel returns
 * focus to this button.
 */
function notClearButton(exercise, index) {
  const button = el('button', 'lesson-not-clear', t('lesson.notClear'));
  button.type = 'button';
  button.setAttribute('aria-controls', 'ai-panel');
  button.addEventListener('click', () => {
    const prompt = exercise.prompt.length > 70 ? `${exercise.prompt.slice(0, 67)}…` : exercise.prompt;
    const opened = askWorkspaceAI({
      message: t('lesson.aiStarter'),
      label: t('lesson.aiAbout', { n: index + 1, prompt }),
      backLabel: t('lesson.aiBack'),
      returnFocus: button,
    });
    if (!opened) {
      button.disabled = true;
      button.textContent = t('lesson.aiUnavailable');
    }
  });
  return button;
}

function questionCard(exercise, index) {
  const selfCheck = state.selfChecks.get(exercise.id);
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
  setProgressBar(track, state.progress.exercises.filter((item) => item.attempts > 0).length, state.progress.exercisesTotal);
  // The task comes first, so the learner knows what to do before reading the prompt.
  const instructionKey = `lesson.instruction.${exerciseType(exercise)}`;
  const task = pick(exercise.instruction) || (t(instructionKey) !== instructionKey ? t(instructionKey) : '');
  if (task) {
    const instruction = el('p', 'lesson-instruction');
    instruction.id = `task-${exercise.id}`;
    instruction.append(el('strong', undefined, `${t('lesson.task')} `), el('span', undefined, task));
    card.append(instruction);
  }
  const prompt = el('h2', undefined, exercise.prompt);
  prompt.tabIndex = -1;
  if (task) prompt.setAttribute('aria-describedby', `task-${exercise.id}`);
  card.append(prompt);
  const help = el('div', 'lesson-help-row');
  if (pick(exercise.hint)) help.append(hintControl(exercise));
  help.append(notClearButton(exercise, index));
  card.append(help);
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
      const checkChoice = () => {
        if (state.busy || !input.checked) return;
        state.drafts.set(exercise.id, input.value);
        markEdited(exercise);
        submit(exercise, input.value);
      };
      input.addEventListener('click', checkChoice);
      input.addEventListener('change', checkChoice);
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
        const answer = tiles.readAnswer();
        if (answer) submit(exercise, answer);
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
    input.value = selfCheck?.answer ?? (state.drafts.has(exercise.id) ? state.drafts.get(exercise.id) : record?.answer || '');
    input.readOnly = Boolean(selfCheck);
    input.addEventListener('input', () => {
      state.drafts.set(exercise.id, input.value);
      markEdited(exercise);
    });
    if (result) input.classList.add(result.isCorrect ? 'is-correct' : 'is-incorrect');
    label.append(input);
    form.append(label);
    readAnswer = () => input.value;
    if (exercise.type === 'text') {
      form.append(el('p', 'lesson-muted', t('lesson.autoCheckText')));
      autoCheckText(form, input, (answer) => submit(exercise, answer));
    }
  } else {
    form.append(el('p', 'lesson-muted', t('lesson.unsupported')));
  }
  const actions = el('div', 'lesson-answer-actions');
  if (exercise.type === 'self_check') {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      if (!selfCheck) revealModelAnswer(exercise, readAnswer());
    });
    if (selfCheck) {
      const model = labelled(t('lesson.modelAnswer'), selfCheck.modelAnswer);
      model.classList.add('lesson-model-answer');
      model.tabIndex = -1;
      form.append(model);
      for (const [assessment, title] of [['correct', t('lesson.gotRight')], ['incorrect', t('lesson.needPractice')]]) {
        const button = el('button', 'lesson-button lesson-button-secondary', title);
        button.type = 'button';
        button.addEventListener('click', () => submit(exercise, selfCheck.answer, assessment));
        actions.append(button);
      }
    } else {
      const confirm = el('button', 'lesson-button lesson-button-secondary', t('lesson.showModelAnswer'));
      confirm.type = 'submit';
      actions.append(confirm);
    }
  } else if (readAnswer && state.errors.has(exercise.id)) {
    const button = el('button', 'lesson-button lesson-button-secondary', t('lesson.retryCheck'));
    button.type = 'button';
    button.addEventListener('click', () => submit(exercise, readAnswer()));
    actions.append(button);
  }
  if (actions.children.length) form.append(actions);
  state.readCurrent = readAnswer || null;
  card.append(form, feedback(exercise, record));
  const nav = el('div', 'lesson-question-navigation');
  const skip = el('button', 'lesson-button lesson-button-secondary', t('completion.skip'));
  skip.type = 'button';
  skip.addEventListener('click', () => submit(exercise, null));
  nav.append(skip);
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
  if (state.tab === 'practice' && nextUnfinished() !== -1) {
    practice.append(questionCard(exercises[state.index], state.index));
  }
}

function renderPreview() {
  const { lesson, progress } = state;
  const target = $('template-preview');
  target.textContent = '';
  if (!lesson.exercises.length) {
    target.append(el('p', 'lesson-muted', t('lesson.noActivities')));
    return;
  }
  if (nextUnfinished() === -1) return;
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
    const button = el('button', exerciseState(lesson.exercises[index])?.attempts ? 'is-done' : '', String(index + 1));
    button.type = 'button';
    button.setAttribute('aria-label', t('lesson.openQuestion', { n: index + 1 }));
    if (index === state.index) button.setAttribute('aria-current', 'step');
    button.disabled = true;
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
      currentAnswer: state.tab === 'practice' ? state.readCurrent?.() : undefined,
    }));
    state.progress = progress;
    state.cursorKey = user.id ? `fleng.lesson.cursor:${user.id}:${lesson.id}` : null;
    state.completionErrors = {};
    if (state.cursorKey) {
      try { state.completionErrors = JSON.parse(sessionStorage.getItem(`${state.cursorKey}:completion-errors`)) ?? {}; }
      catch { /* The server still supplies attempt counts. */ }
    }
    state.index = restoreCursor();
    saveCursor();
    state.drafts.clear();
    state.tileDrafts.clear();
    state.results.clear();
    state.errors.clear();
    state.selfChecks.clear();
    state.vocabulary = { items: [], loaded: false, loading: false, more: false, error: null };
    state.hints.clear();
    for (const entry of progress.exercises) {
      if (entry.attempts) state.drafts.set(entry.exerciseId, entry.completed ? entry.answer || '' : '');
    }
    const theory = $('panel-theory');
    theory.replaceChildren(el('div', 'lesson-card lesson-theory'));
    const body = theory.firstElementChild;
    body.append(el('h2', undefined, t('lesson.tabTheory')));
    if (lesson.guide) theory.prepend(guideCard(lesson.guide));
    if (lesson.theory?.trim()) renderTheory(body, `## Theory\n\n${lesson.theory}`);
    else body.append(el('p', undefined, t('lesson.noTheory')));
    switchTab(state.tab);
    $('lesson-loading').hidden = true;
    $('lesson-content').hidden = false;
    renderHero();
    renderPreview();
    void restorePendingSubmission(slug);
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
