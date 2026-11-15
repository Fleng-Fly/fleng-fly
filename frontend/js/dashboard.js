import {
  getMyProgress,
  getMyStreak,
  getVocabularyStats,
} from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function button(label, action, className = 'dashboard-text-button') {
  const control = el('button', className, label);
  control.type = 'button';
  control.addEventListener('click', action);
  return control;
}

function message(target, title, detail, retry) {
  target.replaceChildren();
  const heading = el('strong', undefined, title);
  target.append(heading);
  if (detail) target.append(el('p', 'dashboard-muted', detail));
  if (retry) target.append(button('Try again', retry));
}

function setProfile(user) {
  const name = (user.displayName || 'Learner').trim();
  setWorkspaceUser(user);
  $('dashboard-level').textContent = `Level ${user.level} · ${user.xp} XP`;
  $('welcome-message').textContent =
    `Good to see you, ${name}. Make a little progress today and keep your momentum going.`;
}

function animateFill(node, property, value) {
  if (reducedMotion.matches) {
    node.style[property] = value;
  } else {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        node.style[property] = value;
      });
    });
  }
}

function metric(label, value, note) {
  const row = el('div', 'metric-row');
  const copy = el('div');
  copy.append(el('span', 'metric-label', label));
  if (note) copy.append(el('small', 'metric-note', note));
  row.append(copy, el('strong', 'metric-value', String(value)));
  return row;
}

function renderProgress(progressResult, streakResult, wordsResult) {
  const target = $('progress-body');
  target.replaceChildren();
  const progress = progressResult.status === 'fulfilled' ? progressResult.value : null;
  const courses = progress?.courses || [];
  const total = courses.reduce((sum, course) => sum + course.lessonsTotal, 0);
  const completed = courses.reduce((sum, course) => sum + course.lessonsCompleted, 0);
  const percent = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : null;

  const ring = el('div', 'progress-ring');
  if (percent !== null) {
    ring.setAttribute('role', 'progressbar');
    ring.setAttribute('aria-label', 'Published lessons completed');
    ring.setAttribute('aria-valuemin', '0');
    ring.setAttribute('aria-valuemax', '100');
    ring.setAttribute('aria-valuenow', String(percent));
  } else {
    ring.setAttribute('role', 'img');
    ring.setAttribute(
      'aria-label',
      progress ? 'No published lessons to measure' : 'Progress unavailable',
    );
  }
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 120 120');
  svg.setAttribute('aria-hidden', 'true');
  for (const name of ['ring-track', 'ring-fill']) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '60');
    circle.setAttribute('cy', '60');
    circle.setAttribute('r', '50');
    circle.setAttribute('class', name);
    svg.append(circle);
  }
  const center = el('div', 'ring-center');
  center.append(
    el('strong', undefined, percent === null ? '—' : `${percent}%`),
    el('span', undefined, 'completed'),
  );
  ring.append(svg, center);
  target.append(
    ring,
    el(
      'p',
      'ring-description',
      total
        ? `${completed} of ${total} published lessons completed`
        : progress
          ? 'No published lessons yet'
          : 'Progress unavailable',
    ),
  );
  if (percent !== null)
    animateFill(
      svg.querySelector('.ring-fill'),
      'strokeDashoffset',
      String(314.16 * (1 - percent / 100)),
    );

  const stats = el('div', 'metrics');
  stats.append(
    metric('Completed lessons', progress ? progress.lessonsCompleted : '—'),
    metric(
      'Words learned',
      wordsResult.status === 'fulfilled' ? wordsResult.value.wordsLearned : '—',
      wordsResult.status === 'rejected' ? 'Unavailable' : '',
    ),
    metric(
      'Current streak',
      streakResult.status === 'fulfilled' ? `${streakResult.value.current} days` : '—',
      streakResult.status === 'rejected' ? 'Unavailable' : '',
    ),
    metric(
      'Total study time',
      progress ? `${progress.studyMinutes} min` : '—',
      'Estimated lesson time',
    ),
    metric('XP earned', progress ? progress.xp : '—'),
  );
  target.append(stats);
  if (!progress) target.append(button('Retry progress', loadDashboardData));
  if (streakResult.status === 'rejected' || wordsResult.status === 'rejected') {
    target.append(el('p', 'dashboard-muted metric-error', 'Some metrics could not be loaded.'));
    target.append(button('Retry metrics', loadDashboardData));
  }
}

