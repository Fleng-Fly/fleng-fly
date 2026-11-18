// Refresh-token rotation in a real browser: a rotation response that never reaches the page
// (navigation, network drop) must not sign the learner out. No server behaviour is mocked.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

async function register(page) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill('Refresh E2E');
  await page.getByLabel('Email', { exact: true }).fill(`refresh-${randomUUID()}@example.com`);
  await page.getByLabel('Password').fill('e2e-correct-horse-battery');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/dashboard\.html$/);
  await page.waitForLoadState('networkidle');
}

const stillSignedIn = async (page) => (await page.request.post('/api/v1/auth/refresh')).ok();

test('a refresh response lost after the server rotated the token does not end the session', async ({ page }) => {
  await register(page);
  const before = await page.context().cookies();
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fetch(); // the server rotates the token
    await page.context().clearCookies();
    await page.context().addCookies(before); // the browser never stored the new cookie
    await route.abort('failed');
  });
  await page.goto('/dashboard.html');
  await page.waitForTimeout(500);
  await page.unroute('**/api/v1/auth/refresh');
  expect(await stillSignedIn(page)).toBe(true);
  await page.goto('/dashboard.html');
  await expect(page).toHaveURL(/\/dashboard\.html$/);
});

test('leaving the dashboard while its refresh is in flight keeps the learner signed in', async ({ page }) => {
  test.setTimeout(120_000);
  await register(page);
  for (let round = 0; round < 10; round++) {
    for (const path of ['/', '/index.html', '/login.html', '/register.html']) {
      await page.goto(path);
      await expect(page, `${path} (round ${round})`).toHaveURL(/\/dashboard\.html$/);
    }
  }
  expect(await stillSignedIn(page)).toBe(true);
});
