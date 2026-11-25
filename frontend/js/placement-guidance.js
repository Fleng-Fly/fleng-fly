import { el } from './layout.js';
import { getPlacement, listPlacements } from './placement-api.js';
import { describeApiError } from './errors.js';
import { t } from './i18n.js';
import { placementLabel, placementRecommendation } from './placement-copy.js';

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
  target.replaceChildren(el('p', 'muted', t('common.loading')));
  try {
    const recent = await listPlacements();
    const completed = recent.find(attempt => attempt.status === 'completed');
    const active = recent.find(attempt => attempt.status === 'in_progress');
    target.replaceChildren();
    if (completed) {
      const attempt = await getPlacement(completed.id);
      target.append(el('h2', undefined, t('guide.suggestedTitle')), el('p', undefined, placementLabel(attempt.result)));
      const course = attempt.recommendedCourses[0];
      target.append(el('p', 'muted', placementRecommendation(attempt)));
      target.append(course
        ? link(t('guide.explore', { title: course.title }), `/course.html?slug=${encodeURIComponent(course.slug)}`, true)
        : link(t('guide.exploreAll'), '/courses.html', true));
      target.append(link(t('guide.reviewResult'), `/placement-test.html?attempt=${encodeURIComponent(attempt.id)}`));
    } else if (active) {
      target.append(el('h2', undefined, t('guide.savedTitle')), el('p', 'muted', t('guide.savedText')));
      target.append(link(t('guide.resume'), `/placement-test.html?attempt=${encodeURIComponent(active.id)}`, true));
    } else {
      target.append(el('h2', undefined, skipped ? t('guide.laterTitle') : t('guide.newTitle')),
        el('p', 'muted', t('guide.newText')));
      target.append(link(t('guide.start'), '/placement-test.html', !skipped));
      if (!skipped) {
        const skip = el('button', 'btn btn-ghost', t('guide.skip'));
        skip.type = 'button';
        skip.addEventListener('click', () => {
          try { localStorage.setItem(key, 'skipped'); } catch { /* Still dismiss for this visit. */ }
          target.replaceChildren(el('h2', undefined, t('guide.skippedTitle')),
            el('p', 'muted', t('guide.skippedText')), link(t('dashboard.browse'), '/courses.html', true));
        });
        target.append(skip);
      }
    }
  } catch (error) {
    target.replaceChildren(el('h2', undefined, t('guide.unavailable')), el('p', 'muted', describeApiError(error)));
    const retry = el('button', 'btn btn-secondary', t('common.tryAgain')); retry.type = 'button';
    retry.addEventListener('click', () => mountPlacementGuidance(target, user));
    target.append(retry, link(t('dashboard.browse'), '/courses.html'));
  }
}
