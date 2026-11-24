import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

const reviewUrl = '**/api/v1/vocabulary/*/review';
const card = (page) => page.locator('.word-practice-card');

async function seedWords(page, input) {
  await page.goto('/register.html');
  await page.locator('#displayName').fill('Mixed practice learner');
  await page.locator('#email').fill(`mixed-${randomUUID()}@example.com`);
  await page.locator('#password').fill('mixed-practice-test-password');
  await page.locator('#submit-button').click();
  await expect(page).toHaveURL(/dashboard\.html$/);
  await expect(page.locator('#dashboard-level')).toContainText('XP');
  return page.evaluate(async (rows) => {
    const api = await import('/js/api.js');
    const saved = await Promise.all(rows.map(([word, translation]) => api.addVocabulary({ word, translation })));
    return Object.fromEntries(saved.map((word) => [word.id, word]));
  }, input);
}

async function open(page, input = []) {
  const words = await seedWords(page, input);
  await page.goto('/vocabulary.html');
  await expect(page.locator('#words-content')).toBeVisible();
  await page.getByRole('button', { name: 'Start Practice', exact: true }).click();
  return words;
}

const snapshot = (page) => page.evaluate(() => {
  const key = Object.keys(sessionStorage).find((name) => name.startsWith('fleng.mixed-practice.v1:'));
  return JSON.parse(sessionStorage.getItem(key));
});

test('Course Words Tests opens Mixed Practice on desktop and mobile', async ({ page }) => {
  await seedWords(page, [['train', 'поїзд'], ['plant', 'рослина'], ['stone', 'камінь'], ['crown', 'корона']]);
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto('/course-words.html');
    const tests = page.getByRole('link', { name: 'Tests', exact: true });
    await expect(tests).toBeVisible();
    await expect(tests).toHaveCSS('background-image', /linear-gradient/);
    await expect(tests.locator('svg')).toBeVisible();
    const subtitle = await page.locator('.dashboard-subtitle').boundingBox();
    const button = await tests.boundingBox();
    const filters = await page.locator('.course-words-toolbar').boundingBox();
    expect(button.y).toBeGreaterThanOrEqual(subtitle.y + subtitle.height);
    expect(button.y + button.height).toBeLessThanOrEqual(filters.y);
    expect(button.x).toBeCloseTo(subtitle.x);
    expect(button.x + button.width).toBeLessThanOrEqual(viewport.width);
    expect(button.height).toBeGreaterThanOrEqual(44);
    await tests.click();
    await expect(page).toHaveURL(/vocabulary\.html\?mode=mixed$/);
    await expect(page.getByRole('heading', { name: 'Mixed Practice' })).toBeVisible();
    await expect(card(page)).toBeVisible();
    expect((await snapshot(page)).tasks.map((task) => task.type).sort()).toEqual(['choice', 'flashcards', 'letters', 'write']);
  }
});

async function answer(page, words, remembered, pause = false) {
  const current = card(page);
  const id = await current.getAttribute('data-word-id');
  const type = await current.getAttribute('data-task-type');
  const word = words[id];
  const response = page.waitForResponse((entry) => entry.url().endsWith(`/${id}/review`));
  if (type === 'flashcards') {
    await current.getByRole('button', { name: 'Reveal translation', exact: true }).click();
    await current.getByRole('button', { name: remembered ? /^I knew it/ : /^I need practice$/ }).click();
  } else if (type === 'choice') {
    const options = current.locator('.word-choice');
    const choice = remembered ? options.filter({ hasText: word.translation }).first()
      : options.filter({ hasNotText: word.translation }).first();
    await choice.click();
  } else if (type === 'write') {
    const input = current.locator('input');
    const start = Date.now();
    await input.fill(remembered ? `  ${word.word.toUpperCase()}  ` : 'wrong');
    if (!pause) await input.press('Enter');
    expect((await response).ok()).toBe(true);
    if (pause) expect(Date.now() - start).toBeGreaterThanOrEqual(1450);
    return;
  } else {
    expect(type).toBe('letters');
    const missing = [...word.word].filter((_, index) => index % 3 !== 0);
    if (!remembered) [missing[0], missing[1]] = [missing[1], missing[0]];
    for (const [index, letter] of missing.entries()) {
      await current.getByRole('group', { name: 'Available letters' }).getByRole('button', { name: letter, exact: true }).first().click();
      await current.locator('.lesson-tile-slot').nth(index).click();
    }
  }
  expect((await response).ok()).toBe(true);
}

