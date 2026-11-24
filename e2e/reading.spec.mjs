// Reading against the real backend: library, filters, bookmarks, topics, progress, quiz, XP.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

async function register(page) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill(`E2E ${randomUUID().slice(0, 8)}`);
  await page.getByLabel('Email', { exact: true }).fill(`e2e-${randomUUID()}@example.com`);
  await page.getByLabel('Password').fill('e2e-correct-horse-battery');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/dashboard\.html$/);
}

const card = (page, title) => page.locator('.reading-card', { hasText: title });

test('library lists both published demo articles and the sidebar links to Reading', async ({
  page,
}) => {
  await register(page);
  await page.locator('#dashboard-sidebar').getByRole('link', { name: 'Reading' }).click();
  await expect(page).toHaveURL(/\/reading\.html$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Reading');
  await expect(page.locator('.reading-card')).toHaveCount(2);
  await expect(page.locator('#dashboard-sidebar a[aria-current="page"]')).toHaveText('Reading');
  await expect(page.locator('#reading-count')).toBeHidden();
});

test('level and status filters, empty state and clearing', async ({ page }) => {
  await register(page);
  await page.goto('/reading.html');
  await expect(page.locator('.reading-card')).toHaveCount(2);
  await page.locator('#filter-level').getByRole('button', { name: 'A0', exact: true }).click();
  await expect(page.locator('.reading-card')).toHaveCount(1);
  await expect(card(page, 'My day')).toBeVisible();
  await page.locator('#filter-level').getByRole('button', { name: 'B2', exact: true }).click();
  await expect(page.locator('#reading-empty')).toBeVisible();
  await expect(page.locator('#reading-empty-title')).toHaveText('Nothing matches these filters');
  await page.getByRole('button', { name: 'Clear filters' }).click();
  await expect(page.locator('.reading-card')).toHaveCount(2);
  await page.locator('#filter-status').getByRole('button', { name: 'Completed' }).click();
  await expect(page.locator('#reading-empty')).toBeVisible();
});

test('bookmarks persist and the Saved filter shows them', async ({ page }) => {
  await register(page);
  await page.goto('/reading.html');
  await card(page, 'My day').getByRole('button', { name: 'Save article' }).click();
  await expect(
    card(page, 'My day').getByRole('button', { name: 'Remove from saved' }),
  ).toBeVisible();
  await page.reload();
  await page.locator('#filter-status').getByRole('button', { name: 'Saved' }).click();
  await expect(page.locator('.reading-card')).toHaveCount(1);
  await card(page, 'My day').getByRole('button', { name: 'Remove from saved' }).click();
  await expect(page.locator('#reading-empty')).toBeVisible();
});

test('topic preferences are saved, shown first and usable as a filter', async ({ page }) => {
  await register(page);
  await page.goto('/reading.html');
  await expect(
    page.locator('#filter-topic').getByRole('button', { name: /My topics/ }),
  ).toHaveCount(0);
  await page.getByRole('button', { name: 'Choose my topics' }).click();
  await page.getByLabel('Daily life').check();
  await page.getByRole('button', { name: 'Save topics' }).click();
  await expect(page.locator('#topics-dialog')).toBeHidden();
  await page
    .locator('#filter-topic')
    .getByRole('button', { name: /My topics/ })
    .click();
  await expect(page.locator('.reading-card')).toHaveCount(2);
  await page.reload();
  await expect(
    page.locator('#filter-topic').getByRole('button', { name: /★ Daily life/ }),
  ).toBeVisible();
});

test('quiz: no answer key before submit, autosave and resume, fail then pass with XP once', async ({
  page,
}) => {
  await register(page);
  await page.goto('/reading.html');
  await card(page, 'My day').getByRole('link', { name: 'My day' }).click();
  await expect(page.locator('#article-title')).toHaveText('My day');
  await page.getByRole('button', { name: 'Start quiz' }).click();
  await expect(page.locator('.reading-question')).toHaveCount(3);

  // The page must not contain any answer key or explanation before the attempt is submitted.
  const html = await page.content();
  expect(html).not.toContain('The text says');
  expect(html).not.toMatch(/is-correct/);

  // Answer one question, wait for the autosave, reload and resume with the answer restored.
  await page.locator('.reading-question').first().getByLabel("At six o'clock.").check();
  await expect(page.locator('.reading-save-state')).toHaveText('Answers saved', {
    timeout: 10_000,
  });
  await page.reload();
  await page.getByRole('button', { name: 'Resume quiz' }).click();
  await expect(
    page.locator('.reading-question').first().getByLabel("At six o'clock."),
  ).toBeChecked();
  await expect(page.locator('.reading-counter')).toHaveText('1 of 3 answered');
  await expect(page.getByRole('button', { name: 'Submit answers' })).toBeDisabled();

  // Fail first: wrong answers everywhere.
  const q = page.locator('.reading-question');
  await q.nth(1).getByLabel('By car.').check();
  await q.nth(2).getByLabel('Her sister.').check();
  await page.getByRole('button', { name: 'Submit answers' }).click();
  await expect(page.locator('.reading-result')).toContainText('Not quite');
  await expect(page.locator('.reading-xp')).toHaveCount(0);
  await expect(page.locator('.reading-explanation').first()).toContainText('The text says');

  // Retry with the right answers: pass, XP shown once.
  await page.getByRole('button', { name: 'Try again' }).click();
  await page
    .getByRole('button', { name: 'Start quiz' })
    .or(page.getByRole('button', { name: 'Try again' }))
    .first()
    .click();
  await q.nth(0).getByLabel("At seven o'clock.").check();
  await q.nth(1).getByLabel('By bus.').check();
  await q.nth(2).getByLabel('Her brother.').check();
  await page.getByRole('button', { name: 'Submit answers' }).click();
  await expect(page.locator('.reading-result')).toContainText('Well done');
  await expect(page.locator('.reading-xp')).toHaveText('+3 XP');
  await expect(page.locator('#article-status')).toHaveText('Completed');

  // A further pass pays nothing more.
  await page.getByRole('button', { name: 'Try again' }).click();
  await page.getByRole('button', { name: 'Try again' }).first().click();
  await q.nth(0).getByLabel("At seven o'clock.").check();
  await q.nth(1).getByLabel('By bus.').check();
  await q.nth(2).getByLabel('Her brother.').check();
  await page.getByRole('button', { name: 'Submit answers' }).click();
  await expect(page.locator('.reading-result')).toContainText('already earned XP');
  const progress = await page.evaluate(async () => {
    const token = (
      await (await fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' })).json()
    ).accessToken;
    return (
      await fetch('/api/v1/progress/me', { headers: { Authorization: `Bearer ${token}` } })
    ).json();
  });
  expect(progress.xp).toBe(3);
});

test('reading progress is saved while scrolling, with throttled writes', async ({ page }) => {
  await register(page);
  const writes = [];
  page.on('request', (request) => {
    if (request.method() === 'PUT' && request.url().includes('/progress'))
      writes.push(request.url());
  });
  await page.goto('/reading-article.html?slug=a-weekend-in-the-city');
  await expect(page.locator('#article-title')).toHaveText('A weekend in the city');
  await page.setViewportSize({ width: 360, height: 300 });
  for (let i = 0; i < 40; i++) {
    await page.mouse.wheel(0, 40);
    await page.waitForTimeout(25);
  }
  await page.waitForTimeout(7000);
  expect(writes.length).toBeGreaterThanOrEqual(1);
  expect(writes.length).toBeLessThanOrEqual(3); // ~1s of scrolling + 7s wait at 5s spacing
  // The saved percentage is restored after a reload (wait for the article to render first).
  await page.reload();
  await expect(page.locator('#article-title')).toHaveText('A weekend in the city');
  await expect
    .poll(async () => Number(await page.locator('#read-progress').getAttribute('aria-valuenow')))
    .toBeGreaterThan(0);
});

test('unknown and missing articles show a clear state', async ({ page }) => {
  await register(page);
  await page.goto('/reading-article.html?slug=does-not-exist');
  await expect(page.locator('#article-missing')).toBeVisible();
  await expect(page.getByRole('heading', { name: "This article isn't available" })).toBeVisible();
  await page.goto('/reading-article.html');
  await expect(page.locator('#article-missing')).toBeVisible();
});

test('mobile layout has no horizontal scroll and the quiz is usable', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await register(page);
  for (const path of ['/reading.html', '/reading-article.html?slug=my-day']) {
    await page.goto(path);
    await page.waitForLoadState('networkidle');
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, path).toBeLessThanOrEqual(0);
  }
  await page.getByRole('button', { name: 'Start quiz' }).click();
  await expect(page.locator('.reading-question')).toHaveCount(3);
});