function chooseCurrentCourse(courses) {
  const started = courses.filter((course) => course.lessonsStarted > 0);
  // Prefer an unfinished course with the highest completion ratio; API order breaks ties.
  const unfinished = started.filter((course) => course.lessonsCompleted < course.lessonsTotal);
  const choices = unfinished.length ? unfinished : started;
  return choices.reduce((best, course) => {
    if (!best) return course;
    const ratio = course.lessonsTotal ? course.lessonsCompleted / course.lessonsTotal : 0;
    const bestRatio = best.lessonsTotal ? best.lessonsCompleted / best.lessonsTotal : 0;
    return ratio > bestRatio ? course : best;
  }, null);
}

function renderCurrentCourse(progressResult) {
  const target = $('current-course-body');
  target.replaceChildren();
  if (progressResult.status === 'rejected') {
    message(
      target,
      'Could not load your course.',
      describeApiError(progressResult.reason),
      loadDashboardData,
    );
    return;
  }
  const current = chooseCurrentCourse(progressResult.value.courses || []);
  if (!current) {
    message(target, 'No course started yet.', 'Choose a course and open a lesson to begin.');
    const link = el('a', 'dashboard-cta dashboard-cta-small', 'Browse courses');
    link.href = '/courses.html';
    target.append(link);
    return;
  }
  const percent = current.lessonsTotal
    ? Math.min(100, Math.round((current.lessonsCompleted / current.lessonsTotal) * 100))
    : 0;
  const head = el('div', 'current-course-top');
  const details = el('div');
  details.append(el('span', 'course-level', current.level), el('h3', undefined, current.title));
  head.append(details, el('strong', 'course-percent', `${percent}%`));
  const track = el('div', 'dashboard-progress-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', `${current.title} completed lessons`);
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.setAttribute('aria-valuenow', String(percent));
  const fill = el('div', 'dashboard-progress-fill');
  track.append(fill);
  const foot = el('div', 'current-course-foot');
  foot.append(
    el(
      'span',
      'dashboard-muted',
      `${current.lessonsCompleted} of ${current.lessonsTotal} lessons completed`,
    ),
  );
  const action = el(
    'a',
    'dashboard-cta dashboard-cta-small',
    percent === 100 ? 'Review course' : 'Continue course',
  );
  action.href = `/course.html?slug=${encodeURIComponent(current.slug)}`;
  foot.append(action);
  target.append(head, track, foot);
  animateFill(fill, 'width', `${percent}%`);
  for (const id of ['sidebar-course-link', 'quick-course-link']) $(id).href = action.href;
}

async function loadDashboardData() {
  const target = $('progress-body');
  message(target, 'Loading progress…');
  message($('current-course-body'), 'Loading course…');
  const [progress, streak, words] = await Promise.allSettled([
    getMyProgress(),
    getMyStreak(),
    getVocabularyStats(),
  ]);
  if (
    [progress, streak, words].some(
      (result) => result.status === 'rejected' && result.reason?.status === 401,
    )
  ) {
    window.location.replace('/login.html');
    return;
  }
  renderProgress(progress, streak, words);
  renderCurrentCourse(progress);
}

async function main() {
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    $('session-error').hidden = true;
    setProfile(user);
    $('dashboard-content').hidden = false;
    await loadDashboardData();
  } catch (error) {
    $('session-error-text').textContent = describeApiError(error);
    $('session-error').hidden = false;
  }
}

mountWorkspace('dashboard');
$('session-retry').addEventListener('click', main);
main();
