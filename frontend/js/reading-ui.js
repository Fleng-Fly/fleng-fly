/** Small pieces shared by the Reading pages. All text goes through textContent / t(). */
import { setReadingBookmark } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { t, tn } from './i18n.js';

export const LEVELS = ['A0', 'A1', 'A2', 'B1', 'B2'];

export const levelBadge = (level) =>
  el('span', `reading-level reading-level-${level.toLowerCase()}`, level);

export const minutesText = (minutes) => tn('rd.minutes', minutes, { n: minutes });

/** Short status line for an article's progress, or `null` before the first visit. */
export function progressText(progress) {
  if (!progress) return null;
  if (progress.status === 'completed') return t('rd.completed');
  return progress.readPercent > 0 ? t('rd.percentRead', { percent: progress.readPercent }) : null;
}

/**
 * A bookmark toggle button. It flips immediately and rolls back (with `onError`) when the
 * server rejects the change; `onChange(bookmarked)` fires only after a confirmed save.
 */
export function bookmarkButton(article, { onChange = () => {}, onError = () => {} } = {}) {
  const button = el('button', 'reading-bookmark');
  button.type = 'button';
  const paint = () => {
    const on = Boolean(article.bookmarked);
    button.setAttribute('aria-pressed', String(on));
    button.setAttribute('aria-label', on ? t('rd.unbookmark') : t('rd.bookmark'));
    button.title = on ? t('rd.unbookmark') : t('rd.bookmark');
    button.textContent = on ? '★' : '☆';
  };
  paint();
  button.addEventListener('click', async () => {
    const next = !article.bookmarked;
    article.bookmarked = next;
    button.disabled = true;
    paint();
    try {
      await setReadingBookmark(article.slug, next);
      onChange(next);
    } catch (error) {
      article.bookmarked = !next;
      paint();
      onError(error.status ? describeApiError(error) : t('rd.bookmarkFailed'));
    } finally {
      button.disabled = false;
    }
  });
  return button;
}
