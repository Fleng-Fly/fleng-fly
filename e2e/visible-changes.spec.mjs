// What a learner actually sees after Learning Experience 2.0, starting from the first course
// in the catalog (a seeded demo course), not only from the curriculum lessons.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

async function register(page) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill('Visible E2E');
  await page.getByLabel('Email', { exact: true }).fill(`visible-${randomUUID()}@example.com`);
  await page.getByLabel('Password').fill('e2e-correct-horse-battery');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/dashboard\.html$/);
}

async function finishLesson(page, slug) {
  return page.evaluate(async (lessonSlug) => {
    const api = await import('/js/api.js');
    const lesson = await api.getLesson(lessonSlug);
    await api.startLesson(lessonSlug);
    let last;
    for (const exercise of lesson.exercises) {
      const probe = exercise.type === 'single_choice' ? exercise.options[0].id : 'probe';
      const assessment = exercise.type === 'self_check' ? { selfAssessment: 'correct' } : {};
      last = await api.submitAnswer(lessonSlug, { exerciseId: exercise.id, answer: probe, ...assessment });
      if (!last.isCorrect) {
        const answer = last.correctOptionId ?? last.acceptedAnswers[0];
        last = await api.submitAnswer(lessonSlug, { exerciseId: exercise.id, answer });
      }
    }
    return last.lesson;
  }, slug);
}

test('the first course in the catalog opens a lesson with ten exercises, tasks and AI help', async ({ page }) => {
  await register(page);
  await page.goto('/courses.html');
  const first = page.locator('a[href*="course.html"]').first();
  await expect(first).toBeVisible();
  await first.click();
  await page.locator('a[href*="lesson.html"]').first().click();
  await expect(page).toHaveURL(/lesson\.html/);
  await page.getByRole('tab', { name: 'Practice' }).click();
  const card = page.locator('.lesson-question');
  await expect(card.locator('.lesson-question-meta')).toContainText('/ 10');
  await expect(card.locator('.lesson-instruction')).toContainText('Task:');
  await expect(card.getByRole('button', { name: "I don't understand" })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Fleng AI' })).toBeVisible();
});

test('finishing the first demo lesson collects its ten words into the dictionary', async ({ page }) => {
  await register(page);
  await page.goto('/lesson.html?slug=greetings-and-introductions');
  const lesson = await finishLesson(page, 'greetings-and-introductions');
  expect(lesson.completed).toBe(true);
  expect(lesson.exercisesTotal).toBe(10);
  await page.goto('/vocabulary.html');
  await expect(page.locator('#word-count')).toHaveText('10 words');
  await expect(page.locator('#word-list')).toContainText('goodbye');
  await expect(page.locator('#word-course')).toBeVisible();
  await expect(page.locator('#word-lesson')).toBeVisible();
  await page.locator('#word-search').fill('дякую');
  await expect(page.locator('#word-count')).toHaveText('1 word');
  await expect(page.locator('#word-list')).toContainText('thank you');
});

test('theory shows the rule as short numbered steps with the extras folded away', async ({ page }) => {
  await register(page);
  await page.goto('/lesson.html?slug=fleng-a0-classroom');
  const steps = page.locator('.lesson-rule-steps li');
  await expect(steps.first()).toBeVisible();
  const texts = await steps.allTextContents();
  expect(texts.length).toBeGreaterThanOrEqual(3);
  // No step is a lone one- or two-word fragment such as "Listen." or "Write.".
  for (const text of texts) expect(text.trim().split(/\s+/).length, text).toBeGreaterThan(2);
  const more = page.locator('details.lesson-theory-more');
  await expect(more).toBeVisible();
  await expect(more).not.toHaveAttribute('open', '');
});

test('Settings offers to connect Google when the server has it configured', async ({ page }) => {
  await register(page);
  // Only the server flag is simulated: Google credentials are not available in this environment.
  await page.route('**/api/v1/auth/providers', (route) => route.fulfill({ json: { google: true } }));
  await page.goto('/settings.html');
  await expect(page.locator('#google-card')).toBeVisible();
  await expect(page.locator('#google-link-form')).toBeVisible();
  await expect(page.getByLabel('Confirm your password')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Connect Google' })).toBeVisible();
});

test('the sidebar has one "My Words" link next to "Courses" and no Words group', async ({ page }) => {
  await register(page);
  const nav = page.locator('#dashboard-sidebar nav.sidebar-nav');
  await expect(nav.locator('details')).toHaveCount(0);
  await expect(nav.getByText('Course Words')).toHaveCount(0);
  await expect(nav.getByRole('link', { name: 'Courses' })).toBeVisible();
  const myWords = nav.getByRole('link', { name: 'My Words' });
  await expect(myWords).toBeVisible();
  await myWords.click();
  await expect(page).toHaveURL(/\/vocabulary\.html$/);
  await expect(page.locator('#dashboard-sidebar a[aria-current="page"]')).toHaveText('My Words');
  // The Course Words page keeps its URL, it is just not in the menu.
  await page.goto('/course-words.html');
  await expect(page.locator('h1')).toContainText('Course Words');
});
