import { getCourse, getLessonProgress, getMyProgress } from './api.js';
import { catalogMessage, courseProgress } from './catalog-ui.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const container = document.getElementById('course-body');
let sessionReady = false;
let loading = false;

function lessonItem(lesson, progress, index) {
  const complete = progress.completed;
  const started = Boolean(progress.startedAt);
  const item = el('li', `catalog-panel catalog-lesson${complete ? ' is-complete' : ''}`);
  const number = el('span', 'catalog-lesson-number', String(index + 1).padStart(2, '0'));
  number.setAttribute('aria-label', `Lesson ${index + 1}`);
  const copy = el('div', 'catalog-lesson-copy');
  copy.append(el('h3', undefined, lesson.title), el('p', 'catalog-description', lesson.summary));
  const meta = el('div', 'catalog-lesson-meta');
  meta.append(
    el('span', undefined, `${lesson.estimatedMinutes} min`),
    el(
      'span',
      `catalog-status${complete ? ' is-complete' : started ? ' is-started' : ''}`,
      complete ? 'Completed' : started ? 'In Progress' : 'Not Started',
    ),
  );
  copy.append(meta);
  const link = el(
    'a',
    `catalog-button${started && !complete ? '' : ' is-secondary'}`,
    complete ? 'Review Lesson' : started ? 'Continue Lesson' : 'Start Lesson',
  );
  link.href = `/lesson.html?slug=${encodeURIComponent(lesson.slug)}`;
  link.setAttribute('aria-label', `${link.textContent}: ${lesson.title}`);
  item.append(number, copy, link);
  return item;
}

function renderCourse(course, current, lessonsProgress) {
  const breadcrumb = el('nav', 'breadcrumb catalog-breadcrumb');
  breadcrumb.setAttribute('aria-label', 'Breadcrumb');
  const back = el('a', undefined, 'Courses');
  back.href = '/courses.html';
  const title = el('span', undefined, course.title);
  title.setAttribute('aria-current', 'page');
  const separator = el('span', undefined, '/');
  separator.setAttribute('aria-hidden', 'true');
  breadcrumb.append(back, separator, title);
  const hero = el('header', 'catalog-panel catalog-hero');
  hero.append(
    el('span', 'catalog-badge', course.level),
    el('h1', undefined, course.title),
    el('p', 'catalog-description', course.description),
    courseProgress(current),
  );
  const section = el('section', 'catalog-lessons');
  section.append(el('h2', undefined, 'Lessons'));
  if (!course.lessons.length) {
    const empty = el('div');
    catalogMessage(empty, 'No lessons yet', 'No lessons have been published for this course yet.');
    section.append(empty);
  } else {
    const list = el('ol', 'catalog-lesson-list');
    list.append(
      ...course.lessons.map((lesson, index) => lessonItem(lesson, lessonsProgress[index], index)),
    );
    section.append(list);
  }
  container.replaceChildren(breadcrumb, hero, section);
  document.title = `${course.title} — Fleng`;
}

async function load() {
  if (loading) return;
  loading = true;
  container.setAttribute('aria-busy', 'true');
  catalogMessage(container, 'Loading course…', 'Getting your latest learning progress.');
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (!user) return;
      setWorkspaceUser(user);
      sessionReady = true;
    }
    const slug = queryParam('slug');
    if (!slug) {
      catalogMessage(container, 'Course not specified', 'Pick a course from the catalog.');
      return;
    }
    const [course, progress] = await Promise.all([getCourse(slug), getMyProgress()]);
    const current = progress.courses.find((item) => item.courseId === course.id);
    if (!current) throw new Error('Course progress is unavailable. Please try again.');
    const lessonsProgress = await Promise.all(
      course.lessons.map((lesson) => getLessonProgress(lesson.slug)),
    );
    renderCourse(course, current, lessonsProgress);
  } catch (error) {
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    if (error.status === 404) {
      catalogMessage(
        container,
        'Course not found',
        'This course or one of its lessons is no longer available.',
        load,
      );
    } else {
      catalogMessage(container, 'Could not load this course', describeApiError(error), load);
    }
  } finally {
    loading = false;
    container.setAttribute('aria-busy', 'false');
  }
}

mountWorkspace('courses');
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
