// Measured reading time against the real backend: heartbeat rules, statistics and display.
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

const apiJson = (page, path) =>
  page.evaluate(async (target) => {
    const refreshed = await (
      await fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' })
    ).json();
    const response = await fetch(`/api/v1${target}`, {
      headers: { Authorization: `Bearer ${refreshed.accessToken}` },
    });
    return response.json();
  }, path);

test('no heartbeat is sent for an idle page; reading sends them and time shows up everywhere', async ({
  page,
}) => {
  test.setTimeout(120_000);
  await register(page);
  const beats = [];
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().endsWith('/heartbeat')) {
      beats.push({ at: Date.now(), body: request.postData() });
    }
  });

  await page.goto('/reading-article.html?slug=a-weekend-in-the-city');
  await expect(page.locator('#article-title')).toHaveText('A weekend in the city');
  // Idle: the page is open but nobody interacts. Nothing may be sent for a full interval.
  await page.waitForTimeout(17_000);
  expect(beats).toHaveLength(0);

  // Reading: keep interacting for ~35 s so that two or more heartbeats go out.
  const started = Date.now();
  while (Date.now() - started < 35_000) {
    await page.mouse.move(100 + (Date.now() % 50), 200);
    await page.mouse.wheel(0, 5);
    await page.waitForTimeout(2_000);
  }
  expect(beats.length).toBeGreaterThanOrEqual(2);
  expect(beats.length).toBeLessThanOrEqual(3); // 15 s interval: no bursts
  for (const beat of beats) expect(JSON.parse(beat.body)).toEqual({ active: true }); // no client time

  const study = await apiJson(page, '/reading/study-time?days=7');
  expect(study.totalSeconds).toBeGreaterThanOrEqual(10);
  expect(study.totalSeconds).toBeLessThanOrEqual(40); // never more than the real reading time
  expect(study.todaySeconds).toBe(study.totalSeconds);
  expect(study.byArticle[0].slug).toBe('a-weekend-in-the-city');

  await expect(page.locator('#article-time')).toContainText('Time reading:');

  const progress = await apiJson(page, '/progress/me');
  expect(progress.readingStudy.totalSeconds).toBe(study.totalSeconds);
  expect(progress.xp).toBe(0); // reading time never awards XP
  expect(progress.studyMinutes).toBe(0); // the lesson estimate is untouched

  await page.goto('/progress.html');
  await expect(page.locator('.progress-metric', { hasText: 'Reading time' })).toBeVisible();
});

test('a hidden tab stops sending heartbeats', async ({ page }) => {
  test.setTimeout(90_000);
  await register(page);
  let beats = 0;
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().endsWith('/heartbeat')) beats += 1;
  });
  await page.goto('/reading-article.html?slug=my-day');
  await expect(page.locator('#article-title')).toHaveText('My day');
  await page.mouse.move(120, 220);
  // Pretend the tab is in the background.
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
  });
  for (let i = 0; i < 4; i++) {
    await page.mouse.move(130 + i, 230);
    await page.waitForTimeout(5_000);
  }
  expect(beats).toBe(0);
});
