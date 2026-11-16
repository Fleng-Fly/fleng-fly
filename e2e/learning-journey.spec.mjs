// Core student journey in a real browser against the real backend and a temporary SQLite file.
// See docs/qa/e2e.md. Every test registers its own learner, so tests are independent of each
// other and of execution order. Nothing here mocks or intercepts an API response.
import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

const PASSWORD = 'e2e-correct-horse-battery';
// Published seed course used for the journey (backend/app/db/seed.py).
const COURSE = { slug: 'english-foundations', title: 'English Foundations' };
const LESSON = { title: 'Greetings and introductions', question: 'Complete the greeting' };

const PRIVATE_PAGES = [
  '/dashboard.html',
  '/courses.html',
  `/course.html?slug=${COURSE.slug}`,
  '/lesson.html?slug=greetings-and-introductions',
  '/settings.html',
  '/vocabulary.html',
  '/leaderboard.html',
  '/team.html',
];

function newLearner() {
  return {
    name: `E2E ${randomUUID().slice(0, 8)}`,
    // example.com is accepted by the backend's email validator; special-use TLDs such as .test are not.
    email: `e2e-${randomUUID()}@example.com`,
    password: PASSWORD,
  };
}

async function registerThroughUi(page, learner) {
  await page.goto('/register.html');
  await page.getByLabel('Display name').fill(learner.name);
  await page.getByLabel('Email').fill(learner.email);
  await page.getByLabel('Password').fill(learner.password);
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page).toHaveURL(/\/dashboard\.html$/);
  await expect(page.locator('#dashboard-level')).toContainText('XP');
}

async function logOutFromWorkspace(page) {
  await page.locator('#profile-toggle').click();
  await page.locator('#profile-logout').click();
  await expect(page).toHaveURL(/\/index\.html$/);
}

// Reads server state through the page's own authenticated API client (no mocking).
const myProgress = (page) =>
  page.evaluate(async () => (await import('/js/api.js')).getMyProgress());

async function startFirstLesson(page) {
  await page.goto('/courses.html');
  const card = page.locator('.catalog-card', { hasText: COURSE.title });
  await card.getByRole('link', { name: /Start Course|Continue Course|Review Course/ }).click();
  await expect(page).toHaveURL(new RegExp(`/course\\.html\\?slug=${COURSE.slug}$`));
  await page
    .getByRole('link', { name: new RegExp(`(Start|Continue|Review) Lesson: ${LESSON.title}`) })
    .click();
  await expect(page).toHaveURL(/\/lesson\.html\?slug=greetings-and-introductions$/);
  await expect(page.locator('#lesson-title')).toHaveText(LESSON.title);
}

async function openPractice(page) {
  await page.locator('#tab-practice').click();
  await expect(page.locator('#panel-practice')).toBeVisible();
}

async function openQuestion(page, number) {
  await page.getByRole('button', { name: `Open question ${number}`, exact: true }).click();
  await expect(page.locator('.lesson-question-meta .lesson-chip')).toContainText(
    `Question ${number} /`,
  );
}

async function answerChoice(page, optionText) {
  await page.getByLabel(optionText, { exact: true }).check();
  await page.getByRole('button', { name: 'Check answer' }).click();
}

test.describe('account', () => {
  test('registers through the UI, lands on the dashboard and stays signed in after reload', async ({
    page,
  }) => {
    const learner = newLearner();
    await registerThroughUi(page, learner);
    await expect(page.locator('#dashboard-level')).toContainText('0 XP');
    await page.reload();
    await expect(page).toHaveURL(/\/dashboard\.html$/);
    await expect(page.locator('#profile-short-name')).not.toHaveText('Account');
  });

  test('rejects registering the same email twice', async ({ page, browser, baseURL }) => {
    const learner = newLearner();
    await registerThroughUi(page, learner);
    const other = await browser.newContext({ baseURL });
    const second = await other.newPage();
    await second.goto('/register.html');
    await second.getByLabel('Display name').fill('Someone else');
    await second.getByLabel('Email').fill(learner.email);
    await second.getByLabel('Password').fill(learner.password);
    await second.getByRole('button', { name: 'Create account' }).click();
    await expect(second.locator('#form-error')).toBeVisible();
    await expect(second).toHaveURL(/\/register\.html$/);
    await other.close();
  });

  test('logs out and logs back in; a wrong password is refused', async ({ page }) => {
    const learner = newLearner();
    await registerThroughUi(page, learner);
    await logOutFromWorkspace(page);

    await page.goto('/login.html');
    await page.getByLabel('Email').fill(learner.email);
    await page.getByLabel('Password').fill('definitely-the-wrong-password');
    await page.getByRole('button', { name: 'Log in' }).click();
    await expect(page.locator('#form-error')).toBeVisible();
    await expect(page).toHaveURL(/\/login\.html$/);

    await page.getByLabel('Password').fill(learner.password);
    await page.getByRole('button', { name: 'Log in' }).click();
    await expect(page).toHaveURL(/\/dashboard\.html$/);
    await expect(page.locator('#dashboard-level')).toContainText('XP');
  });
});

