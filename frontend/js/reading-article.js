import {
  getReadingArticle,
  listReadingAttempts,
  saveReadingAnswers,
  startReadingAttempt,
  submitReadingAttempt,
  updateReadingProgress,
} from './api.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { t, tn } from './i18n.js';
import {
  answeredCount,
  canSubmit,
  openAttempt,
  paragraphs,
  pickAnswers,
  reportablePercent,
  resultSummary,
  reviewOptionState,
} from './reading-quiz.js';
import { bookmarkButton, levelBadge, minutesText, progressText } from './reading-ui.js';
import { createWriter, progressWorthSending, readPercent } from './reading-sync.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
const slug = queryParam('slug');
const PASS_MARK = 70;

const state = {
  article: null,
  attempt: null, // open attempt (with `questions`), or null
  answers: {},
  history: [],
  localPercent: 0,
  dwell: 0,
  interacted: false,
  progressWriter: null,
  answersWriter: null,
  attemptRequest: 0,
};

/* ── loading and article rendering ─────────────────────────────────────── */

function showMissing() {
  $('article-loading').hidden = true;
  $('article').hidden = true;
  $('article-missing').hidden = false;
}

function showError(message) {
  $('article-loading').hidden = true;
  $('article-error-text').textContent = message;
  $('article-error').hidden = false;
}

function paintProgress(percent) {
  $('read-progress-bar').style.width = `${percent}%`;
  $('read-progress').setAttribute('aria-valuenow', String(percent));
}

function paintStatus() {
  const text = progressText(state.article.progress);
  $('article-status').textContent = text ?? '';
  $('article-status').classList.toggle('is-done', state.article.progress?.status === 'completed');
}

function renderArticle(article) {
  document.title = `${article.title} — Fleng`;
  $('article-meta').replaceChildren(
    levelBadge(article.level),
    el('span', undefined, minutesText(article.readingMinutes)),
    el('span', undefined, article.category.title),
  );
  $('article-title').textContent = article.title;
  $('article-description').textContent = article.description;
  $('article-bookmark').replaceChildren(
    bookmarkButton(article, {
      onChange: () => {
        $('article-feedback').textContent = '';
      },
      onError: (message) => {
        $('article-feedback').textContent = message;
      },
    }),
  );
  if (article.coverImageUrl) {
    $('article-cover').src = article.coverImageUrl;
    $('article-cover').alt = article.coverAlt || '';
    $('article-cover').hidden = false;
  }
  $('article-body').replaceChildren(
    ...paragraphs(article.content).map((text) => el('p', undefined, text)),
  );
  paintStatus();
  state.localPercent = article.progress?.readPercent ?? 0;
  paintProgress(state.localPercent);
  setupResume(article);
  $('article-loading').hidden = true;
  $('article').hidden = false;
}

function setupResume(article) {
  const percent = article.progress?.readPercent ?? 0;
  const button = $('article-resume');
  if (percent < 5 || percent > 95) return;
  button.textContent = t('rd.resume', { percent });
  button.hidden = false;
  button.addEventListener('click', () => {
    const rect = $('article-body').getBoundingClientRect();
    const target =
      window.scrollY + rect.top + (rect.height * percent) / 100 - window.innerHeight * 0.6;
    window.scrollTo({ top: Math.max(0, target), behavior: 'smooth' });
    button.hidden = true;
  });
}

/* ── reading progress (throttled) ──────────────────────────────────────── */

function setupProgressTracking(article) {
  state.progressWriter = createWriter({
    write: (percent) =>
      updateReadingProgress(article.slug, percent).then((row) => {
        article.progress = row;
        paintStatus();
      }),
    shouldSend: progressWorthSending,
    delayMs: 1500,
    minIntervalMs: 5000, // at most 12 writes a minute; the server allows 60
  });
  for (const type of ['scroll', 'wheel', 'touchstart', 'keydown', 'pointerdown']) {
    window.addEventListener(
      type,
      () => {
        state.interacted = true;
      },
      { passive: true, once: false },
    );
  }
  setInterval(() => {
    if (state.interacted && document.visibilityState === 'visible') state.dwell += 1;
  }, 1000);

  let scheduled = false;
  const measure = () => {
    scheduled = false;
    const rect = $('article-body').getBoundingClientRect();
    const raw = readPercent({ top: rect.top, height: rect.height, viewport: window.innerHeight });
    const percent = reportablePercent(raw, state.dwell, article.readingMinutes);
    if (percent > state.localPercent) {
      state.localPercent = percent;
      paintProgress(percent);
      state.progressWriter.set(percent);
    }
  };
  const onScroll = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(measure);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  // Re-measure as dwell time elapses, so a short article can still reach 100% without scrolling.
  setInterval(onScroll, 2000);
  const flush = () => {
    void state.progressWriter.flush();
  };
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);
}

