import { getCourse } from './api.js';
import { describeApiError } from './errors.js';
import { el, mountHeader, queryParam, renderMessage } from './layout.js';
import { requireSession } from './session.js';

function lessonItem(lesson) {
  const item = el('li');
  const link = el('a');
  link.href = `/lesson.html?slug=${encodeURIComponent(lesson.slug)}`;

  const left = el('div');
  left.append(
    el('div', 'lesson-title', lesson.title),
    el('div', 'lesson-summary', lesson.summary),
  );
  const meta = el('span', 'lesson-meta', `${lesson.estimatedMinutes} min`);

  link.append(left, meta);
  item.append(link);
  return item;
}

function renderCourse(container, course) {
  container.textContent = '';

  const breadcrumb = el('nav', 'breadcrumb');
  const back = el('a', undefined, 'Courses');
  back.href = '/courses.html';
  breadcrumb.append(back, el('span', undefined, '/'), el('span', undefined, course.title));

  const header = el('header');
  const row = el('div', 'row');
  row.append(el('h1', undefined, course.title), el('span', 'badge', course.level));
  header.append(row, el('p', 'muted', course.description));

  const section = el('section');
  section.append(el('h2', 'section-title', 'Lessons'));
  if (course.lessons.length === 0) {
    section.append(
      el('p', 'muted text-sm', 'No lessons have been published for this course yet.'),
    );
  } else {
    const list = el('ul', 'lesson-list');
    for (const lesson of course.lessons) list.append(lessonItem(lesson));
    section.append(list);
  }

  container.append(breadcrumb, header, section);
}

async function load() {
  const container = document.getElementById('course-body');
  const slug = queryParam('slug');
  if (!slug) {
    renderMessage(container, 'Course not specified', 'Pick a course from the catalog.');
    return;
  }
  renderMessage(container, undefined, 'Loading course…');
  try {
    const course = await getCourse(slug);
    renderCourse(container, course);
  } catch (error) {
    if (error.status === 404) {
      renderMessage(
        container,
        'Course not found',
        'This course does not exist or is not published yet.',
      );
    } else {
      renderMessage(container, 'Could not load this course', describeApiError(error), load);
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
