import { getMyProgress } from './api.js';
import { describeApiError } from './errors.js';
import { el, mountHeader } from './layout.js';
import { requireSession } from './session.js';

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = String(value);
}

function renderProfile(user) {
  setText('user-name', user.displayName);
  setText('user-email', user.email);
  setText('user-level', user.level);
  setText('user-xp', user.xp);
}

function renderProgressError(error) {
  const container = document.getElementById('progress-body');
  container.textContent = '';
  const card = el('div', 'card');
  const title = el('h3', undefined, 'Could not load your progress');
  const message = el('p', 'muted text-sm', describeApiError(error));
  const retry = el('button', 'btn btn-secondary', 'Try again');
  retry.type = 'button';
  retry.addEventListener('click', loadProgress);
  card.append(title, message, retry);
  container.append(card);
}

async function loadProgress() {
  const container = document.getElementById('progress-body');
  container.textContent = '';
  container.append(el('p', 'muted', 'Loading your progress…'));
  try {
    const progress = await getMyProgress();
    container.textContent = '';
    const grid = el('div', 'stat-grid');
    for (const [label, value] of [
      ['Lessons completed', progress.lessonsCompleted],
      ['Lessons started', progress.lessonsStarted],
      ['Study minutes', progress.studyMinutes],
    ]) {
      const stat = el('div', 'stat');
      stat.append(el('div', 'stat-label', label), el('div', 'stat-value', String(value)));
      grid.append(stat);
    }
    container.append(grid);
  } catch (error) {
    renderProgressError(error);
  }
}

async function main() {
  const user = await requireSession();
  if (!user) return;
  await mountHeader('dashboard', user);
  renderProfile(user);
  loadProgress();
}

main();