test.describe('catalog and lesson', () => {
  test('lists the published courses, filters them, and opens a course and its first lesson', async ({
    page,
  }) => {
    await registerThroughUi(page, newLearner());
    await page.goto('/courses.html');

    // Cards must match what the real API publishes.
    const published = await page.evaluate(async () => (await import('/js/api.js')).listCourses());
    expect(published.length).toBeGreaterThan(0);
    await expect(page.locator('.catalog-card')).toHaveCount(published.length);
    await expect(page.locator('#course-results-count')).toHaveText(
      `${published.length} ${published.length === 1 ? 'course' : 'courses'}`,
    );
    for (const course of published) {
      await expect(page.locator('.catalog-card', { hasText: course.title })).toBeVisible();
    }

    await page.locator('#course-filters button[data-level="A1"]').click();
    const a1 = published.filter((course) => course.level === 'A1');
    await expect(page.locator('.catalog-card')).toHaveCount(a1.length);
    await page.locator('#course-filters button[data-level="All"]').click();
    await page.locator('#course-search').fill('no-such-course-anywhere');
    await expect(page.getByText('No courses found')).toBeVisible();
    await page.locator('#course-search').fill('');

    await startFirstLesson(page);
    await expect(page.locator('#lesson-activity-count')).toHaveText('0 / 3 activities');
    await expect(page.locator('#lesson-xp')).toHaveText('0 XP earned');
  });
});

test.describe('exercise, progress and XP', () => {
  test('a correct answer awards XP once, is saved across reloads, and is not paid twice', async ({
    page,
  }) => {
    await registerThroughUi(page, newLearner());
    await startFirstLesson(page);
    await openPractice(page);
    await expect(page.locator('.lesson-question h2')).toContainText(LESSON.question);

    await answerChoice(page, 'Hello');
    await expect(page.locator('#lesson-last-answer .lesson-feedback')).toContainText(
      'Correct · +1 XP',
    );
    await expect(page.locator('#lesson-activity-count')).toHaveText('1 / 3 activities');
    await expect(page.locator('#lesson-xp')).toHaveText('1 XP earned');
    expect((await myProgress(page)).xp).toBe(1);

    // Saved on the server: a full reload restores progress and the learner's answer.
    await page.reload();
    await expect(page.locator('#lesson-activity-count')).toHaveText('1 / 3 activities');
    await expect(page.locator('#lesson-xp')).toHaveText('1 XP earned');
    await openPractice(page);
    await openQuestion(page, 1);
    const saved = page.locator('.lesson-question .lesson-feedback');
    await expect(saved).toContainText('Completed');
    await expect(saved).toContainText('Your latest answer: Hello');

    // Answering the same exercise correctly again must not pay XP again.
    await answerChoice(page, 'Hello');
    await expect(page.locator('#lesson-last-answer .lesson-feedback strong').first()).toHaveText(
      'Correct',
    );
    await expect(page.locator('#lesson-xp')).toHaveText('1 XP earned');
    expect((await myProgress(page)).xp).toBe(1);

    // The same total is visible on the dashboard and the course page.
    await page.goto('/dashboard.html');
    await expect(page.locator('#dashboard-level')).toContainText('1 XP');
    await page.goto(`/course.html?slug=${COURSE.slug}`);
    await expect(page.locator('.catalog-lesson').first()).toContainText('In Progress');
  });

  test('a wrong answer earns nothing and the exercise can still be completed afterwards', async ({
    page,
  }) => {
    await registerThroughUi(page, newLearner());
    await startFirstLesson(page);
    await openPractice(page);

    await answerChoice(page, 'Goodbye');
    await expect(page.locator('#lesson-xp')).toHaveText('0 XP earned');
    await expect(page.locator('#lesson-activity-count')).toHaveText('0 / 3 activities');
    expect((await myProgress(page)).xp).toBe(0);

    await openQuestion(page, 1);
    await answerChoice(page, 'Hello');
    await expect(page.locator('#lesson-xp')).toHaveText('1 XP earned');
    expect((await myProgress(page)).xp).toBe(1);
  });

  test('progress belongs to the learner who earned it', async ({ page, browser, baseURL }) => {
    await registerThroughUi(page, newLearner());
    await startFirstLesson(page);
    await openPractice(page);
    await answerChoice(page, 'Hello');
    await expect(page.locator('#lesson-xp')).toHaveText('1 XP earned');

    const other = await browser.newContext({ baseURL });
    const otherPage = await other.newPage();
    await registerThroughUi(otherPage, newLearner());
    expect((await myProgress(otherPage)).xp).toBe(0);
    await other.close();
  });
});

test.describe('logout and private pages', () => {
  test('after logging out every private page redirects to the login page', async ({ page }) => {
    await registerThroughUi(page, newLearner());
    await page.goto('/courses.html');
    await expect(page.locator('.catalog-card').first()).toBeVisible();
    await page.locator('#profile-toggle').click();
    await page.locator('#profile-logout').click();
    await expect(page).toHaveURL(/\/index\.html$/);

    // The server no longer knows this session, not just the page.
    expect((await page.request.get('/api/v1/users/me')).status()).toBe(401);
    expect((await page.request.post('/api/v1/auth/refresh')).status()).toBe(401);

    for (const path of PRIVATE_PAGES) {
      await page.goto(path);
      await expect(page, path).toHaveURL(/\/login\.html$/);
    }
  });

  test('an anonymous visitor cannot open private pages or read private API data', async ({
    browser,
    baseURL,
  }) => {
    const context = await browser.newContext({ baseURL });
    const page = await context.newPage();
    for (const path of PRIVATE_PAGES) {
      await page.goto(path);
      await expect(page, path).toHaveURL(/\/login\.html$/);
    }
    for (const path of ['/api/v1/users/me', '/api/v1/progress/me']) {
      expect((await context.request.get(path)).status(), path).toBe(401);
    }
    await context.close();
  });
});
