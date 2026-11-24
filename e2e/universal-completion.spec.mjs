import { randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const content = (file) => JSON.parse(readFileSync(new URL(`../backend/app/db/content/${file}.json`, import.meta.url), 'utf8'));
const { courses } = content('curriculum-a0-b2');
const practice = content('curriculum-practice-supplement').lessons;
const words = content('curriculum-vocabulary-supplement').lessons;

for (const [index, course] of courses.entries()) {
  const isFinalLesson = index % 2 === 1 || course.level === 'B2';
  const lesson = isFinalLesson ? course.lessons.at(-1) : course.lessons[0];
  test(`${course.level} uses the shared result for ${lesson.slug}`, async ({ page }) => {
    await page.setViewportSize(index % 2 ? { width: 360, height: 780 } : { width: 1280, height: 850 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/register.html');
    await page.locator('#displayName').fill('Universal completion learner');
    await page.locator('#email').fill(`completion-${randomUUID()}@example.com`);
    await page.locator('#password').fill('completion-test-password');
    await page.locator('#submit-button').click();
    await expect(page).toHaveURL(/dashboard\.html$/);

    await page.goto(`/lesson.html?slug=${lesson.slug}&tab=practice`);
    await expect(page.locator('.lesson-question')).toBeVisible();
    await expect(page.locator('.test-completion')).toHaveCount(0);
    const fixture = {
      base: lesson.exercises,
      practice: practice[lesson.slug],
      vocabulary: words[lesson.slug],
    };
    const last = await page.evaluate(async ({ slug, fixture, makeMistake }) => {
      const { getLesson, submitAnswer } = await import('/js/api.js');
      const current = await getLesson(slug);
      const lastExercise = current.exercises.at(-1);
      const answerFor = (exercise) => {
        const base = fixture.base.find((item) => item.slug === exercise.slug);
        if (base) return base.correct_option_id;
        const position = Number(exercise.slug.split('-').at(-1)) - 1;
        if (exercise.slug.includes('-vocabulary-')) {
          const word = fixture.vocabulary[position];
          return exercise.options.find((option) => option.text === (position % 2 ? word.word : word.translation)).id;
        }
        const item = fixture.practice[position];
        return item.accepted_answers?.[0] ?? item.model_answer;
      };
      if (makeMistake) {
        const first = current.exercises[0];
        const wrong = first.options.find((option) => option.id !== answerFor(first));
        await submitAnswer(slug, { exerciseId: first.id, answer: wrong.id, expectedAttempts: 0 });
      }
      for (const [position, exercise] of current.exercises.slice(0, -1).entries()) {
        const saved = await submitAnswer(slug, {
          exerciseId: exercise.id,
          answer: answerFor(exercise),
          expectedAttempts: Number(makeMistake && position === 0),
          ...(exercise.type === 'self_check' ? { selfAssessment: 'correct' } : {}),
        });
        if (!saved.completed || saved.lesson.completed) throw new Error(`Unexpected progress for ${exercise.slug}`);
      }
      return { answer: answerFor(lastExercise), total: current.exercises.length };
    }, { slug: lesson.slug, fixture, makeMistake: index % 2 === 1 });

    await page.reload();
    await expect(page.locator('#lesson-completed')).toBeHidden();
    await page.locator(`.lesson-question input[value="${last.answer}"]`).check();
    const result = page.locator('.test-completion');
    await expect(result.getByRole('heading', { level: 2 })).toBeFocused();
    await expect(result.locator('.completion-subtitle')).toHaveText(lesson.title);
    await expect(result.locator('.completion-course')).toHaveText(course.title);
    await expect(result.locator('.completion-level')).toHaveText(`Level ${course.level}`);
    await expect(result.locator('.completion-row')).toHaveCount(last.total);
    await expect(result.getByText('Perfect Score')).toHaveCount(index % 2 ? 0 : 1);
    await expect(result.getByRole('link', { name: 'Next Lesson' })).toHaveCount(isFinalLesson ? 0 : 1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

    const readProgress = () => page.evaluate(async (slug) =>
      (await import('/js/api.js')).getLessonProgress(slug), lesson.slug);
    const saved = await readProgress();
    expect(saved.xpEarned).toBeGreaterThan(0);
    await page.goto(`/course.html?slug=${course.slug}`);
    await page.getByRole('link', { name: `View Results: ${lesson.title}` }).click();
    await expect(result.getByRole('heading', { level: 2 })).toBeFocused();
    expect(await readProgress()).toEqual(saved);
    await result.getByRole('link', { name: 'Back to Courses' }).click();
    await expect(page).toHaveURL(/courses\.html$/);
  });
}