test('mixed practice runs all four types, restores FIFO and finishes only after correction', async ({ page }) => {
  const words = await open(page, [['train', 'поїзд'], ['plant', 'рослина'], ['stone', 'камінь'], ['crown', 'корона']]);
  await expect(page.getByRole('heading', { name: 'Mixed Practice' })).toBeVisible();
  const initial = await snapshot(page);
  expect(initial.tasks.map((task) => task.type).sort()).toEqual(['choice', 'flashcards', 'letters', 'write']);
  const rotations = [...initial.queue];
  for (let index = 0; index < initial.queue.length; index++) {
    const id = rotations.shift();
    await expect(card(page)).toHaveAttribute('data-word-id', id);
    await answer(page, words, false);
    rotations.push(id);
    await expect(page.locator('#word-practice')).toContainText(`Correct answer: ${words[id].word}`);
    await expect.poll(async () => (await snapshot(page)).queue).toEqual(rotations);
    await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
    if (index === 1) {
      await page.reload();
      await expect(card(page)).toHaveAttribute('data-word-id', rotations[0]);
      expect((await snapshot(page)).queue).toEqual(rotations);
    }
  }
  for (const [index, id] of rotations.entries()) {
    await expect(card(page)).toHaveAttribute('data-word-id', id);
    await answer(page, words, true, true);
    await expect.poll(async () => (await snapshot(page)).queue.length).toBe(3 - index);
  }
  await expect(page.locator('#practice-summary-title')).toBeVisible();
  await expect(page.getByRole('meter')).toHaveAttribute('aria-valuenow', '0');
  await page.reload();
  await expect(page.getByRole('meter')).toHaveAttribute('aria-valuenow', '0');
  await page.getByRole('button', { name: 'Review Mistakes' }).click();
  await expect(page.locator('.completion-row details[open]')).toHaveCount(4);
  await expect(page.locator('.completion-review')).toContainText('Your answer:');
  await expect(page.locator('.completion-review')).toContainText('Correct answer:');
  const xp = await page.evaluate(async () => (await (await import('/js/api.js')).getMyProgress()).xp);
  expect(xp).toBe(0);
  await page.getByRole('button', { name: 'Retry Mistakes', exact: true }).click();
  await expect(card(page)).toBeVisible();
  expect((await snapshot(page)).queue).toHaveLength(4);
  for (let remaining = 4; remaining > 0; remaining--) {
    await answer(page, words, true);
    await expect.poll(async () => (await snapshot(page)).queue.length).toBe(remaining - 1);
  }
  await page.reload();
  await page.setViewportSize({ width: 360, height: 780 });
  await expect(page.getByText('Perfect Score')).toBeVisible();
  await page.getByText('Mistakes from earlier rounds').click();
  await expect(page.locator('.completion-previous .completion-row')).toHaveCount(4);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Finish & Return' }).click();
  await expect(page.locator('#word-list-panel')).toBeVisible();
});

test('empty dictionary shows guidance and creates no review', async ({ page }) => {
  let reviews = 0;
  page.on('request', (request) => { if (request.url().endsWith('/review')) reviews++; });
  await open(page);
  await expect(page.locator('#word-practice')).toContainText('No words for this activity');
  expect(reviews).toBe(0);
});

test('one word and reload after a committed review produce a single saved attempt', async ({ page }) => {
  const words = await open(page, [['train', 'поїзд']]);
  const [id] = Object.keys(words);
  await expect(card(page)).toHaveAttribute('data-task-type', 'flashcards');
  let committed;
  const committedToDatabase = new Promise((resolve) => { committed = resolve; });
  let release;
  const responseReleased = new Promise((resolve) => { release = resolve; });
  const attempts = [];
  page.on('request', (request) => {
    if (request.url().endsWith('/review')) attempts.push(request.postDataJSON().attemptId);
  });
  await page.route(reviewUrl, async (route) => {
    const response = await route.fetch();
    committed(response.ok());
    await responseReleased;
    await route.fulfill({ response }).catch(() => {});
  }, { times: 1 });
  try {
    await card(page).getByRole('button', { name: 'Reveal translation', exact: true }).click();
    await card(page).getByRole('button', { name: /^I knew it/ }).dblclick();
    expect(await committedToDatabase).toBe(true);
    await page.reload();
    await expect(page.locator('#practice-summary-title')).toBeVisible();
    await expect(page.getByText('Perfect Score')).toBeVisible();
    expect(attempts).toHaveLength(2);
    expect(attempts[0]).toBe(attempts[1]);
    const history = await page.evaluate(async (wordId) => {
      const { apiFetch } = await import('/js/api.js');
      return apiFetch(`/vocabulary/${wordId}/reviews`);
    }, id);
    expect(history).toHaveLength(1);
  } finally {
    release();
  }
});
