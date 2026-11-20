import { listCourses } from './api.js';
import { listPlacements } from './placement-api.js';
import { el } from './layout.js';
import { t } from './i18n.js';
import { placementLevelFrom, recommendNextCourse } from './next-course.js';

/** Load catalog + placement level and compute the recommendation. Never throws. */
export async function loadNextCourse(progressCourses, afterSlug = null) {
  try {
    const [courses, attempts] = await Promise.all([
      listCourses(),
      listPlacements().catch(() => []), // Placement is optional context.
    ]);
    return recommendNextCourse({
      courses,
      progress: progressCourses,
      placementLevel: placementLevelFrom(attempts),
      afterSlug,
    });
  } catch {
    return { status: 'none', course: null, hasCompleted: false };
  }
}

/** Compact card: level, title, short description and a link. `null` when nothing to show. */
export function nextCourseCard(result, className) {
  if (result.status === 'next') {
    const { course } = result;
    const box = el('aside', className);
    box.setAttribute('aria-label', t('catalog.nextCourse'));
    const link = el('a', 'catalog-button dashboard-cta dashboard-cta-small', t('catalog.startNext'));
    link.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;
    const head = el('div', 'next-course-head');
    head.append(el('span', 'course-level catalog-badge', course.level), el('h3', undefined, course.title));
    box.append(
      el('p', 'dashboard-eyebrow', t('catalog.nextCourse')),
      head,
      el('p', 'catalog-description dashboard-muted', course.description),
      link,
    );
    return box;
  }
  if (result.status === 'complete') {
    const box = el('aside', className);
    box.append(el('h3', undefined, t('catalog.lineDoneTitle')), el('p', 'dashboard-muted', t('catalog.allDone')));
    return box;
  }
  return null;
}