/* ── quiz ──────────────────────────────────────────────────────────────── */

function showQuizError(message = '') {
  $('quiz-error').textContent = message;
  $('quiz-error').hidden = !message;
}

function button(label, className, onClick) {
  const node = el('button', className, label);
  node.type = 'button';
  node.addEventListener('click', onClick);
  return node;
}

function renderQuizIntro() {
  state.answersWriter?.dispose();
  state.attempt = null;
  showQuizError();
  const open = openAttempt(state.history);
  const body = el('div', 'reading-quiz-intro');
  body.append(el('p', 'dashboard-muted', t('rd.quizIntro', { mark: PASS_MARK })));
  const count = state.article.questionCount;
  body.append(
    el(
      'p',
      'reading-quiz-facts',
      `${tn('rd.questions', count, { n: count })} · ${tn('rd.points', state.article.pointsPossible, { n: state.article.pointsPossible })}`,
    ),
  );
  const submitted = state.history.filter((attempt) => attempt.status === 'submitted');
  const label = open
    ? t('rd.quizResume')
    : submitted.length
      ? t('rd.quizRetry')
      : t('rd.quizStart');
  const start = button(label, 'lesson-button lesson-button-primary', () => startQuiz(start));
  body.append(start);
  if (submitted.length) {
    const list = el('ul', 'reading-history');
    list.setAttribute('aria-label', t('rd.history'));
    for (const attempt of submitted) {
      const stateLabel = attempt.passed ? t('rd.attemptPassed') : t('rd.attemptFailed');
      list.append(
        el(
          'li',
          attempt.passed ? 'is-done' : '',
          `${t('rd.attemptN', { n: attempt.attemptNumber })} — ${t('rd.attemptScore', { score: attempt.scorePercent, state: stateLabel })}`,
        ),
      );
    }
    body.append(el('h3', 'reading-history-title', t('rd.history')), list);
  }
  $('quiz-body').replaceChildren(body);
}

async function startQuiz(trigger) {
  const request = ++state.attemptRequest;
  trigger.disabled = true;
  showQuizError();
  try {
    const attempt = await startReadingAttempt(state.article.slug);
    if (request !== state.attemptRequest) return;
    state.attempt = attempt;
    state.answers = { ...attempt.answers };
    renderQuestions();
  } catch (error) {
    trigger.disabled = false;
    if (error.status === 404) {
      showMissing();
      return;
    }
    showQuizError(error.status ? describeApiError(error) : t('rd.quizStartFailed'));
  }
}

function saveStateText(status) {
  return (
    {
      pending: t('rd.savePending'),
      saving: t('rd.saveSaving'),
      saved: t('rd.saveSaved'),
      error: t('rd.saveError'),
      idle: '',
    }[status] ?? ''
  );
}

function renderQuestions() {
  const { attempt } = state;
  const questions = attempt.questions;
  const form = el('form', 'reading-questions');
  form.noValidate = true;
  const saveNote = el('p', 'reading-save-state', '');
  saveNote.setAttribute('role', 'status');
  const counter = el('p', 'reading-counter', '');
  const submit = el('button', 'lesson-button lesson-button-primary', t('rd.submit'));
  submit.type = 'submit';
  const hint = el('p', 'dashboard-muted', t('rd.submitNeedsAll'));

  const refresh = () => {
    counter.textContent = t('rd.answered', {
      done: answeredCount(questions, state.answers),
      total: questions.length,
    });
    submit.disabled = !canSubmit(questions, state.answers);
    hint.hidden = !submit.disabled;
  };

  state.answersWriter?.dispose();
  state.answersWriter = createWriter({
    write: (answers) => saveReadingAnswers(attempt.id, answers),
    delayMs: 1200,
    minIntervalMs: 3000, // at most 20 writes a minute; the server allows 30
    onState: (status) => {
      saveNote.textContent = saveStateText(status);
      saveNote.classList.toggle('is-error', status === 'error');
    },
  });

  questions.forEach((question, index) => {
    const fieldset = el('fieldset', 'reading-question');
    const legend = el('legend');
    legend.append(
      el(
        'span',
        'reading-question-n',
        t('rd.questionN', { n: index + 1, total: questions.length }),
      ),
      el('span', 'reading-question-prompt', question.prompt),
    );
    const options = el('div', 'lesson-options');
    for (const answer of question.answers) {
      const label = el('label', 'lesson-option');
      const input = el('input');
      input.type = 'radio';
      input.name = `q-${question.id}`;
      input.value = answer.id;
      input.checked = state.answers[question.id] === answer.id;
      input.addEventListener('change', () => {
        state.answers[question.id] = answer.id;
        state.answersWriter.set({ ...state.answers });
        refresh();
      });
      label.append(input, el('span', undefined, answer.text));
      options.append(label);
    }
    fieldset.append(legend, options);
    form.append(fieldset);
  });

  const footer = el('div', 'reading-quiz-footer');
  footer.append(counter, saveNote, hint, submit);
  form.append(footer);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    void submitQuiz(submit);
  });
  refresh();
  saveNote.textContent = '';
  $('quiz-body').replaceChildren(form);
}

