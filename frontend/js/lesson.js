import { getLesson } from './api.js';
import { describeApiError } from './errors.js';
import { el, mountHeader, queryParam, renderMessage } from './layout.js';
import { requireSession } from './session.js';

/**
 * Render lesson `theory` with a tiny, safe markup:
 * blocks separated by blank lines; `## ` starts a heading; lines starting with
 * `- ` form a list; anything else is a paragraph. All text goes through
 * `textContent`, never `innerHTML`.
 */
function renderTheory(container, theory) {
  container.textContent = '';
  for (const raw of theory.split(/\n\s*\n/)) {
    const block = raw.trim();
    if (!block) continue;
    const lines = block
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

    if (lines.every((line) => line.startsWith('- '))) {
      const list = el('ul');
      for (const line of lines) list.append(el('li', undefined, line.slice(2)));
      container.append(list);
    } else if (block.startsWith('## ')) {
      container.append(el('h3', undefined, block.slice(3)));
    } else {
      container.append(el('p', undefined, lines.join(' ')));
    }
  }
}

function renderLesson(container, lesson) {
  container.textContent = '';
  const courseHref = `/course.html?slug=${encodeURIComponent(lesson.courseSlug)}`;

  const breadcrumb = el('nav', 'breadcrumb');
  const coursesLink = el('a', undefined, 'Courses');
  coursesLink.href = '/courses.html';
  const courseLink = el('a', undefined, lesson.courseTitle);
  courseLink.href = courseHref;
  breadcrumb.append(
    coursesLink,
    el('span', undefined, '/'),
    courseLink,
    el('span', undefined, '/'),
    el('span', undefined, lesson.title),
  );

  const header = el('header');
  const row = el('div', 'row');
  row.append(el('h1', undefined, lesson.title), el('span', 'badge', lesson.level));
  header.append(row, el('p', 'muted', lesson.summary));

  const prose = el('article', 'card prose');
  renderTheory(prose, lesson.theory);

  const actions = el('div', 'actions');
  const back = el('a', 'btn btn-ghost', 'Back to course');
  back.href = courseHref;
  actions.append(back);

  container.append(
    breadcrumb,
    header,
    el('p', 'muted text-sm', `About ${lesson.estimatedMinutes} minutes`),
    prose,
    actions,
  );
}

async function load() {
  const container = document.getElementById('lesson-body');
  const slug = queryParam('slug');
  if (!slug) {
    renderMessage(container, 'Lesson not specified', 'Pick a lesson from a course.');
    return;
  }
  renderMessage(container, undefined, 'Loading lesson…');
  try {
    const lesson = await getLesson(slug);
    renderLesson(container, lesson);
  } catch (error) {
    if (error.status === 404) {
      renderMessage(
        container,
        'Lesson not found',
        'This lesson does not exist or is not published yet.',
      );
    } else {
      renderMessage(container, 'Could not load this lesson', describeApiError(error), load);
    }
  }
}

async function main() {
  const user = await requireSession();
  if (!user) return;
  await mountHeader('courses', user);
  load();
}

main();
