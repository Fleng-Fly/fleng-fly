import { elapsedSeconds, TestCompletionScreen } from './test-completion.js';
import { el } from './layout.js';
import { getLang, t } from './i18n.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { describeApiError } from './errors.js';
import { completePlacement, getPlacement, listPlacements, retryPlacementMistakes, savePlacementAnswer, startPlacement } from './placement-api.js';

const $ = (id) => document.getElementById(id);
let attempt = null, index = 0, busy = false, ready = false, historyBusy = false, historyOffset = 0;
let retryAction = main;
let latestLevel = null; // estimated level of the newest completed attempt (history is newest first)
mountWorkspace('placement');

/** Highlights the learner's latest completed estimate in the CEFR row. */
function markCurrentLevel() {
  for (const card of document.querySelectorAll('#placement-levels li')) {
    const current = card.dataset.level === latestLevel;
    card.classList.toggle('is-current', current);
    card.querySelector('.pt-current')?.remove();
    if (current) card.prepend(el('span', 'pt-current', t('pt.current')));
  }
}
function status(text) { $('placement-status').textContent = text; }
function showError(error, retry) {
  $('placement-error-text').textContent = describeApiError(error);
  $('placement-error').hidden = false;
  retryAction = retry;
}
function controls() {
  $('placement-start').disabled = busy || !ready;
  $('placement-skip').disabled = busy || !attempt || index === -1;
  for (const node of $('placement-question').querySelectorAll('input')) node.disabled = busy;
}
function adopt(value) {
  attempt = value;
  index = attempt.questions.findIndex((question) => !Object.hasOwn(attempt.answers, question.id));
  const url = new URL(location.href); url.searchParams.set('attempt', attempt.id);
  history.replaceState(null, '', url);
  $('placement-error').hidden = true;
  const answering = attempt.status === 'in_progress';
  $('placement-player').hidden = !answering;
  // While answering, only the questions are shown; the landing blocks return afterwards.
  $('placement-intro').hidden = answering;
  $('placement-levels').hidden = answering;
  $('placement-result').hidden = attempt.status !== 'completed';
  if (attempt.status === 'completed') renderResult();
  else if (index !== -1) renderQuestion(true);
  else $('placement-question').replaceChildren();
}
function renderQuestion(focus = false) {
  const question = attempt.questions[index];
  $('placement-count').textContent = t('pt.questionOf', { n: index + 1, total: attempt.total });
  $('placement-saved').textContent = t('pt.savedCount', { done: attempt.answered, total: attempt.total });
  $('placement-progress').max = attempt.total;
  $('placement-progress').value = attempt.answered;
  const field = el('fieldset');
  const heading = el('legend', undefined, question.prompt);
  heading.tabIndex = -1; field.append(heading);
  for (const option of question.options) {
    const label = el('label', 'placement-option');
    const radio = el('input'); radio.type = 'radio'; radio.name = 'placement-answer';
    radio.value = option.id; radio.checked = attempt.answers[question.id] === option.id;
    radio.addEventListener('change', () => saveOutcome(question, option.id));
    label.append(radio, el('span', undefined, option.text)); field.append(label);
  }
  $('placement-question').replaceChildren(field);
  controls(); if (focus) heading.focus();
}
function renderResult() {
  const { result } = attempt;
  const extra = el('div', 'completion-extra');
  extra.append(el('p', undefined, t('pt.score', { correct: result.correct, total: result.total, range: result.assessmentRange })));
  const limitations = el('ul');
  for (const text of result.limitations) limitations.append(el('li', undefined, text));
  extra.append(limitations, el('p', 'muted', t('pt.disclaimer')), el('p', 'muted', t('pt.note')));
  const bands = el('ul', 'placement-band-list');
  for (const band of result.bands) bands.append(el('li', undefined, `${band.level}: ${band.correct}/${band.total}${['C1', 'C2'].includes(band.level) ? t('pt.exploratory') : ''}`));
  extra.append(bands, el('h3', undefined, t('pt.suggested')), el('p', 'muted', attempt.recommendationNote));
  const courses = el('ul');
  for (const course of attempt.recommendedCourses) {
    const link = el('a', 'btn btn-primary', t('pt.startCourse', { title: course.title, level: course.level }));
    link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
    const item = el('li'); item.append(link); courses.append(item);
  }
  extra.append(courses);
  const questions = new Map(attempt.questions.map((question) => [question.id, question]));
  // Older attempts allowed editing an answer before completion.
  const legacy = attempt.scoringVersion === 'conservative-1';
  let firstChoices = {};
  if (legacy) {
    try { firstChoices = JSON.parse(sessionStorage.getItem(`fleng.placement.first-answers:${attempt.id}`)) ?? {}; }
    catch { /* The final score and saved review are still available. */ }
  }
  const firstTry = !legacy ? result.correct
    : result.review.every(({ questionId }) => firstChoices[questionId] != null)
      ? result.review.filter(({ questionId, correctOptionId }) => firstChoices[questionId] === correctOptionId).length
      : undefined;
  const previousItems = [];
  const items = result.review.map((review) => {
    const question = questions.get(review.questionId);
    const skipped = review.selectedOptionId == null;
    const expected = question.options.find((option) => option.id === review.correctOptionId)?.text;
    const first = firstChoices[question.id];
    if (first && first !== review.correctOptionId && first !== review.selectedOptionId) {
      previousItems.push({
        title: question.prompt, mistake: true,
        answer: question.options.find((option) => option.id === first)?.text, expected,
      });
    }
    return {
      title: question.prompt, skipped, mistake: !review.isCorrect && !skipped,
      answer: question.options.find((option) => option.id === review.selectedOptionId)?.text,
      expected,
      note: review.explanation,
    };
  });
  TestCompletionScreen($('placement-result'), {
    headingId: 'placement-completion-title',
    title: t(attempt.practice ? 'vocab.complete' : 'completion.placement'),
    subtitle: attempt.practice ? t('completion.placementPractice') : result.label,
    level: result.estimatedLevel,
    correct: result.correct,
    total: result.total,
    firstTry,
    skipped: items.filter((item) => item.skipped).length,
    mistakes: items.filter((item) => item.mistake).length,
    seconds: elapsedSeconds(attempt.startedAt, attempt.completedAt),
    items,
    previousItems,
    tryAgain: () => startNewAttempt(),
    retryMistakes: items.some((item) => item.mistake)
      ? () => startNewAttempt(() => retryPlacementMistakes(attempt.id))
      : undefined,
    backToCourses: true,
    continueLearning: attempt.recommendedCourses[0]
      ? `/course.html?slug=${encodeURIComponent(attempt.recommendedCourses[0].slug)}` : undefined,
    extra: attempt.practice ? undefined : extra,
  }).focus();
}

