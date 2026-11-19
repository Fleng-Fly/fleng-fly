// Placement Test inside Courses, against the real backend (no mocked API responses).
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

test('Placement Test is reached from Courses, not from the sidebar', async ({ page }) => {
  await register(page);
  const sidebar = page.locator('#dashboard-sidebar');
  await expect(sidebar.getByRole('link', { name: 'Level test' })).toHaveCount(0);
  await expect(sidebar.locator('a[href="/placement-test.html"]')).toHaveCount(0);
  await page.goto('/courses.html');
  await page.getByRole('link', { name: 'Find your level' }).click();
  await expect(page).toHaveURL(/\/placement-test\.html$/);
  // Breadcrumb, Courses stays highlighted in the sidebar.
  await expect(page.locator('.pt-breadcrumb')).toContainText('Courses');
  await expect(page.locator('.pt-breadcrumb [aria-current="page"]')).toHaveText('Placement Test');
  await expect(sidebar.locator('a[aria-current="page"]')).toHaveText('Courses');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Discover your English level');
  await expect(page.locator('.pt-facts li')).toHaveText(['36 questions', '20–30 minutes', 'A1–B2']);
  await expect(page.locator('#placement-levels li')).toHaveCount(4);
  await expect(page.locator('#placement-levels .pt-current')).toHaveCount(0);
  await expect(page.locator('#placement-history-status')).toContainText('No attempts yet');
});

test('start, resume an unfinished attempt and see it in the history', async ({ page }) => {
  await register(page);
  await page.goto('/placement-test.html');
  const start = page.getByRole('button', { name: 'Start placement test' });
  await expect(start).toBeEnabled();
  await start.click();
  await expect(page.locator('#placement-player')).toBeVisible();
  await expect(page.locator('#placement-intro')).toBeHidden();
  await page.locator('#placement-question input').first().check();
  await expect(page.locator('#placement-saved')).toContainText('1 of 36');
  const url = page.url();
  expect(url).toMatch(/attempt=/);
  // Resume by URL: the saved answer is restored without starting another attempt.
  await page.goto(url);
  await expect(page.locator('#placement-question input:checked')).toHaveCount(1);
  await page.goto('/placement-test.html');
  await expect(page.locator('.pt-attempt')).toHaveCount(1);
  await expect(page.locator('.pt-attempt')).toContainText('Resume · 1/36');
  await page.locator('.pt-attempt .pt-link').click();
  await expect(page.locator('#placement-question input:checked')).toHaveCount(1);
});

test('the page is available in Ukrainian and fits a phone screen', async ({ page }) => {
  await register(page);
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto('/placement-test.html');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Discover your English level');
  await page.locator('.lang-switch').getByRole('button', { name: /УК|UK/ }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Дізнайтеся свій рівень англійської');
  await expect(page.getByRole('button', { name: 'Розпочати тест рівня' })).toBeVisible();
  await expect(page.locator('#placement-levels li').first()).toContainText('Початківець');
  const size = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth }));
  expect(size.content).toBeLessThanOrEqual(size.viewport + 1);
});
