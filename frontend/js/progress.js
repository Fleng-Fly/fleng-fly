import { getMyAchievements, getMyProgress } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { getLang, t, tn } from './i18n.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const target = document.getElementById('progress-body');
const numberFormat = () => new Intl.NumberFormat(getLang(), { maximumFractionDigits: 2 });
const number = { format: (value) => numberFormat().format(value) };
let sessionReady = false;
let loading = false;
let generation = 0;

function validate(data) {
  const count = (value) => Number.isSafeInteger(value) && value >= 0;
  if (!data || !['lessonsStarted', 'lessonsCompleted', 'activeCourses', 'xp'].every((key) => count(data[key])) ||
      !data.streak || !count(data.streak.current) || !count(data.streak.longest) ||
      !data.xpHistory || !Array.isArray(data.courses) || !data.courses.every((course) =>
        typeof course.title === 'string' && typeof course.slug === 'string' &&
        count(course.lessonsTotal) && count(course.lessonsCompleted) &&
        Number.isFinite(course.completionPercent) && course.completionPercent >= 0 && course.completionPercent <= 100)) {
    throw new Error(t('progress.incomplete'));
  }
}

function metric(title, value, detail) {
  const card = el('article', 'dashboard-card progress-metric');
  card.append(el('h2', undefined, title), el('strong', 'progress-value', number.format(value)));
  if (detail) card.append(el('p', undefined, detail));
  return card;
}

function courseRow(course) {
  const item = el('li', 'progress-course');
  const heading = el('div', 'progress-course-heading');
  const link = el('a', undefined, course.title);
  link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
  heading.append(link, el('span', undefined, `${number.format(course.completionPercent)}%`));
  const bar = el('progress');
  bar.max = 100;
  bar.value = course.completionPercent;
  bar.setAttribute('aria-label', t('progress.courseComplete', { title: course.title, pct: number.format(course.completionPercent) }));
  item.append(heading, bar, el('p', undefined, course.lessonsTotal
    ? t('dashboard.lessonsOfTotal', { done: number.format(course.lessonsCompleted), total: number.format(course.lessonsTotal) })
    : t('progress.noLessons')));
  return item;
}

function renderAchievements(section, achievements) {
  const earned = achievements.filter((achievement) => achievement.awardedAt);
  if (!earned.length) {
    section.append(el('p', 'dashboard-muted', t('achievement.empty')));
    return;
  }
  const list = el('ul', 'progress-course-list');
  for (const achievement of earned) {
    const key = `achievement.${achievement.code}`;
    const title = t(key);
    list.append(el('li', 'progress-course', title === key ? achievement.title : title));
  }
  section.append(list);
}

function render(data) {
  validate(data);
  const metrics = el('section', 'progress-metrics');
  metrics.setAttribute('aria-label', t('progress.stats'));
  metrics.append(
    metric(t('dashboard.mLessons'), data.lessonsCompleted, t('progress.lessonsNote')),
    metric(t('progress.active'), data.activeCourses, t('progress.activeNote')),
    metric(t('progress.totalXp'), data.xp, t('progress.xpNote')),
    metric(t('dashboard.mStreak'), data.streak.current, t('progress.streakNote', { days: tn('dashboard.days', data.streak.current), best: tn('dashboard.days', data.streak.longest) })),
  );
  const history = el('p', 'progress-note', data.xpHistory.last7Days == null || data.xpHistory.last30Days == null
    ? t('progress.historyUnavailable')
    : t('progress.historyNote'));
  target.replaceChildren(metrics, history);
  if (data.lessonsStarted === 0 && data.xp === 0 && data.streak.longest === 0) {
    const empty = el('section', 'dashboard-card progress-message');
    empty.append(el('h2', undefined, t('progress.emptyTitle')),
      el('p', 'dashboard-muted', t('progress.emptyText')));
    const link = el('a', 'dashboard-text-button', t('dashboard.browse'));
    link.href = '/courses.html';
    empty.append(link);
    target.append(empty);
  }
  const courses = el('section', 'dashboard-card progress-courses');
  courses.append(el('h2', undefined, t('progress.courses')),
    el('p', 'progress-note', t('progress.coursesNote')));
  if (data.courses.length) {
    const list = el('ul', 'progress-course-list');
    list.append(...data.courses.map(courseRow));
    courses.append(list);
  } else courses.append(el('p', 'dashboard-muted', t('progress.noCourses')));
  target.append(courses);
  const achievements = el('section', 'dashboard-card progress-courses');
  achievements.append(el('h2', undefined, t('achievement.title')));
  const status = el('div');
  status.append(el('p', 'dashboard-muted', t('common.loading')));
  achievements.append(status);
  target.append(achievements);
  void getMyAchievements().then((items) => {
    status.replaceChildren();
    renderAchievements(status, items);
  }).catch(() => {
    status.replaceChildren(el('p', 'dashboard-muted', t('achievement.unavailable')));
  });
}

function message(title, detail, retry = false) {
  const card = el('div', 'dashboard-card progress-message');
  card.setAttribute('role', retry ? 'alert' : 'status');
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
  if (loading) return;
  loading = true;
  const request = ++generation;
  target.setAttribute('aria-busy', 'true');
  message(t('progress.loading'), t('progress.loadingText'));
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (request !== generation || !user) return;
      setWorkspaceUser(user);
      sessionReady = true;
    }
    const data = await getMyProgress();
    if (request === generation) render(data);
  } catch (error) {
    if (request !== generation) return;
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    message(t('progress.unavailable'), describeApiError(error), true);
  } finally {
    if (request === generation) {
      loading = false;
      target.setAttribute('aria-busy', 'false');
    }
  }
}

mountWorkspace('progress');
function clear() {
  generation++;
  loading = false;
  sessionReady = false;
  target.setAttribute('aria-busy', 'false');
  message(t('progress.private'), t('progress.privateText'));
}
window.addEventListener('fleng:session-ended', () => {
  clear();
  window.location.replace('/login.html');
});
window.addEventListener('pagehide', clear);
window.addEventListener('pageshow', (event) => { if (event.persisted) load(); });
load();
