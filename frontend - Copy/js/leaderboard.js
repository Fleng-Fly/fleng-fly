import { getLeaderboard } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const target = document.getElementById('leaderboard-body');
const number = new Intl.NumberFormat('en');
let sessionReady = false;

function avatar(entry) {
  const node = el(
    'span',
    `learner-avatar avatar-${(entry.rank - 1) % 3}`,
    entry.displayName.trim().charAt(0).toLocaleUpperCase() || 'F',
  );
  node.setAttribute('aria-hidden', 'true');
  return node;
}

function learner(entry) {
  const copy = el('span', 'learner-name', entry.displayName);
  if (entry.isCurrentUser) copy.append(el('small', 'learner-you', 'You'));
  return copy;
}

function podium(entry) {
  const card = el(
    'article',
    `podium-card podium-${entry.rank}${entry.isCurrentUser ? ' is-you' : ''}`,
  );
  card.append(
    el('span', 'podium-place', ['✦ FIRST PLACE', 'SECOND PLACE', 'THIRD PLACE'][entry.rank - 1]),
  );
  card.append(avatar(entry), learner(entry));
  card.append(el('strong', 'podium-xp', `${number.format(entry.xp)} XP`));
  card.append(
    el(
      'p',
      'dashboard-muted',
      `${number.format(entry.lessonsCompleted)} lessons · ${entry.streak} day streak`,
    ),
  );
  card.append(el('span', 'podium-rank', `#${entry.rank}`));
  return card;
}

function row(entry) {
  const tr = el('tr', entry.isCurrentUser ? 'current-learner' : '');
  tr.append(el('td', 'rank-cell', `#${entry.rank}`));
  const name = el('td');
  const identity = el('div', 'learner-identity');
  identity.append(avatar(entry), learner(entry));
  name.append(identity);
  tr.append(
    name,
    el('td', 'xp-cell', number.format(entry.xp)),
    el('td', undefined, number.format(entry.lessonsCompleted)),
    el('td', undefined, `${entry.streak} days`),
  );
  return tr;
}

function render(data) {
  target.replaceChildren();
  if (!data.entries.length) {
    message('A new leaderboard starts here.', 'Complete a lesson and start earning XP.');
    return;
  }
  const top = el('section', 'leaderboard-podium');
  top.setAttribute('aria-label', 'Top three learners');
  top.append(...data.entries.slice(0, 3).map(podium));
  const panel = el('section', 'dashboard-card leaderboard-panel');
  const heading = el('div', 'section-heading');
  heading.append(
    el('h2', undefined, 'The leaderboard'),
    el('span', 'dashboard-muted', `${number.format(data.total)} learners`),
  );
  const scroll = el('div', 'leaderboard-scroll');
  scroll.tabIndex = 0;
  scroll.setAttribute('role', 'region');
  scroll.setAttribute('aria-label', 'Learner rankings, scroll horizontally for all statistics');
  const table = el('table', 'leaderboard-table');
  const caption = el(
    'caption',
    'sr-only',
    'All-time ranking by XP. Equal XP is ordered by a permanent learner ID.',
  );
  const head = el('thead');
  const headers = el('tr');
  for (const label of ['Rank', 'Learner', 'XP', 'Lessons', 'Streak']) {
    const th = el('th', undefined, label);
    th.scope = 'col';
    headers.append(th);
  }
  head.append(headers);
  const body = el('tbody');
  body.append(...data.entries.map(row));
  table.append(caption, head, body);
  scroll.append(table);
  panel.append(heading, scroll);
  if (data.currentUser && !data.entries.some((entry) => entry.isCurrentUser)) {
    panel.append(
      el(
        'p',
        'own-rank',
        `Your position: #${data.currentUser.rank} · ${number.format(data.currentUser.xp)} XP · ${data.currentUser.lessonsCompleted} lessons · ${data.currentUser.streak} day streak`,
      ),
    );
  }
  panel.append(
    el(
      'p',
      'leaderboard-note dashboard-muted',
      'Ranked by total XP earned in lessons. Keep learning at your own pace.' +
        (data.total > data.entries.length ? ` Showing the top ${data.entries.length}.` : ''),
    ),
  );
  target.append(top, panel);
}

function message(title, detail, retry) {
  const card = el('div', 'dashboard-card leaderboard-message');
  card.append(el('h2', undefined, title), el('p', 'dashboard-muted', detail));
  if (retry) {
    const button = el('button', 'dashboard-text-button', 'Try again');
    button.type = 'button';
    button.addEventListener('click', load);
    card.append(button);
  }
  target.replaceChildren(card);
}

async function load() {
  target.setAttribute('aria-busy', 'true');
  message('Loading learners…', 'Getting the latest progress from the community.');
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (!user) return;
      setWorkspaceUser(user);
      sessionReady = true;
    }
    render(await getLeaderboard());
  } catch (error) {
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    message('Leaderboard is unavailable.', describeApiError(error), true);
  } finally {
    target.setAttribute('aria-busy', 'false');
  }
}

mountWorkspace('leaderboard');
load();
