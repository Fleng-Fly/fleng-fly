import { el } from './layout.js';
import { requireSession } from './session.js';
import { describeApiError } from './errors.js';
import { completePlacement, getPlacement, listPlacements, savePlacementAnswer, startPlacement } from './placement-api.js';

const $ = (id) => document.getElementById(id);
let attempt = null, index = 0, busy = false, ready = false, historyBusy = false, historyOffset = 0;
let retryAction = main;

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
  $('placement-player').hidden = attempt.status !== 'in_progress';
  $('placement-result').hidden = attempt.status !== 'completed';
  if (attempt.status === 'completed') renderResult();
  else renderQuestion();
}
function renderQuestion(focus = false) {
  const question = attempt.questions[index];
  $('placement-count').textContent = `Question ${index + 1} of ${attempt.total}`;
  $('placement-saved').textContent = `${attempt.answered} of ${attempt.total} answers saved`;
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
      busy = true; controls(); status('Saving your answer…');
      try {
        const saved = await savePlacementAnswer(attempt.id, question.id, option.id);
        adopt(saved); status('Answer saved. You can change it before finishing.');
      } catch (error) {
        renderQuestion();
        showError(error, () => openAttempt(attempt.id));
        status('Could not confirm the save. Reload this attempt before continuing.');
      } finally { busy = false; controls(); $('placement-question').querySelector('input:checked')?.focus(); }
    });
    label.append(radio, el('span', undefined, option.text)); field.append(label);
  }
  $('placement-question').replaceChildren(field);
  controls(); if (focus) heading.focus();
}
function renderResult() {
  const target = $('placement-result'), result = attempt.result;
  target.replaceChildren(el('h2', undefined, result.label), el('p', undefined, `${result.correct} / ${result.total} correct · assessment range ${result.assessmentRange} · limited reliability`));
  const limitations = el('ul');
  for (const text of result.limitations) limitations.append(el('li', undefined, text));
  target.append(limitations);
  const bands = el('ul', 'placement-band-list');
  for (const band of result.bands) bands.append(el('li', undefined, `${band.level}: ${band.correct}/${band.total}${['C1', 'C2'].includes(band.level) ? ' · exploratory' : ''}`));
  target.append(bands, el('h3', undefined, 'Suggested courses'), el('p', 'muted', attempt.recommendationNote));
  const courses = el('ul');
  for (const course of attempt.recommendedCourses) {
    const link = el('a', 'btn btn-primary', `Start ${course.title} · ${course.level}`);
    link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
    const item = el('li'); item.append(link); courses.append(item);
  }
  const dashboard = el('a', 'btn btn-secondary', 'Back to Dashboard');
  dashboard.href = '/dashboard.html';
  target.append(courses, dashboard, el('h3', undefined, 'Answer review'));
  for (const review of result.review) {
    const question = attempt.questions.find((item) => item.id === review.questionId);
    const details = el('details', 'placement-review');
    details.append(el('summary', undefined, `${review.isCorrect ? 'Correct' : 'Review'} · ${question.prompt}`));
    const selected = question.options.find((option) => option.id === review.selectedOptionId);
    const correct = question.options.find((option) => option.id === review.correctOptionId);
    details.append(el('p', undefined, `Your answer: ${selected.text}`), el('p', undefined, `Correct answer: ${correct.text}`), el('p', 'muted', review.explanation));
    target.append(details);
  }
}
async function openAttempt(id) {
  if (busy) return;
  busy = true; controls(); status('Loading your attempt…');
  try { index = 0; adopt(await getPlacement(id)); status('Attempt loaded.'); }
  catch (error) { showError(error, () => openAttempt(id)); status(''); }
  finally { busy = false; controls(); }
}
async function loadHistory(reset = true) {
  if (historyBusy) return;
  historyBusy = true; $('placement-history-refresh').disabled = true;
  $('placement-history-more').disabled = true;
  if (reset) { historyOffset = 0; $('placement-history-list').replaceChildren(); }
  $('placement-history-status').textContent = 'Loading attempts…';
  try {
    const rows = await listPlacements(historyOffset);
    for (const row of rows) {
      const item = el('li');
      const label = row.status === 'completed' ? `View result · ${row.resultLabel || row.estimatedLevel || 'See result'}` : `Resume · ${row.answered}/${row.total} saved`;
      const button = el('button', 'btn btn-secondary', `${new Date(row.startedAt).toLocaleString()} · ${label}`);
      button.type = 'button'; button.addEventListener('click', () => openAttempt(row.id)); item.append(button);
      $('placement-history-list').append(item);
    }
    historyOffset += rows.length;
    $('placement-history-more').hidden = rows.length < 20;
    $('placement-history-status').textContent = historyOffset ? '' : 'No attempts yet. Start whenever you are ready.';
  } catch (error) { $('placement-history-status').textContent = describeApiError(error); }
  finally { historyBusy = false; $('placement-history-refresh').disabled = false; $('placement-history-more').disabled = false; }
}
$('placement-start').addEventListener('click', async () => {
  if (busy || !ready) return;
  busy = true; controls(); status('Starting a new attempt…');
  try { index = 0; adopt(await startPlacement()); status('Choose one answer. Your choices are saved without revealing correctness.'); await loadHistory(); }
  catch (error) { showError(error, () => loadHistory()); status('If the response was lost, refresh history to find the new attempt.'); }
  finally { busy = false; controls(); }
});
$('placement-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || !attempt || attempt.answered !== attempt.total) return;
  busy = true; controls(); status('Checking your answers…');
  try { adopt(await completePlacement(attempt.id)); status('Result saved. Your learning progress and profile were not changed.'); await loadHistory(); }
  catch (error) { showError(error, () => openAttempt(attempt.id)); status('Could not confirm completion. Reload this attempt before retrying.'); }
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
    ready = true; $('placement-error').hidden = true; controls(); status('Ready when you are.');
    await loadHistory();
    const id = new URLSearchParams(location.search).get('attempt');
    if (id) await openAttempt(id);
  } catch (error) { status(''); showError(error, main); }
}
main();