async function openAttempt(id) {
  if (busy) return;
  busy = true; controls(); status(t('pt.loadingAttempt'));
  try {
    adopt(await getPlacement(id));
    if (attempt.status === 'in_progress' && index === -1) await finishAttempt();
    else status(t('pt.loaded'));
  }
  catch (error) { showError(error, () => openAttempt(id)); status(''); }
  finally { busy = false; controls(); }
}
async function loadHistory(reset = true) {
  if (historyBusy) return;
  historyBusy = true; $('placement-history-refresh').disabled = true;
  $('placement-history-more').disabled = true;
  if (reset) { historyOffset = 0; latestLevel = null; $('placement-history-list').replaceChildren(); }
  $('placement-history-status').textContent = t('pt.loadingAttempts');
  try {
    const rows = await listPlacements(historyOffset);
    for (const row of rows) {
      const done = row.status === 'completed';
      const item = el('li', 'pt-attempt');
      const date = new Date(row.startedAt).toLocaleDateString(getLang(), { day: 'numeric', month: 'short', year: 'numeric' });
      const open = el('button', 'pt-link', done ? t('pt.viewResults') : t('pt.resume', { done: row.answered, total: row.total }));
      open.type = 'button'; open.addEventListener('click', () => openAttempt(row.id));
      item.append(
        el('span', `pt-badge${done && row.estimatedLevel ? '' : ' is-empty'}`, done ? row.estimatedLevel || '–' : '…'),
        el('span', 'pt-attempt-date', date),
        el('span', 'pt-attempt-score', done ? t('pt.scoreShort', { correct: row.correct ?? 0, total: row.total }) : t('pt.inProgress')),
        open,
      );
      $('placement-history-list').append(item);
      if (done && row.estimatedLevel && !latestLevel) latestLevel = row.estimatedLevel;
    }
    markCurrentLevel();
    historyOffset += rows.length;
    $('placement-history-more').hidden = rows.length < 20;
    $('placement-history-status').textContent = historyOffset ? '' : t('pt.noAttempts');
  } catch (error) { $('placement-history-status').textContent = describeApiError(error); }
  finally { historyBusy = false; $('placement-history-refresh').disabled = false; $('placement-history-more').disabled = false; }
}
async function startNewAttempt(start = startPlacement) {
  if (busy || !ready) return;
  busy = true; controls(); status(t('pt.starting'));
  try { adopt(await start()); status(t('pt.chooseOne')); await loadHistory(); }
  catch (error) { showError(error, () => startNewAttempt(start)); status(t('pt.startLost')); }
  finally { busy = false; controls(); }
}
$('placement-start').addEventListener('click', () => startNewAttempt());
async function finishAttempt() {
  status(t('pt.checkingAnswers'));
  adopt(await completePlacement(attempt.id));
  status(t('pt.resultSaved'));
  await loadHistory();
}

async function saveOutcome(question, optionId) {
  if (busy || attempt?.questions[index]?.id !== question.id) return;
  busy = true; controls(); status(t('pt.saving'));
  try {
    adopt(await savePlacementAnswer(attempt.id, question.id, optionId));
    if (index === -1) await finishAttempt();
    else status(t('pt.saved'));
  } catch (error) {
    if (index !== -1) renderQuestion();
    showError(error, () => openAttempt(attempt.id));
    status(t(index === -1 ? 'pt.finishFailed' : 'pt.saveFailed'));
  } finally { busy = false; controls(); }
}

$('placement-form').addEventListener('submit', (event) => event.preventDefault());
$('placement-skip').addEventListener('click', () => {
  if (attempt?.questions[index]) void saveOutcome(attempt.questions[index], null);
});
$('placement-history-refresh').addEventListener('click', () => loadHistory());
$('placement-history-more').addEventListener('click', () => loadHistory(false));
$('placement-retry').addEventListener('click', () => retryAction());
async function main() {
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    ready = true; $('placement-error').hidden = true; controls(); status(t('pt.ready'));
    await loadHistory();
    const id = new URLSearchParams(location.search).get('attempt');
    if (id) await openAttempt(id);
  } catch (error) { status(''); showError(error, main); }
}
main();