async function submitQuiz(submit) {
  const { attempt } = state;
  const answers = pickAnswers(attempt.questions, state.answers);
  submit.disabled = true;
  submit.textContent = t('rd.submitting');
  showQuizError();
  // The full answer set travels with the submit, so pending autosaves can be dropped safely.
  state.answersWriter.dispose();
  try {
    const done = await submitReadingAttempt(attempt.id, answers);
    state.attempt = null;
    await refreshAfterSubmit();
    renderResult(done.result);
  } catch (error) {
    if (error.status === 404) {
      showMissing();
      return;
    }
    showQuizError(describeApiError(error));
    submit.disabled = false;
    submit.textContent = t('rd.submit');
    renderQuestions();
  }
}

async function refreshAfterSubmit() {
  try {
    const [article, history] = await Promise.all([
      getReadingArticle(state.article.slug),
      listReadingAttempts(state.article.slug),
    ]);
    state.article = { ...state.article, progress: article.progress };
    state.history = history;
    paintStatus();
  } catch {
    /* The result is already known; the history refreshes on the next visit. */
  }
}

function reviewItem(item, index) {
  const node = el('div', 'reading-review-item');
  node.append(el('p', 'reading-question-prompt', `${index + 1}. ${item.prompt}`));
  const options = el('div', 'lesson-options');
  for (const answer of item.answers) {
    const mode = reviewOptionState(item, answer.id);
    const cls = mode.startsWith('correct')
      ? ' is-correct'
      : mode === 'wrong-chosen'
        ? ' is-incorrect'
        : '';
    const row = el('div', `lesson-option reading-review-option${cls}`);
    row.append(el('span', undefined, answer.text));
    const tag = {
      'correct-chosen': `${t('rd.yourAnswer')} · ${t('rd.correct')}`,
      correct: t('rd.correctAnswer'),
      'wrong-chosen': `${t('rd.yourAnswer')} · ${t('rd.incorrect')}`,
    }[mode];
    if (tag) row.append(el('small', 'reading-review-tag', tag));
    options.append(row);
  }
  node.append(options);
  if (item.selectedAnswerId == null) node.append(el('p', 'dashboard-muted', t('rd.noAnswer')));
  if (item.explanation)
    node.append(el('p', 'reading-explanation', `${t('rd.explanation')}: ${item.explanation}`));
  return node;
}

function renderResult(result) {
  const summary = resultSummary(result);
  const box = el('div', `reading-result ${summary.passed ? 'is-pass' : 'is-fail'}`);
  box.setAttribute('role', 'status');
  box.append(
    el('h3', undefined, summary.passed ? t('rd.resultPassed') : t('rd.resultFailed')),
    el(
      'p',
      'reading-score',
      t('rd.scoreValue', {
        earned: result.pointsEarned,
        possible: result.pointsPossible,
        percent: summary.percent,
      }),
    ),
  );
  if (summary.showXp) box.append(el('p', 'reading-xp', t('rd.xpEarned', { xp: summary.xp })));
  else if (summary.alreadyEarned) box.append(el('p', 'dashboard-muted', t('rd.xpAlready')));
  const actions = el('div', 'reading-actions');
  actions.append(button(t('rd.quizRetry'), 'lesson-button lesson-button-primary', renderQuizIntro));
  const back = el('a', 'lesson-button lesson-button-secondary', t('rd.backToList'));
  back.href = '/reading.html';
  actions.append(back);
  const review = el('section', 'reading-review');
  review.append(el('h3', undefined, t('rd.reviewTitle')), ...result.questions.map(reviewItem));
  $('quiz-body').replaceChildren(box, actions, review);
  box.setAttribute('tabindex', '-1');
  box.focus();
}

async function setupQuiz(article) {
  if (!article.questionCount) return;
  $('quiz').hidden = false;
  try {
    state.history = await listReadingAttempts(article.slug);
  } catch {
    state.history = []; // history is optional; starting a quiz still resumes an open attempt
  }
  renderQuizIntro();
}

/* ── start ─────────────────────────────────────────────────────────────── */

async function init() {
  $('article-error').hidden = true;
  if (!slug) {
    showMissing();
    return;
  }
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    const article = await getReadingArticle(slug);
    state.article = article;
    renderArticle(article);
    setupProgressTracking(article);
    await setupQuiz(article);
  } catch (error) {
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    if (error.status === 404) {
      showMissing();
      return;
    }
    showError(describeApiError(error));
  }
}

$('article-retry').addEventListener('click', () => window.location.reload());
mountWorkspace('reading');
void init();
