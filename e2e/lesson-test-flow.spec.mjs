import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

const PRACTICE = 'present-perfect-practice';
const GREETINGS = 'greetings-and-introductions';
const answerRoute = '**/api/v1/lessons/*/submit';
const card = (page) => page.locator('.lesson-question');
const bank = (page, letter) => card(page).locator('.lesson-tile-bank')
  .getByRole('button', { name: letter, exact: true }).first();
const slots = (page) => card(page).locator('.lesson-tile-slot');
const choice = (page, label) => card(page).getByRole('radio', { name: new RegExp(label) }).click();
const question = (page, number) => expect(card(page).locator('.lesson-question-meta'))
  .toContainText(`Question ${number} /`, { timeout: 10000 });
const skip = (page) => card(page).getByRole('button', { name: 'Skip', exact: true }).click();
const metric = (page, name) => page.locator(`[data-metric="${name}"] dd`);

async function register(page) {
  await page.goto('/register.html');
  await page.locator('#displayName').fill('Lesson flow learner');
  await page.locator('#email').fill(`flow-${randomUUID()}@example.com`);
  await page.locator('#password').fill('lesson-flow-test-password');
  await page.locator('#submit-button').click();
  await expect(page).toHaveURL(/dashboard\.html$/);
  await expect(page.locator('#dashboard-level')).toContainText('XP');
}

async function open(page, slug = PRACTICE) {
  await page.goto(`/lesson.html?slug=${slug}&tab=practice`);
  await question(page, 1);
}

function progress(page, slug = PRACTICE) {
  return page.evaluate(async (id) => (await import('/js/api.js')).getLessonProgress(id), slug);
}

async function letter(page, value, index) {
  await bank(page, value).click();
  await slots(page).nth(index).click();
}

async function textAnswer(page, answer) {
  const input = card(page).locator('input.lesson-answer');
  await input.fill(answer);
  await input.press('Enter');
}

test.beforeEach(async ({ page }) => {
  await register(page);
});

for (const scenario of [
  { name: 'all correct', outcomes: ['correct', 'correct', 'correct'] },
  { name: 'all wrong', outcomes: ['incorrect', 'incorrect', 'incorrect'] },
  { name: 'all skipped', outcomes: ['skipped', 'skipped', 'skipped'] },
  { name: 'mixed with a final skip', outcomes: ['incorrect', 'correct', 'skipped'] },
]) {
  test(`one pass: ${scenario.name}`, async ({ page }) => {
    await open(page);
    for (const [index, outcome] of scenario.outcomes.entries()) {
      await question(page, index + 1);
      if (outcome === 'skipped') await skip(page);
      else if (index === 0) await choice(page, outcome === 'correct' ? 'has' : 'have');
      else if (index === 1) {
        const letters = outcome === 'correct' ? ['e', 'e'] : ['a', 'o'];
        await letter(page, letters[0], 0);
        await letter(page, letters[1], 1);
      } else await textAnswer(page, outcome === 'correct' ? 'never' : 'always');
      if (index === 0) {
        await question(page, 2);
        await page.reload();
        await question(page, 2);
      }
    }
    await expect(page.locator('#lesson-completion-title')).toBeVisible();
    await expect(card(page)).toHaveCount(0);
    for (const outcome of ['correct', 'incorrect', 'skipped']) {
      await expect(metric(page, outcome)).toHaveText(String(scenario.outcomes.filter((value) => value === outcome).length));
    }
    const saved = await progress(page);
    expect(saved.pendingExerciseIds).toEqual([]);
    expect(saved.exercises.map((record) => record.firstOutcome)).toEqual(scenario.outcomes);
    expect(saved.exercises.every((record) => record.attempts === 1)).toBe(true);
    const passed = scenario.outcomes.every((value) => value === 'correct');
    expect(saved.completed).toBe(passed);
    await expect(page.getByRole('link', { name: /^(Next Lesson|Continue Learning)$/ })).toHaveCount(Number(passed));
    await page.reload();
    await expect(page.locator('#lesson-completion-title')).toBeVisible();
    expect(await progress(page)).toEqual(saved);
    if (scenario.name.startsWith('mixed')) {
      await page.getByRole('button', { name: 'Review Mistakes' }).click();
      await expect(page.locator('.completion-row details[open]')).toHaveCount(1);
      await page.getByRole('button', { name: 'Retry Mistakes' }).click();
      await question(page, 1);
      await choice(page, 'has');
      await question(page, 3);
      await page.reload();
      await question(page, 3);
      await textAnswer(page, 'never');
      await expect(page.locator('#lesson-completion-title')).toBeVisible();
      await expect(metric(page, 'incorrect')).toHaveText('1');
      await expect(metric(page, 'skipped')).toHaveText('1');
      expect((await progress(page)).completed).toBe(true);
    }
  });
}

