import { el } from './layout.js';
import { getPlacement, listPlacements } from './placement-api.js';
import { describeApiError } from './errors.js';

function link(label, href, primary = false) {
  const node = el('a', `btn ${primary ? 'btn-primary' : 'btn-secondary'}`, label);
  node.href = href;
  return node;
}

// Only a dismissal preference is stored locally, scoped to the signed-in learner.
// Scores and course suggestions always come from the owned Placement API.
export async function mountPlacementGuidance(target, user) {
  const key = `fleng.placement-intro.v1.${user.id}`;
  let skipped = false;
  try { skipped = localStorage.getItem(key) === 'skipped'; } catch { /* Storage may be disabled. */ }
  target.replaceChildren(el('p', 'muted', 'Finding your next step…'));
  try {
    const recent = await listPlacements();
    const completed = recent.find(attempt => attempt.status === 'completed');
    const active = recent.find(attempt => attempt.status === 'in_progress');
    target.replaceChildren();
    if (completed) {
      const attempt = await getPlacement(completed.id);
      target.append(el('h2', undefined, 'Your suggested starting point'), el('p', undefined, attempt.result.label));
      const course = attempt.recommendedCourses[0];
      target.append(el('p', 'muted', attempt.recommendationNote));
      target.append(course
        ? link(`Explore ${course.title}`, `/course.html?slug=${encodeURIComponent(course.slug)}`, true)
        : link('Explore available courses', '/courses.html', true));
      target.append(link('Review placement result', `/placement-test.html?attempt=${encodeURIComponent(attempt.id)}`));
    } else if (active) {
      target.append(el('h2', undefined, 'Your placement test is saved'), el('p', 'muted', 'Continue when you are ready. You can keep learning in the meantime.'));
      target.append(link('Resume placement test', `/placement-test.html?attempt=${encodeURIComponent(active.id)}`, true));
    } else {
      target.append(el('h2', undefined, skipped ? 'Find your starting level whenever you are ready' : 'Welcome! Find a course that fits you'),
        el('p', 'muted', 'Try the 20–30 minute placement test for an approximate starting point. It is optional and does not change your XP or profile level.'));
      target.append(link('Find my starting point', '/placement-test.html', !skipped));
      if (!skipped) {
        const skip = el('button', 'btn btn-ghost', 'Skip for now');
        skip.type = 'button';
        skip.addEventListener('click', () => {
          try { localStorage.setItem(key, 'skipped'); } catch { /* Still dismiss for this visit. */ }
          target.replaceChildren(el('h2', undefined, 'Choose your own starting point'),
            el('p', 'muted', 'Browse courses now. Placement Test is always available in the navigation.'), link('Browse courses', '/courses.html', true));
        });
        target.append(skip);
      }
    }
  } catch (error) {
    target.replaceChildren(el('h2', undefined, 'Placement guidance is unavailable'), el('p', 'muted', describeApiError(error)));
    const retry = el('button', 'btn btn-secondary', 'Try again'); retry.type = 'button';
    retry.addEventListener('click', () => mountPlacementGuidance(target, user));
    target.append(retry, link('Browse courses', '/courses.html'));
  }
}
