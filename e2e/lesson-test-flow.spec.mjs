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
const jump = (page, number) => page.getByRole('button', { name: `Open question ${number}`, exact: true }).click();

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

test('wrong answers rotate in FIFO order, including repeat failures, and survive reload', async ({ page }) => {
  await open(page);
  const [first, second, third] = (await progress(page)).pendingExerciseIds;
  await jump(page, 2);
  await letter(page, 'a', 0);
  await letter(page, 'o', 1);
  await question(page, 1);
  await choice(page, 'have');
  await question(page, 3);
  await expect(page.locator('#lesson-last-answer')).toContainText('Incorrect');
  await textAnswer(page, 'never');
  await question(page, 2);
  const halfway = await progress(page);
  expect(halfway.pendingExerciseIds).toEqual([second, first]);
  expect(halfway.exercisesCompleted).toBe(1);
  expect(halfway.xpEarned).toBeGreaterThan(0);
  expect(halfway.pendingExerciseIds).not.toContain(third);

  await jump(page, 1);
  await page.reload();
  await question(page, 1); // The cursor is intentionally away from the queue head.
  expect(await progress(page)).toEqual(halfway);
  await jump(page, 2);
  await letter(page, 'a', 0);
  await letter(page, 'o', 1);
  await question(page, 1);
  expect((await progress(page)).pendingExerciseIds).toEqual([first, second]);
  await page.reload();
  await question(page, 1);
  await choice(page, 'has');
  await question(page, 2);
  const beforeLast = await progress(page);
  expect(beforeLast.completed).toBe(false);
  expect(beforeLast.pendingExerciseIds).toEqual([second]);

  await jump(page, 1);
  await choice(page, 'has');
  await question(page, 2);
  expect((await progress(page)).xpEarned).toBe(beforeLast.xpEarned);
  await bank(page, 'a').dragTo(page.locator('#lesson-title'));
  await expect(bank(page, 'a')).toBeVisible();
  await letter(page, 'e', 0);
  expect((await progress(page)).exercises[1].attempts).toBe(2);
  await slots(page).first().dragTo(page.locator('#lesson-title'));
  await expect(slots(page).first()).toHaveText('e');
  await letter(page, 'e', 1);
  await expect.poll(async () => (await progress(page)).completed).toBe(true);
  const finished = await progress(page);
  await expect(page.locator('#lesson-completion-title')).toBeVisible();
  await expect(page.getByRole('meter')).toHaveAttribute('aria-valuenow', '33');
  await page.getByRole('button', { name: 'Review Mistakes' }).click();
  await expect(page.locator('.completion-row details[open]')).toHaveCount(2);
  await expect(page.locator('.completion-review')).toContainText('Your answer:');
  await expect(page.locator('.completion-review')).toContainText('Correct answer:');
  await expect(page.getByRole('link', { name: 'Continue Learning' })).toBeVisible();
  expect(finished.pendingExerciseIds).toEqual([]);
  expect(finished.exercisesCompleted).toBe(3);
  await page.reload();
  await question(page, 1);
  expect(await progress(page)).toEqual(finished);
});

test('self-assessment reveals a model only after confirmation without grading the preview', async ({ page }) => {
  await open(page, GREETINGS);
  await jump(page, 3);
  const before = await progress(page, GREETINGS);
  const answer = card(page).locator('textarea');
  const model = card(page).locator('.lesson-model-answer');
  const confirm = card(page).getByRole('button', { name: 'Confirm answer and show example' });
  await expect(model).toHaveCount(0);
  await expect(card(page).getByRole('button', { name: 'I got it right' })).toHaveCount(0);
  await confirm.click();
  await expect(card(page).locator('.lesson-feedback')).toContainText('Write');
  await answer.fill('Good morning!');
  const previewRequests = [];
  page.on('request', (request) => {
    if (request.url().endsWith('/self-check/preview')) previewRequests.push(request);
  });
  await confirm.dblclick();
  await expect(model).toContainText('Good morning!');
  await expect(answer).toHaveAttribute('readonly', '');
  expect(previewRequests).toHaveLength(1);
  expect(await progress(page, GREETINGS)).toEqual(before);

  await card(page).getByRole('button', { name: 'I need practice' }).click();
  await question(page, 1);
  const failed = await progress(page, GREETINGS);
  const id = before.exercises[2].exerciseId;
  expect(failed.pendingExerciseIds.at(-1)).toBe(id);
  expect(failed.exercises[2]).toMatchObject({ attempts: 1, completed: false });
  await jump(page, 3);
  await expect(model).toHaveCount(0);
  await answer.fill('Good morning!');
  await confirm.click();
  await expect(model).toBeVisible();
  await card(page).getByRole('button', { name: 'I got it right' }).dblclick();
  await question(page, 1);
  const passed = await progress(page, GREETINGS);
  expect(passed.exercises[2]).toMatchObject({ attempts: 2, completed: true });
  expect(passed.pendingExerciseIds).not.toContain(id);
  expect(passed.xpEarned).toBeGreaterThan(0);
});

test('text pause and Enter each submit once, including Enter during a pending check', async ({ page }) => {
  await open(page);
  await jump(page, 3);
  const input = card(page).locator('input.lesson-answer');
  const submitTimes = [];
  page.on('request', (request) => {
    if (request.url().endsWith('/submit')) submitTimes.push(Date.now());
  });
  const start = Date.now();
  await input.fill('always');
  await expect.poll(() => submitTimes.length).toBe(1);
  expect(submitTimes[0] - start).toBeGreaterThanOrEqual(1450);
  await question(page, 1);
  await jump(page, 3);
  await page.route(answerRoute, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    await route.continue();
  });
  await textAnswer(page, 'never');
  await page.keyboard.press('Enter');
  await question(page, 1);
  await expect.poll(async () => (await progress(page)).exercises[2].attempts).toBe(2);
  await page.waitForTimeout(1600); // The canceled text timer would fire within this interval.
  expect(submitTimes).toHaveLength(2);
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

test('reload before a committed response arrives recovers the new queue and current exercise', async ({ page }) => {
  await open(page);
  await jump(page, 2);
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
    await question(page, 1);
    const restored = await progress(page);
    expect(restored.exercises[1]).toMatchObject({ attempts: 1, completed: false });
    expect(restored.pendingExerciseIds.at(-1)).toBe(restored.exercises[1].exerciseId);
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

test('a submission that commits after the replacement page loads updates the restored queue', async ({ page }) => {
  await open(page);
  await jump(page, 2);
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
  await question(page, 1);
  expect((await progress(page)).exercises[1].attempts).toBe(1);
});
