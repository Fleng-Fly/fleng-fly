import { getMyProgress, listCourses } from './api.js';
import { catalogMessage, courseProgress } from './catalog-ui.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const container = document.getElementById('courses-body');
const search = document.getElementById('course-search');
const clear = document.getElementById('course-search-clear');
const filters = document.getElementById('course-filters');
const count = document.getElementById('course-results-count');
let courses = [];
let progress;
let level = 'All';
let sessionReady = false;
let loading = false;
let loaded = false;

function courseCard(course) {
  const current = progress.courses.find((item) => item.courseId === course.id);
  // Missing progress must not masquerade as an unstarted course.
  if (!current) throw new Error('Course progress is unavailable. Please try again.');
  const completed = current.lessonsTotal > 0 && current.lessonsCompleted >= current.lessonsTotal;
  const card = el('article', `catalog-panel catalog-card${completed ? ' is-complete' : ''}`);
  const meta = el('div', 'catalog-card-meta');
  meta.append(el('span', 'catalog-badge', course.level));
  if (completed) meta.append(el('span', 'catalog-status is-complete', '✓ Completed'));
  card.append(
    meta,
    el('h2', undefined, course.title),
    el('p', 'catalog-description', course.description),
  );
  card.append(
    el(
      'p',
      'catalog-lesson-count',
      `${course.lessonCount} ${course.lessonCount === 1 ? 'lesson' : 'lessons'}`,
    ),
  );
  if (current.lessonsStarted > 0) card.append(courseProgress(current));
  const link = el(
    'a',
    'catalog-button',
    completed ? 'Review Course' : current.lessonsStarted > 0 ? 'Continue Course' : 'Start Course',
  );
  link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
  link.setAttribute('aria-label', `${link.textContent}: ${course.title}`);
  card.append(link);
  return card;
}

function render() {
  clear.hidden = !search.value;
  if (!loaded) return;
  const query = search.value.trim().toLocaleLowerCase();
  const matches = courses.filter(
    (course) =>
      (level === 'All' || course.level === level) &&
      `${course.title} ${course.description}`.toLocaleLowerCase().includes(query),
  );
  count.textContent = `${matches.length} ${matches.length === 1 ? 'course' : 'courses'}`;
  if (!courses.length) {
    catalogMessage(container, 'No courses yet', 'Published courses will appear here.');
  } else if (!matches.length) {
    catalogMessage(
      container,
      'No courses found',
      'Try another search or CEFR level.',
      () => {
        search.value = '';
        selectLevel('All');
        search.focus();
      },
      'Reset filters',
    );
  } else {
    const grid = el('div', 'catalog-grid');
    grid.append(...matches.map(courseCard));
    container.replaceChildren(grid);
  }
}

function selectLevel(value) {
  level = value;
  for (const button of filters.querySelectorAll('button')) {
    button.setAttribute('aria-pressed', String(button.dataset.level === level));
  }
  render();
}

async function load() {
  if (loading) return;
  loading = true;
  loaded = false;
  count.textContent = '';
  container.setAttribute('aria-busy', 'true');
  catalogMessage(container, 'Loading courses…', 'Getting your latest learning progress.');
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (!user) return;
      setWorkspaceUser(user);
      sessionReady = true;
    }
    [courses, progress] = await Promise.all([listCourses(), getMyProgress()]);
    // Validate before enabling filters, including courses outside the current filter.
    if (courses.some((course) => !progress.courses.some((item) => item.courseId === course.id))) {
      throw new Error('The catalog has changed. Please try again to load its progress.');
    }
    loaded = true;
    render();
  } catch (error) {
    loaded = false;
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    catalogMessage(container, 'Could not load courses', describeApiError(error), load);
  } finally {
    loading = false;
    container.setAttribute('aria-busy', 'false');
  }
}

mountWorkspace('courses');
search.addEventListener('input', render);
clear.addEventListener('click', () => {
  search.value = '';
  render();
  search.focus();
});
filters.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-level]');
  if (button) selectLevel(button.dataset.level);
});
// Refresh after lesson navigation, including restoration from the browser back/forward cache.
window.addEventListener('pageshow', (event) => {
  if (event.persisted) load();
});
window.addEventListener('focus', () => {
  if (sessionReady) load();
});
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && sessionReady) load();
});
load();
