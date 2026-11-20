import { getDailyGoals, updateCurrentUser } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { t } from './i18n.js';
import {
  GOAL_LIMITS,
  browserTimeZone,
  goalMet,
  goalPercent,
  needsTimeZoneSync,
  parseGoalInputs,
} from './daily-goals.js';

function goalRow(label, entry) {
  const row = el('div', `goal-row${goalMet(entry) ? ' is-met' : ''}`);
  const head = el('div', 'goal-head');
  head.append(
    el('span', 'metric-label', label),
    el('strong', 'metric-value', t('dashboard.goalCount', { done: entry.done, goal: entry.goal })),
  );
  const percent = goalPercent(entry.done, entry.goal);
  const track = el('div', 'dashboard-progress-track goal-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', t('dashboard.goalBar', { label }));
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.setAttribute('aria-valuenow', String(percent));
  const fill = el('div', 'dashboard-progress-fill');
  fill.style.width = `${percent}%`;
  track.append(fill);
  row.append(head, track);
  if (goalMet(entry)) row.append(el('small', 'metric-note', t('dashboard.goalDone')));
  return row;
}

function numberField(id, label, limits, value) {
  const wrap = el('label', 'goal-field');
  wrap.setAttribute('for', id);
  const input = el('input', 'goal-input');
  input.id = id;
  input.type = 'number';
  input.inputMode = 'numeric';
  input.min = String(limits.min);
  input.max = String(limits.max);
  input.value = String(value);
  wrap.append(el('span', undefined, label), input);
  return { wrap, input };
}

/** Settings are saved on the profile (synced between devices); progress is read-only. */
function editForm(goals, { onSaved, onCancel }) {
  const form = el('form', 'goal-form');
  const lessons = numberField('goal-lessons', t('dashboard.goalLessons'), GOAL_LIMITS.lessons, goals.lessons.goal);
  const words = numberField('goal-words', t('dashboard.goalWords'), GOAL_LIMITS.words, goals.vocabulary.goal);
  const error = el('p', 'dashboard-muted goal-error');
  error.setAttribute('role', 'alert');
  error.hidden = true;
  const save = el('button', 'dashboard-cta dashboard-cta-small', t('common.save'));
  save.type = 'submit';
  const cancel = el('button', 'dashboard-text-button', t('common.cancel'));
  cancel.type = 'button';
  cancel.addEventListener('click', onCancel);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const parsed = parseGoalInputs(lessons.input.value, words.input.value);
    if (parsed.error) {
      error.textContent = t('dashboard.goalRange', {
        lessonsMax: GOAL_LIMITS.lessons.max,
        wordsMax: GOAL_LIMITS.words.max,
      });
      error.hidden = false;
      return;
    }
    save.disabled = true;
    try {
      await updateCurrentUser(parsed.value);
      await onSaved();
    } catch (failure) {
      error.textContent = describeApiError(failure);
      error.hidden = false;
      save.disabled = false;
    }
  });
  const actions = el('div', 'goal-actions');
  actions.append(save, cancel);
  form.append(lessons.wrap, words.wrap, error, actions);
  return form;
}

/**
 * Render the card body. The browser zone is pushed to the profile first (only when it
 * differs) so the very first read already uses the learner's own day.
 */
export async function mountDailyGoals(target, user) {
  const draw = async () => {
    target.replaceChildren(el('p', 'dashboard-muted', t('common.loading')));
    try {
      const zone = browserTimeZone();
      if (needsTimeZoneSync(user, zone)) {
        try {
          const updated = await updateCurrentUser({ timezone: zone });
          user.timezone = updated?.timezone ?? zone;
        } catch {
          /* The server falls back to its own zone; goals still render. */
        }
      }
      const goals = await getDailyGoals();
      target.replaceChildren();
      const heading = el('div', 'section-heading');
      const title = el('div');
      title.append(
        el('p', 'dashboard-eyebrow', t('dashboard.goalsEyebrow')),
        el('h2', undefined, t('dashboard.goalsTitle')),
      );
      const edit = el('button', 'dashboard-text-button', t('dashboard.goalsEdit'));
      edit.type = 'button';
      edit.addEventListener('click', () => {
        edit.hidden = true;
        target.replaceChildren(
          heading,
          editForm(goals, { onSaved: draw, onCancel: () => draw() }),
        );
      });
      heading.append(title, edit);
      target.append(
        heading,
        goalRow(t('dashboard.goalLessons'), goals.lessons),
        goalRow(t('dashboard.goalWords'), goals.vocabulary),
      );
    } catch (failure) {
      target.replaceChildren(
        el('strong', undefined, t('dashboard.goalsFailed')),
        el('p', 'dashboard-muted', describeApiError(failure)),
      );
      const retry = el('button', 'dashboard-text-button', t('common.tryAgain'));
      retry.type = 'button';
      retry.addEventListener('click', draw);
      target.append(retry);
    }
  };
  await draw();
}
