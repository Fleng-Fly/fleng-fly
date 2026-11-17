import { getLeaderboard } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { getLang, t, tn } from './i18n.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const target = document.getElementById('leaderboard-body');
let number = new Intl.NumberFormat(getLang());
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
  if (entry.isCurrentUser) copy.append(el('small', 'learner-you', t('lb.you')));
  return copy;
}

function podium(entry) {
  const card = el(
    'article',
    `podium-card podium-${entry.rank}${entry.isCurrentUser ? ' is-you' : ''}`,
  );
  card.append(
    el('span', 'podium-place', `${entry.rank === 1 ? '✦ ' : ''}${t(`lb.place${entry.rank}`)}`),
  );
  card.append(avatar(entry), learner(entry));
  card.append(el('strong', 'podium-xp', `${number.format(entry.xp)} XP`));
  card.append(
    el(
      'p',
      'dashboard-muted',
      t('lb.stats', { lessons: tn('lb.lessons', entry.lessonsCompleted, { n: number.format(entry.lessonsCompleted) }), streak: tn('dashboard.days', entry.streak) }),
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
    el('td', undefined, tn('dashboard.days', entry.streak)),
  );
  return tr;
}

function render(data) {
  number = new Intl.NumberFormat(getLang());
  target.replaceChildren();
  if (!data.entries.length) {
    message(t('lb.emptyTitle'), t('lb.emptyText'));
    return;
  }
  const top = el('section', 'leaderboard-podium');
  top.setAttribute('aria-label', t('lb.topThree'));
  top.append(...data.entries.slice(0, 3).map(podium));
  const panel = el('section', 'dashboard-card leaderboard-panel');
  const heading = el('div', 'section-heading');
  heading.append(
    el('h2', undefined, t('lb.title')),
    el('span', 'dashboard-muted', tn('lb.learners', data.total, { n: number.format(data.total) })),
  );
  const scroll = el('div', 'leaderboard-scroll');
  scroll.tabIndex = 0;
  scroll.setAttribute('role', 'region');
  scroll.setAttribute('aria-label', t('lb.scrollLabel'));
  const table = el('table', 'leaderboard-table');
  const caption = el(
    'caption',
    'sr-only',
    t('lb.caption'),
  );
  const head = el('thead');
  const headers = el('tr');
  for (const label of [t('lb.rank'), t('lb.learner'), 'XP', t('lb.colLessons'), t('lb.streak')]) {
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
        t('lb.yourPosition', { rank: data.currentUser.rank, xp: number.format(data.currentUser.xp), lessons: tn('lb.lessons', data.currentUser.lessonsCompleted, { n: data.currentUser.lessonsCompleted }), streak: tn('dashboard.days', data.currentUser.streak) }),
      ),
    );
  }
  panel.append(
    el(
      'p',
      'leaderboard-note dashboard-muted',
      t('lb.note') +
        (data.total > data.entries.length ? ` ${t('lb.showingTop', { n: data.entries.length })}` : ''),
    ),
  );
  target.append(top, panel);
}

function message(title, detail, retry) {
  const card = el('div', 'dashboard-card leaderboard-message');
  card.append(el('h2', undefined, title), el('p', 'dashboard-muted', detail));
  if (retry) {
    const button = el('button', 'dashboard-text-button', t('common.tryAgain'));
    button.type = 'button';
    button.addEventListener('click', load);
    card.append(button);
  }
  target.replaceChildren(card);
}

async function load() {
  target.setAttribute('aria-busy', 'true');
  message(t('lb.loading'), t('lb.loadingText'));
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
    message(t('lb.unavailable'), describeApiError(error), true);
  } finally {
    target.setAttribute('aria-busy', 'false');
  }
}

mountWorkspace('leaderboard');
load();
