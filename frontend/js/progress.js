import { getMyProgress } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const target = document.getElementById('progress-body');
const number = new Intl.NumberFormat('en', { maximumFractionDigits: 2 });
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
    throw new Error('Progress data is incomplete. Please try again.');
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
  bar.setAttribute('aria-label', `${course.title}: ${number.format(course.completionPercent)}% complete`);
  item.append(heading, bar, el('p', undefined, course.lessonsTotal
    ? `${number.format(course.lessonsCompleted)} of ${number.format(course.lessonsTotal)} lessons completed`
    : 'No published lessons yet.'));
  return item;
}

function render(data) {
  validate(data);
  const metrics = el('section', 'progress-metrics');
  metrics.setAttribute('aria-label', 'Your learning statistics');
  metrics.append(
    metric('Completed lessons', data.lessonsCompleted, 'Across your learning history'),
    metric('Active courses', data.activeCourses, 'Started, with lessons left to finish'),
    metric('Total XP', data.xp, 'Earned through learning'),
    metric('Current streak', data.streak.current, `${data.streak.current === 1 ? 'day' : 'days'} · Best streak: ${number.format(data.streak.longest)} ${data.streak.longest === 1 ? 'day' : 'days'}`),
  );
  const history = el('p', 'progress-note', data.xpHistory.last7Days == null || data.xpHistory.last30Days == null
    ? 'Daily XP history for the last 7 and 30 days is unavailable. Your total XP is shown above.'
    : 'Your total XP is shown above. Daily XP charts are not available on this page.');
  target.replaceChildren(metrics, history);
  if (data.lessonsStarted === 0 && data.xp === 0 && data.streak.longest === 0) {
    const empty = el('section', 'dashboard-card progress-message');
    empty.append(el('h2', undefined, 'Your progress starts here'),
      el('p', 'dashboard-muted', 'Start a lesson to build your progress. Completed lessons and earned XP will appear here.'));
    const link = el('a', 'dashboard-text-button', 'Explore lessons');
    link.href = '/courses.html';
    empty.append(link);
    target.append(empty);
  }
  const courses = el('section', 'dashboard-card progress-courses');
  courses.append(el('h2', undefined, 'Course progress'),
    el('p', 'progress-note', 'Completion is based on the lessons currently available in each course.'));
  if (data.courses.length) {
    const list = el('ul', 'progress-course-list');
    list.append(...data.courses.map(courseRow));
    courses.append(list);
  } else courses.append(el('p', 'dashboard-muted', 'No published courses are available yet. Your learning totals are saved.'));
  target.append(courses);
}

function message(title, detail, retry = false) {
  const card = el('div', 'dashboard-card progress-message');
  card.setAttribute('role', retry ? 'alert' : 'status');
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
  if (loading) return;
  loading = true;
  const request = ++generation;
  target.setAttribute('aria-busy', 'true');
  message('Loading your progress…', 'Getting your saved learning statistics.');
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
    message('Progress is unavailable', describeApiError(error), true);
  } finally {
    if (request === generation) {
      loading = false;
      target.setAttribute('aria-busy', 'false');
    }
  }
}

mountWorkspace('progress');
// Add navigation only on this page; shared workspace and other pages are unchanged.
const nav = document.querySelector('.sidebar-nav');
if (nav) {
  const link = el('a', 'sidebar-link active', 'Progress');
  link.href = '/progress.html';
  link.setAttribute('aria-current', 'page');
  nav.append(link);
}
function clear() {
  generation++;
  loading = false;
  sessionReady = false;
  target.setAttribute('aria-busy', 'false');
  message('Your progress is private', 'Sign in to view your learning statistics.');
}
window.addEventListener('fleng:session-ended', () => {
  clear();
  window.location.replace('/login.html');
});
window.addEventListener('pagehide', clear);
window.addEventListener('pageshow', (event) => { if (event.persisted) load(); });
load();
