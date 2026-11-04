import { el } from './layout.js';

/** Counts come from /progress/me, never from a local progress cache. */
export function courseProgress(progress) {
  const total = progress.lessonsTotal;
  const done = progress.lessonsCompleted;
  const percent = total ? Math.min(100, Math.round((done / total) * 100)) : 0;
  const complete = total > 0 && done >= total;
  const node = el('div', `catalog-progress${complete ? ' is-complete' : ''}`);
  const caption = el('div', 'catalog-progress-caption');
  caption.append(
    el('span', undefined, `${done} of ${total} lessons completed`),
    el('span', undefined, complete ? 'Completed' : `${percent}%`),
  );
  const track = el('div', 'catalog-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', 'Course completion');
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.setAttribute('aria-valuenow', String(percent));
  const fill = el('span', 'catalog-fill');
  fill.style.width = `${percent}%`;
  track.append(fill);
  node.append(caption, track);
  return node;
}

export function catalogMessage(container, title, detail, action, label = 'Try again') {
  const card = el('div', 'catalog-panel catalog-message');
  card.setAttribute('role', 'status');
  card.append(el('h2', undefined, title), el('p', 'dashboard-muted', detail));
  if (action) {
    const button = el('button', 'catalog-button is-secondary', label);
    button.type = 'button';
    button.addEventListener('click', action);
    card.append(button);
  }
  container.replaceChildren(card);
}
