// Real integrated UI checks: shared shell, responsive pages and persisted EN/UK.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

const pages = [
  '/dashboard.html',
  '/courses.html',
  '/course.html?slug=english-foundations',
  '/lesson.html?slug=greetings-and-introductions',
  '/vocabulary.html',
  '/course-words.html',
  '/progress.html',
  '/leaderboard.html',
  '/settings.html',
  '/placement-test.html',
];

async function signIn(page) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill('Responsive Learner');
  await page.getByLabel('Email', { exact: true }).fill(`responsive-${randomUUID()}@example.com`);
  await page.getByLabel('Password').fill('responsive-test-password');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/dashboard\.html$/);
  await expect(page.locator('#dashboard-level')).toContainText('XP');
}

for (const width of [1440, 768, 390, 360]) {
  test(`integrated pages fit ${width}px and mobile navigation stays accessible`, async ({
    page,
  }, info) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width, height: 900 });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    await expect(page.locator('.hero a[href="/register.html"]')).toBeVisible();
    await signIn(page);
    for (const path of pages) {
      await page.goto(path);
      await expect(page.locator('main')).toBeVisible();
      if (path !== '/placement-test.html') {
        await expect(page.locator('#profile-short-name')).toContainText('Responsive');
      } else {
        await expect(page.locator('#placement-start')).toBeEnabled();
      }
      await page.waitForLoadState('networkidle');
      const size = await page.evaluate(() => ({
        viewport: document.documentElement.clientWidth,
        content: document.documentElement.scrollWidth,
      }));
      expect(size.content, `${path} at ${width}px`).toBeLessThanOrEqual(size.viewport + 1);
      if (path === '/dashboard.html' || path.startsWith('/lesson.html')) {
        await page.screenshot({
          path: info.outputPath(
            `${path.includes('dashboard') ? 'dashboard' : 'lesson'}-${width}.png`,
          ),
          fullPage: true,
        });
      }
    }
    if (width <= 768) {
      await page.goto('/dashboard.html');
      const open = page.locator('#nav-open');
      await open.click();
      await expect(open).toHaveAttribute('aria-expanded', 'true');
      await expect(page.locator('#dashboard-sidebar')).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(open).toHaveAttribute('aria-expanded', 'false');
      await expect(open).toBeFocused();
    }
    expect(errors).toEqual([]);
  });
}

test('EN/UK switch persists to the account and keeps shared pages usable', async ({ page }) => {
  await signIn(page);
  await Promise.all([
    page.waitForEvent('domcontentloaded'),
    page.locator('button[data-lang="uk"]').click(),
  ]);
  await expect(page.locator('html')).toHaveAttribute('lang', 'uk');
  await expect(page.locator('h1')).toHaveText('Вітаємо, Responsive Learner');
  await expect
    .poll(() =>
      page.evaluate(
        async () => (await (await import('/js/api.js')).getCurrentUser()).preferredLanguage,
      ),
    )
    .toBe('Ukrainian');
  await page.reload();
  await expect(page.locator('#dashboard-level')).toContainText('XP');
  await expect(page.locator('html')).toHaveAttribute('lang', 'uk');
  await page.goto('/vocabulary.html');
  await expect(page.locator('html')).toHaveAttribute('lang', 'uk');
  await expect(page.locator('#profile-short-name')).toContainText('Responsive');
  await Promise.all([
    page.waitForEvent('domcontentloaded'),
    page.locator('button[data-lang="en"]').click(),
  ]);
  await expect(page.locator('#profile-short-name')).toContainText('Responsive');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect
    .poll(() =>
      page.evaluate(
        async () => (await (await import('/js/api.js')).getCurrentUser()).preferredLanguage,
      ),
    )
    .toBe('English');
});

test('A0 sidecar guide, hint and Ukrainian wrong-answer explanation survive integration', async ({
  page,
}) => {
  await signIn(page);
  const lesson = await (await page.request.get('/api/v1/lessons/fleng-a0-hello')).json();
  const exercise = lesson.exercises[0];
  await page.goto('/lesson.html?slug=fleng-a0-hello');
  await expect(page.locator('.lesson-guide-text')).toHaveText(lesson.guide.explanation.en);
  await Promise.all([
    page.waitForEvent('domcontentloaded'),
    page.locator('button[data-lang="uk"]').click(),
  ]);
  await expect(page.locator('.lesson-guide-text')).toHaveText(lesson.guide.explanation.uk);
  await page.locator('#tab-practice').click();
  await page.locator('.lesson-hint-toggle').click();
  await expect(page.locator('.lesson-hint-text')).toHaveText(exercise.hint.uk);
  expect(
    await page.evaluate(async () => (await (await import('/js/api.js')).getMyProgress()).xp),
  ).toBe(0);
  await page
    .locator('.lesson-option')
    .filter({ has: page.getByText('are', { exact: true }) })
    .getByRole('radio')
    .check();
  const submission = page.waitForResponse(
    (response) => response.url().endsWith('/submit') && response.request().method() === 'POST',
  );
  await page.locator('.lesson-answer-form button[type="submit"]').click();
  const graded = await (await submission).json();
  expect(graded.isCorrect).toBe(false);
  expect(graded.xpAwarded).toBe(0);
  await expect(page.locator('#lesson-last-answer')).toContainText(graded.wrongAnswerNote.uk);
  await expect(page.locator('#lesson-last-answer')).toContainText(graded.explanationLocalized.uk);
});