test('self-assessment reveals a model without grading until the learner confirms', async ({ page }) => {
  await open(page, GREETINGS);
  await skip(page);
  await question(page, 2);
  await skip(page);
  await question(page, 3);
  const before = await progress(page, GREETINGS);
  const answer = card(page).locator('textarea');
  const model = card(page).locator('.lesson-model-answer');
  const confirm = card(page).getByRole('button', { name: 'Confirm answer and show example' });
  await expect(model).toHaveCount(0);
  await confirm.click();
  await expect(card(page).locator('.lesson-feedback')).toContainText('Write');
  await answer.fill('Good morning!');
  await confirm.click();
  await expect(model).toContainText('Good morning!');
  expect(await progress(page, GREETINGS)).toEqual(before);
  await card(page).getByRole('button', { name: 'I need practice' }).click();
  await question(page, 4);
  expect((await progress(page, GREETINGS)).exercises[2]).toMatchObject({
    attempts: 1, completed: false, firstOutcome: 'incorrect',
  });
});

test('text auto-check and Enter produce only one submission', async ({ page }) => {
  await open(page);
  await skip(page);
  await question(page, 2);
  await skip(page);
  await question(page, 3);
  const input = card(page).locator('input.lesson-answer');
  let submits = 0;
  page.on('request', (request) => { if (request.url().endsWith('/submit')) submits++; });
  await input.fill('always');
  await expect(page.locator('#lesson-completion-title')).toBeVisible();
  await page.keyboard.press('Enter');
  expect(submits).toBe(1);
});

test('network failure permits retry and a lost committed response is reconciled', async ({ page }) => {
  await open(page);
  await page.route(answerRoute, (route) => route.abort(), { times: 1 });
  await choice(page, 'has');
  await expect(card(page).locator('.lesson-feedback')).toHaveClass(/is-error/);
  expect((await progress(page)).exercises[0].attempts).toBe(0);
  await page.route(answerRoute, async (route) => {
    expect((await route.fetch()).ok()).toBe(true);
    await route.abort();
  }, { times: 1 });
  await card(page).getByRole('button', { name: 'Retry checking' }).click();
  await question(page, 2);
  expect((await progress(page)).exercises[0]).toMatchObject({ attempts: 1, completed: true });
});

test('reload before a committed response arrives restores the next unvisited exercise', async ({ page }) => {
  await open(page);
  await skip(page);
  await question(page, 2);
  let committed;
  const serverCommitted = new Promise((resolve) => { committed = resolve; });
  let release;
  const responseReleased = new Promise((resolve) => { release = resolve; });
  await page.route(answerRoute, async (route) => {
    const response = await route.fetch();
    committed(response.ok());
    await responseReleased;
    await route.fulfill({ response }).catch(() => {}); // Reload has detached the old request.
  }, { times: 1 });
  try {
    await letter(page, 'a', 0);
    await letter(page, 'o', 1);
    expect(await serverCommitted).toBe(true);
    await page.reload();
    await question(page, 3);
    const restored = await progress(page);
    expect(restored.exercises[1]).toMatchObject({ attempts: 1, completed: false });
    expect(restored.pendingExerciseIds).toEqual([restored.exercises[2].exerciseId]);
  } finally {
    release();
  }
});

test('simultaneous requests using the same attempt count produce one saved attempt', async ({ page }) => {
  await open(page);
  const [exerciseId] = (await progress(page)).pendingExerciseIds;
  const outcomes = await page.evaluate(async ({ slug, exerciseId }) => {
    const { submitAnswer } = await import('/js/api.js');
    const payload = { exerciseId, answer: 'b', expectedAttempts: 0 };
    return Promise.all([1, 2].map(async () => {
      try {
        return (await submitAnswer(slug, payload)).xpAwarded;
      } catch (error) {
        return error.status;
      }
    }));
  }, { slug: PRACTICE, exerciseId });
  expect(outcomes.sort((a, b) => a - b)).toEqual([1, 409]);
  expect((await progress(page)).exercises[0]).toMatchObject({ attempts: 1, completed: true });
});

test('a submission that commits after the replacement page loads advances the restored pass', async ({ page }) => {
  await open(page);
  await skip(page);
  await question(page, 2);
  const dispatched = page.waitForRequest(answerRoute);
  await page.route(answerRoute, () => {}, { times: 1 });
  await letter(page, 'a', 0);
  await letter(page, 'o', 1);
  const request = await dispatched;
  const authorization = await request.headerValue('authorization');
  await page.reload();
  await question(page, 2);
  expect((await progress(page)).exercises[1].attempts).toBe(0);

  // The request has left the old page but reaches FastAPI after the reload's first GET.
  const late = await page.request.post(request.url(), {
    data: request.postDataJSON(), headers: { authorization },
  });
  expect(late.ok()).toBe(true);
  await question(page, 3);
  expect((await progress(page)).exercises[1].attempts).toBe(1);
});
