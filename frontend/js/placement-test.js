import { el } from './layout.js';
import { getLang, t } from './i18n.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { describeApiError } from './errors.js';
import { completePlacement, getPlacement, listPlacements, savePlacementAnswer, startPlacement } from './placement-api.js';

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
  $('placement-previous').disabled = busy || index === 0;
  $('placement-next').disabled = busy || !attempt || index >= attempt.questions.length - 1;
  $('placement-unanswered').disabled = busy || !attempt || attempt.answered === attempt.total;
  $('placement-finish').disabled = busy || !attempt || attempt.answered !== attempt.total;
  for (const node of $('placement-question').querySelectorAll('input')) node.disabled = busy;
}
function adopt(value) {
  attempt = value;
  index = Math.min(index, attempt.questions.length - 1);
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
  else renderQuestion();
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
    radio.addEventListener('change', async () => {
      if (busy) return;
      busy = true; controls(); status(t('pt.saving'));
      try {
        const saved = await savePlacementAnswer(attempt.id, question.id, option.id);
        adopt(saved); status(t('pt.saved'));
      } catch (error) {
        renderQuestion();
        showError(error, () => openAttempt(attempt.id));
        status(t('pt.saveFailed'));
      } finally { busy = false; controls(); $('placement-question').querySelector('input:checked')?.focus(); }
    });
    label.append(radio, el('span', undefined, option.text)); field.append(label);
  }
  $('placement-question').replaceChildren(field);
  controls(); if (focus) heading.focus();
}
function renderResult() {
  const target = $('placement-result'), result = attempt.result;
  target.replaceChildren(el('h2', undefined, result.label), el('p', undefined, t('pt.score', { correct: result.correct, total: result.total, range: result.assessmentRange })));
  const limitations = el('ul');
  for (const text of result.limitations) limitations.append(el('li', undefined, text));
  target.append(limitations, el('p', 'muted', t('pt.disclaimer')), el('p', 'muted', t('pt.note')));
  const bands = el('ul', 'placement-band-list');
  for (const band of result.bands) bands.append(el('li', undefined, `${band.level}: ${band.correct}/${band.total}${['C1', 'C2'].includes(band.level) ? t('pt.exploratory') : ''}`));
  target.append(bands, el('h3', undefined, t('pt.suggested')), el('p', 'muted', attempt.recommendationNote));
  const courses = el('ul');
  for (const course of attempt.recommendedCourses) {
    const link = el('a', 'btn btn-primary', t('pt.startCourse', { title: course.title, level: course.level }));
    link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
    const item = el('li'); item.append(link); courses.append(item);
  }
  const dashboard = el('a', 'btn btn-secondary', t('pt.toDashboard'));
  dashboard.href = '/dashboard.html';
  target.append(courses, dashboard, el('h3', undefined, t('pt.review')));
  for (const review of result.review) {
    const question = attempt.questions.find((item) => item.id === review.questionId);
    const details = el('details', 'placement-review');
    details.append(el('summary', undefined, `${review.isCorrect ? t('pt.correct') : t('pt.toReview')} · ${question.prompt}`));
    const selected = question.options.find((option) => option.id === review.selectedOptionId);
    const correct = question.options.find((option) => option.id === review.correctOptionId);
    details.append(el('p', undefined, t('pt.yourAnswer', { text: selected.text })), el('p', undefined, t('pt.correctAnswer', { text: correct.text })), el('p', 'muted', review.explanation));
    target.append(details);
  }
}
async function openAttempt(id) {
  if (busy) return;
  busy = true; controls(); status(t('pt.loadingAttempt'));
  try { index = 0; adopt(await getPlacement(id)); status(t('pt.loaded')); }
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
$('placement-start').addEventListener('click', async () => {
  if (busy || !ready) return;
  busy = true; controls(); status(t('pt.starting'));
  try { index = 0; adopt(await startPlacement()); status(t('pt.chooseOne')); await loadHistory(); }
  catch (error) { showError(error, () => loadHistory()); status(t('pt.startLost')); }
  finally { busy = false; controls(); }
});
$('placement-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || !attempt || attempt.answered !== attempt.total) return;
  busy = true; controls(); status(t('pt.checkingAnswers'));
  try { adopt(await completePlacement(attempt.id)); status(t('pt.resultSaved')); await loadHistory(); }
  catch (error) { showError(error, () => openAttempt(attempt.id)); status(t('pt.finishFailed')); }
  finally { busy = false; controls(); }
});
$('placement-previous').addEventListener('click', () => { if (!busy && index > 0) { index--; renderQuestion(true); } });
$('placement-next').addEventListener('click', () => { if (!busy && index < attempt.questions.length - 1) { index++; renderQuestion(true); } });
$('placement-unanswered').addEventListener('click', () => {
  if (busy || !attempt) return;
  const next = attempt.questions.findIndex((q) => !attempt.answers[q.id]);
  if (next >= 0) { index = next; renderQuestion(true); }
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
