import { getMyProgress, listCourses } from './api.js';
import { t, tn } from './i18n.js';
import { getPlacement, listPlacements } from './placement-api.js';
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
let recommended = null; // { slugs: Set, label } from the learner's latest completed placement test
let progress;
let level = 'All';
let sessionReady = false;
let loading = false;
let loaded = false;

/** Course suggestions come only from the learner's own completed placement attempt. */
async function loadRecommendation() {
  recommended = null;
  try {
    const attempts = await listPlacements();
    const done = attempts.find((attempt) => attempt.status === 'completed');
    if (!done) return;
    const detail = await getPlacement(done.id);
    const slugs = new Set((detail.recommendedCourses || []).map((course) => course.slug));
    if (slugs.size) recommended = { slugs, label: detail.result?.label || '' };
  } catch { /* Recommendations are optional; the catalog works without them. */ }
}

function recommendationNote() {
  const note = el('p', 'catalog-recommendation');
  note.append(el('strong', undefined, t('catalog.recommendedTitle')), ' ', t('catalog.recommendedText'), ' ');
  const link = el('a', undefined, t('catalog.viewResult'));
  link.href = '/placement-test.html';
  note.append(link);
  return note;
}

function courseCard(course) {
  const current = progress.courses.find((item) => item.courseId === course.id);
  // Missing progress must not masquerade as an unstarted course.
  if (!current) throw new Error(t('catalog.progressMissing'));
  const completed = current.lessonsTotal > 0 && current.lessonsCompleted >= current.lessonsTotal;
  const card = el('article', `catalog-panel catalog-card${completed ? ' is-complete' : ''}`);
  const meta = el('div', 'catalog-card-meta');
  meta.append(el('span', 'catalog-badge', course.level));
  meta.append(el('span', 'catalog-level-name', t(`catalog.level.${course.level}`)));
  if (completed) meta.append(el('span', 'catalog-status is-complete', `✓ ${t('catalog.completed')}`));
  else if (recommended?.slugs.has(course.slug)) meta.append(el('span', 'catalog-status is-recommended', t('catalog.recommended')));
  card.append(
    meta,
    el('h2', undefined, course.title),
    el('p', 'catalog-description', course.description),
  );
  card.append(
    el('p', 'catalog-lesson-count', tn('catalog.lessonCount', course.lessonCount)),
  );
  if (current.lessonsStarted > 0) card.append(courseProgress(current));
  const link = el(
    'a',
    'catalog-button',
    completed ? t('catalog.reviewCourse') : current.lessonsStarted > 0 ? t('catalog.continueCourse') : t('catalog.startCourse'),
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
  count.textContent = tn('catalog.courseCount', matches.length);
  if (!courses.length) {
    catalogMessage(container, t('catalog.noCourses'), t('catalog.noCoursesText'));
  } else if (!matches.length) {
    catalogMessage(
      container,
      t('catalog.noMatches'),
      t('catalog.noMatchesText'),
      () => {
        search.value = '';
        selectLevel('All');
        search.focus();
      },
      t('catalog.resetFilters'),
    );
  } else {
    const grid = el('div', 'catalog-grid');
    grid.append(...matches.map(courseCard));
    container.replaceChildren(...(recommended ? [recommendationNote()] : []), grid);
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
  catalogMessage(container, t('catalog.loadingCourses'), t('catalog.loadingProgress'));
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
      throw new Error(t('catalog.changed'));
    }
    await loadRecommendation();
    loaded = true;
    render();
  } catch (error) {
    loaded = false;
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    catalogMessage(container, t('catalog.loadCoursesFailed'), describeApiError(error), load);
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
