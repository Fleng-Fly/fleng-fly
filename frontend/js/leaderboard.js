import { getLeaderboard } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const target = document.getElementById('leaderboard-body');
const number = new Intl.NumberFormat('en');
const SVG_NS = 'http://www.w3.org/2000/svg';
const MEDAL_CLASSES = { 1: 'is-first', 2: 'is-second', 3: 'is-third' };
let sessionReady = false;

function svgPath(d, className) {
  const path = document.createElementNS(SVG_NS, 'path');
  path.setAttribute('d', d);
  if (className) path.setAttribute('class', className);
  return path;
}

/** Decorative wings behind the first place avatar (purely visual). */
function wingsSvg() {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 160 64');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  svg.setAttribute('class', 'leaderboard-wings');
  svg.append(
    svgPath(
      'M76 14C60 16 44 25 30 37 22 44 15 51 10 56c13 0 26-5 37-12 14-9 24-18 29-30Z',
      'leaderboard-wing',
    ),
    svgPath(
      'M84 14c16 2 32 11 46 23 8 7 15 14 20 19-13 0-26-5-37-12-14-9-24-18-29-30Z',
      'leaderboard-wing',
    ),
    svgPath('M72 20C60 24 48 31 39 40', 'leaderboard-wing-line'),
    svgPath('M68 26C56 30 44 38 34 47', 'leaderboard-wing-line'),
    svgPath('M88 20c12 4 24 11 33 20', 'leaderboard-wing-line'),
    svgPath('M92 26c12 4 24 12 34 21', 'leaderboard-wing-line'),
  );
  return svg;
}

function crownSvg() {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  svg.append(svgPath('M3 17.5h18l1-9.5-5.5 3.6L12 4.5 7.5 11.6 2 8l1 9.5Z'));
  return svg;
}

function streakChip(days) {
  const chip = el('span', 'leaderboard-streak');
  chip.append(
    el('span', 'leaderboard-streak-dot'),
    el('span', undefined, days === 1 ? '1 day' : `${number.format(days)} days`),
  );
  return chip;
}

function medalBadge(rank) {
  const modifier = MEDAL_CLASSES[rank];
  return el(
    'span',
    modifier ? `leaderboard-medal ${modifier}` : 'leaderboard-medal',
    `#${rank}`,
  );
}

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
  if (entry.rank === 1) {
    const crown = el('span', 'leaderboard-crown');
    crown.append(crownSvg());
    card.append(crown, wingsSvg());
  }
  card.append(
    el('span', 'podium-place', ['✦ FIRST PLACE', 'SECOND PLACE', 'THIRD PLACE'][entry.rank - 1]),
  );
  card.append(avatar(entry), learner(entry));
  card.append(el('strong', 'podium-xp', `${number.format(entry.xp)} XP`));
  const facts = el('p', 'dashboard-muted podium-facts');
  facts.append(
    el('span', undefined, `${number.format(entry.lessonsCompleted)} lessons ·`),
    streakChip(entry.streak),
  );
  card.append(facts);
  card.append(el('span', 'podium-rank', `#${entry.rank}`));
  return card;
}

function row(entry) {
  const tr = el('tr', entry.isCurrentUser ? 'current-learner' : '');
  const rank = el('td', 'rank-cell');
  rank.append(medalBadge(entry.rank));
  tr.append(rank);
  const name = el('td');
  const identity = el('div', 'learner-identity');
  identity.append(avatar(entry), learner(entry));
  name.append(identity);
  const streak = el('td', 'streak-cell');
  streak.append(streakChip(entry.streak));
  tr.append(
    name,
    el('td', 'xp-cell', number.format(entry.xp)),
    el('td', undefined, number.format(entry.lessonsCompleted)),
    streak,
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
