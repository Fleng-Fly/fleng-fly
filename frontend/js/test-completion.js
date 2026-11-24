import { el } from './layout.js';
import { t } from './i18n.js';

export function elapsedSeconds(start, end) {
  if (start == null || end == null) return undefined;
  const seconds = (new Date(end) - new Date(start)) / 1000;
  return Number.isFinite(seconds) && seconds >= 0 ? Math.floor(seconds) : undefined;
}

function action(label, handler, primary = false) {
  const node = el(typeof handler === 'string' ? 'a' : 'button',
    `btn btn-${primary ? 'primary' : 'secondary'}`, label);
  if (typeof handler === 'string') node.href = handler;
  else {
    node.type = 'button';
    node.addEventListener('click', handler);
  }
  return node;
}

function reviewRow(item) {
  const row = el('li', 'completion-row');
  const details = el('details');
  details.append(el('summary', undefined, item.title));
  if (item.errors?.length) {
    for (const { answer, expected } of item.errors) {
      if (answer != null) details.append(el('p', undefined, t('completion.yourAnswer', { answer })));
      if (expected != null) details.append(el('p', undefined, t('completion.correctAnswer', { answer: expected })));
    }
  } else {
    if (item.answer != null) details.append(el('p', undefined, t('completion.yourAnswer', { answer: item.answer })));
    if (item.expected != null) details.append(el('p', undefined, t('completion.correctAnswer', { answer: item.expected })));
  }
  if (item.note) details.append(el('p', undefined, item.note));
  if (details.children.length > 1) row.append(details);
  else row.append(el('span', undefined, item.title));
  if (item.mistake != null) {
    row.append(el('span', item.mistake ? 'completion-mistake' : 'completion-correct',
      t(item.mistake ? 'completion.mistake' : 'completion.correct')));
  }
  return { row, details, mistake: item.mistake };
}

/** Renders an already confirmed result. Actions belong to the owning test. */
export function renderTestCompletion(target, {
  headingId, title, subtitle, correct, total, firstTry, mistakes, retries, seconds, xp,
  items = [], previousItems = [], retryMistakes, tryAgain, finish, continueLearning, extra, animate = true,
}) {
  const perfect = total > 0 && firstTry === total;
  const section = el('section', `test-completion${perfect ? ' is-perfect' : ''}${animate ? ' is-animated' : ''}`);
  section.setAttribute('aria-labelledby', headingId);
  const award = el('div', 'completion-award', perfect ? '🏅' : '🏆');
  award.setAttribute('aria-hidden', 'true');
  const particles = el('div', 'completion-particles');
  particles.setAttribute('aria-hidden', 'true');
  for (let index = 0; animate && index < (perfect ? 24 : 12); index++) {
    const dot = el('i', undefined, index % 3 === 0 ? '✦' : '');
    const angle = index * 2.4;
    const radius = 75 + index % 4 * 22;
    dot.style.setProperty('--x', `${Math.cos(angle) * radius}px`);
    dot.style.setProperty('--y', `${Math.sin(angle) * radius}px`);
    particles.append(dot);
  }
  const heading = el('h2', undefined, title);
  heading.id = headingId;
  heading.tabIndex = -1;
  section.append(particles, award, heading);
  if (perfect) section.append(el('p', 'completion-perfect', t('completion.perfect')));
  if (subtitle) section.append(el('p', 'completion-subtitle', subtitle));
  const score = firstTry ?? correct;
  if (score != null && total > 0) {
    const percent = score === total ? 100 : Math.min(99, Math.round(100 * score / total));
    const label = t(firstTry == null ? 'completion.score' : 'completion.firstTry');
    const caption = el('div', 'completion-score');
    caption.append(el('span', undefined, label), el('strong', undefined, `${percent}%`));
    const bar = el('div', 'completion-bar');
    bar.setAttribute('role', 'meter');
    bar.setAttribute('aria-label', label);
    bar.setAttribute('aria-valuemin', '0');
    bar.setAttribute('aria-valuemax', '100');
    bar.setAttribute('aria-valuenow', String(percent));
    const fill = el('span');
    fill.style.width = `${percent}%`;
    bar.append(fill);
    section.append(caption, bar);
  }

  const metrics = el('dl', 'completion-metrics');
  const time = seconds == null ? undefined : `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  let xpCounter;
  for (const [key, value] of Object.entries({ correct, total, mistakes, retries, time, xp })) {
    if (value == null) continue;
    const metric = el('div');
    metric.style.setProperty('--order', metrics.children.length);
    const amount = el('dd', undefined, String(value));
    if (key === 'xp') {
      xpCounter = el('span', undefined, String(value));
      xpCounter.setAttribute('aria-hidden', 'true');
      amount.replaceChildren(el('span', 'sr-only', String(value)), xpCounter);
    }
    metric.append(el('dt', undefined, t(`completion.${key}`)), amount);
    metrics.append(metric);
  }
  section.append(metrics);
  if (extra) section.append(extra);

  const actions = el('div', 'completion-actions');
  const review = el('section', 'completion-review');
  const reviewTitle = el('h3', undefined, t('completion.reviewed'));
  reviewTitle.tabIndex = -1;
  const rows = items.map(reviewRow);
  if (rows.some(({ mistake }) => mistake)) {
    const toggle = action(t('completion.reviewMistakes'), () => {
      const filtered = toggle.getAttribute('aria-pressed') !== 'true';
      toggle.setAttribute('aria-pressed', String(filtered));
      for (const { row, details, mistake } of rows) {
        row.hidden = filtered && !mistake;
        if (filtered && mistake) details.open = true;
      }
      reviewTitle.textContent = t(filtered ? 'completion.reviewMistakes' : 'completion.reviewed');
      reviewTitle.focus();
    });
    toggle.setAttribute('aria-pressed', 'false');
    actions.append(toggle);
  }
  if (retryMistakes) actions.append(action(t('completion.retryMistakes'), retryMistakes, !continueLearning));
  if (tryAgain) actions.append(action(t('common.tryAgain'), tryAgain));
  if (finish) actions.append(action(t('completion.finish'), finish, typeof continueLearning !== 'string' && !retryMistakes));
  if (typeof continueLearning === 'string') {
    actions.append(action(t('completion.continue'), continueLearning, true));
  } else if (continueLearning) {
    void continueLearning.then((href) => {
      if (href && section.isConnected) actions.append(action(t('completion.continue'), href, true));
    });
  }
  section.append(actions);
  if (rows.length) {
    const list = el('ul');
    list.append(...rows.map(({ row }) => row));
    review.append(reviewTitle, list);
    section.append(review);
  }
  if (previousItems.length) {
    const previous = el('details', 'completion-review completion-previous');
    const list = el('ul');
    list.append(...previousItems.map((item) => reviewRow(item).row));
    previous.append(el('summary', undefined, t('completion.previousMistakes')), list);
    section.append(previous);
  }
  const backdrop = el('div', 'completion-backdrop');
  backdrop.setAttribute('aria-hidden', 'true');
  target.replaceChildren(...(animate ? [backdrop, section] : [section]));

  if (animate && xpCounter && xp > 0 && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
    const start = performance.now();
    xpCounter.textContent = '0';
    function count(now) {
      if (!xpCounter.isConnected) return;
      const fraction = Math.min(1, (now - start) / 750);
      xpCounter.textContent = String(Math.round(xp * fraction));
      if (fraction < 1) requestAnimationFrame(count);
    }
    requestAnimationFrame(count);
  }
  return heading;
}
