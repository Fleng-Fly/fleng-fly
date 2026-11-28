import { getCourse, getLessonProgress, getMyProgress } from './api.js';
import { t } from './i18n.js';
import { catalogMessage, courseProgress } from './catalog-ui.js';
import { describeApiError } from './errors.js';
import { el, queryParam } from './layout.js';
import { loadNextCourse, nextCourseCard } from './next-course-ui.js';
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
  number.setAttribute('aria-label', t('catalog.lessonN', { n: index + 1 }));
  const copy = el('div', 'catalog-lesson-copy');
  copy.append(el('h3', undefined, lesson.title), el('p', 'catalog-description', lesson.summary));
  const meta = el('div', 'catalog-lesson-meta');
  meta.append(
    el('span', undefined, t('catalog.minutes', { n: lesson.estimatedMinutes })),
    el(
      'span',
      `catalog-status${complete ? ' is-complete' : started ? ' is-started' : ''}`,
      complete ? t('catalog.completed') : started ? t('catalog.inProgress') : t('catalog.notStarted'),
    ),
  );
  if (complete || progress.testFinishedAt) {
    const results = el('a', 'catalog-result-link', t('completion.viewResults'));
    results.href = `/lesson.html?slug=${encodeURIComponent(lesson.slug)}&view=results`;
    results.setAttribute('aria-label', `${results.textContent}: ${lesson.title}`);
    meta.append(results);
  }
  copy.append(meta);
  const link = el(
    'a',
    `catalog-button${started && !complete ? '' : ' is-secondary'}`,
    complete ? t('catalog.reviewLesson') : started ? t('catalog.continueLesson') : t('catalog.startLesson'),
  );
  link.href = `/lesson.html?slug=${encodeURIComponent(lesson.slug)}`;
  link.setAttribute('aria-label', `${link.textContent}: ${lesson.title}`);
  item.append(number, copy, link);
  return item;
}

function nextCourseBanner(result) {
  const box = nextCourseCard(result, 'catalog-panel catalog-next');
  if (!box) {
    // A finished side/demo course still earns the congratulation, just without a suggestion.
    const plain = el('aside', 'catalog-panel catalog-next');
    plain.append(el('h2', undefined, t('catalog.courseDone')));
    return plain;
  }
  if (result.status === 'next') box.prepend(el('h2', undefined, t('catalog.courseDone')));
  return box;
}

function renderCourse(course, current, lessonsProgress, recommendation) {
  const breadcrumb = el('nav', 'breadcrumb catalog-breadcrumb');
  breadcrumb.setAttribute('aria-label', t('catalog.breadcrumb'));
  const back = el('a', undefined, t('nav.courses'));
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
  if (/^fleng-vocabulary-(a[012]|b[12])$/.test(course.slug)) {
    const test = el('a', 'catalog-button', t('vocab.levelTest', { level: course.level }));
    test.href = `/vocabulary.html?${new URLSearchParams({ mode: 'mixed', level: course.level })}`;
    hero.append(test);
  }
  const section = el('section', 'catalog-lessons');
  section.append(el('h2', undefined, t('catalog.lessons')));
  if (!course.lessons.length) {
    const empty = el('div');
    catalogMessage(empty, t('catalog.noLessons'), t('catalog.noLessonsText'));
    section.append(empty);
  } else {
    const list = el('ol', 'catalog-lesson-list');
    list.append(
      ...course.lessons.map((lesson, index) => lessonItem(lesson, lessonsProgress[index], index)),
    );
    section.append(list);
  }
  container.replaceChildren(breadcrumb, hero, ...(recommendation ? [recommendation] : []), section);
  document.title = `${course.title} — Fleng`;
}

async function load() {
  if (loading) return;
  loading = true;
  container.setAttribute('aria-busy', 'true');
  catalogMessage(container, t('catalog.loadingCourse'), t('catalog.loadingProgress'));
  try {
    if (!sessionReady) {
      const user = await requireSession({ throwOnUnavailable: true });
      if (!user) return;
      setWorkspaceUser(user);
      sessionReady = true;
    }
    const slug = queryParam('slug');
    if (!slug) {
      catalogMessage(container, t('catalog.noSlug'), t('catalog.noSlugText'));
      return;
    }
    const [course, progress] = await Promise.all([getCourse(slug), getMyProgress()]);
    const current = progress.courses.find((item) => item.courseId === course.id);
    if (!current) throw new Error(t('catalog.progressMissing'));
    const lessonsProgress = await Promise.all(
      course.lessons.map((lesson) => getLessonProgress(lesson.slug)),
    );
    const finished = current.lessonsTotal > 0 && current.lessonsCompleted >= current.lessonsTotal;
    const recommendation = finished
      ? nextCourseBanner(await loadNextCourse(progress.courses, course.slug))
      : null;
    renderCourse(course, current, lessonsProgress, recommendation);
  } catch (error) {
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    if (error.status === 404) {
      catalogMessage(
        container,
        t('catalog.notFound'),
        t('catalog.notFoundText'),
        load,
      );
    } else {
      catalogMessage(container, t('catalog.loadFailed'), describeApiError(error), load);
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
