import { listCourses } from './api.js';
import { describeApiError } from './errors.js';
import { el, mountHeader, renderMessage } from './layout.js';
import { requireSession } from './session.js';

function courseCard(course) {
  const card = el('a', 'card course-card');
  card.href = `/course.html?slug=${encodeURIComponent(course.slug)}`;

  const head = el('div', 'row');
  head.append(el('h2', 'course-title', course.title), el('span', 'badge', course.level));

  const count = course.lessonCount === 1 ? '1 lesson' : `${course.lessonCount} lessons`;
  card.append(head, el('p', 'muted text-sm', course.description), el('span', 'muted text-sm', count));
  return card;
}

async function load() {
  const container = document.getElementById('courses-body');
  renderMessage(container, undefined, 'Loading courses…');
  try {
    const courses = await listCourses();
    container.textContent = '';
    if (courses.length === 0) {
      renderMessage(container, 'No courses yet', 'Published courses will appear here.');
      return;
    }
    const grid = el('div', 'course-grid');
    for (const course of courses) grid.append(courseCard(course));
    container.append(grid);
  } catch (error) {
    renderMessage(container, 'Could not load courses', describeApiError(error), load);
  }
}

async function main() {
  const user = await requireSession();
  if (!user) return;
  await mountHeader('courses', user);
  load();
}

main();
