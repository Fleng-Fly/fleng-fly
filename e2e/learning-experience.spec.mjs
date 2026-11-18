// Learning Experience 2.0 in a real browser against the real backend (see e2e/server.mjs):
// session restoration, task instructions, "I don't understand" and the personal dictionary.
// No API response is mocked; lesson answers are learned from the server's own grading results.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

const LESSON = 'fleng-a0-classroom';

async function register(page) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill(`E2E ${randomUUID().slice(0, 8)}`);
  await page.getByLabel('Email', { exact: true }).fill(`e2e-${randomUUID()}@example.com`);
  await page.getByLabel('Password').fill('e2e-correct-horse-battery');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/dashboard\.html$/);
}

test('a signed-in learner opening the site lands on the dashboard, signed-out on the landing page', async ({ page }) => {
  await register(page);
  for (const path of ['/', '/index.html', '/login.html', '/register.html']) {
    await page.goto(path);
    await expect(page, path).toHaveURL(/\/dashboard\.html$/);
    // Let the dashboard finish its session refresh before the next navigation: the refresh
    // cookie rotates on every load, and an aborted request would lose the new cookie.
    await page.waitForLoadState('networkidle');
  }
  // Google is not configured here, so Settings must not offer to connect it.
  await page.goto('/settings.html');
  await expect(page.locator('#settings-content')).toBeVisible();
  await expect(page.locator('#google-card')).toBeHidden();
  await page.waitForLoadState('networkidle');
  // Google is not configured in this environment, so its button stays hidden.
  await page.context().clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.goto('/login.html');
  await expect(page.locator('#login-form')).toBeVisible();
  await expect(page.locator('#google-block')).toBeHidden();
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Start learning' })).toBeVisible();
});

test('every exercise states its task and "I don\'t understand" keeps the draft answer', async ({ page }) => {
  await register(page);
  await page.goto(`/lesson.html?slug=${LESSON}&tab=practice`);
  const card = page.locator('.lesson-question');
  await expect(card.locator('.lesson-instruction')).toContainText('Task:');
  await expect(card.locator('.lesson-question-meta')).toContainText('/ 12');

  // Go to the typed gap-fill (question 9) and leave a draft answer.
  for (let i = 0; i < 8; i++) await page.getByRole('button', { name: /Next/ }).click();
  await expect(card.locator('.lesson-instruction')).toContainText('Type only the missing word');
  await card.locator('input.lesson-answer').fill('ope');
  await card.getByRole('button', { name: "I don't understand" }).click();
  const panel = page.locator('#ai-panel');
  await expect(panel).toBeVisible();
  await expect(panel.locator('.ai-context')).toContainText('Question 9');
  // AI is disabled here: the panel says so and nothing is sent.
  await expect(panel).toContainText('unavailable');
  await panel.getByRole('button', { name: 'Back to the exercise' }).click();
  await expect(panel).toBeHidden();
  await expect(card.locator('input.lesson-answer')).toHaveValue('ope');
});

test('finishing a lesson fills the personal dictionary once, with course and lesson filters', async ({ page }) => {
  await register(page);
  await page.goto(`/lesson.html?slug=${LESSON}`);
  const completed = await page.evaluate(async (slug) => {
    const api = await import('/js/api.js');
    const lesson = await api.getLesson(slug);
    await api.startLesson(slug);
    let last;
    for (const exercise of lesson.exercises) {
      const probe = exercise.type === 'single_choice' ? exercise.options[0].id : 'probe';
      const assessment = exercise.type === 'self_check' ? { selfAssessment: 'correct' } : {};
      last = await api.submitAnswer(slug, { exerciseId: exercise.id, answer: probe, ...assessment });
      if (!last.isCorrect) {
        const answer = last.correctOptionId ?? last.acceptedAnswers[0];
        last = await api.submitAnswer(slug, { exerciseId: exercise.id, answer });
      }
    }
    return last.lesson;
  }, LESSON);
  expect(completed.completed).toBe(true);
  expect(completed.exercisesTotal).toBe(12);

  await page.goto('/vocabulary.html');
  await expect(page.locator('#word-count')).toHaveText('10 words');
  await expect(page.locator('#word-list')).toContainText('repeat');
  await expect(page.locator('#word-list')).toContainText('A0');
  await page.locator('#word-course').selectOption({ index: 1 });
  await page.locator('#word-lesson').selectOption({ index: 1 });
  await expect(page.locator('#word-count')).toHaveText('10 words');
  await page.locator('#word-search').fill('слухати');
  await expect(page.locator('#word-count')).toHaveText('1 word');
  await expect(page.locator('#word-list')).toContainText('listen');

  // Repeating the lesson does not duplicate words.
  await page.goto(`/lesson.html?slug=${LESSON}`);
  const total = await page.evaluate(async () => {
    const api = await import('/js/api.js');
    return (await api.getVocabularyStats()).totalWords;
  });
  expect(total).toBe(10);
});
