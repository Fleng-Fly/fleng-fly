// Pure helpers for the daily-goals card. Run: node --test scripts/test-daily-goals.mjs
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  goalMet, goalPercent, needsTimeZoneSync, parseGoalInputs,
} from '../frontend/js/daily-goals.js';

test('goalPercent is capped, rounded and safe for zero/missing values', () => {
  assert.equal(goalPercent(2, 3), 67);
  assert.equal(goalPercent(14, 20), 70);
  assert.equal(goalPercent(5, 3), 100);
  assert.equal(goalPercent(0, 3), 0);
  assert.equal(goalPercent(3, 0), 0);
  assert.equal(goalPercent(undefined, 3), 0);
});

test('goalMet needs a positive goal that was reached or exceeded', () => {
  assert.equal(goalMet({ goal: 3, done: 3 }), true);
  assert.equal(goalMet({ goal: 3, done: 4 }), true);
  assert.equal(goalMet({ goal: 3, done: 2 }), false);
  assert.equal(goalMet({ goal: 0, done: 0 }), false);
});

test('the time zone is synced only when known and different from the profile', () => {
  assert.equal(needsTimeZoneSync({ timezone: null }, 'Europe/Kyiv'), true);
  assert.equal(needsTimeZoneSync({ timezone: 'Europe/Kyiv' }, 'Europe/Kyiv'), false);
  assert.equal(needsTimeZoneSync({ timezone: 'UTC' }, 'Europe/Kyiv'), true);
  assert.equal(needsTimeZoneSync({ timezone: null }, null), false);
  assert.equal(needsTimeZoneSync(null, 'UTC'), false);
});

test('goal inputs are whole numbers inside the API ranges', () => {
  assert.deepEqual(parseGoalInputs('3', '20'), { value: { dailyLessonsGoal: 3, dailyWordsGoal: 20 } });
  assert.deepEqual(parseGoalInputs(' 10 ', '100').value, { dailyLessonsGoal: 10, dailyWordsGoal: 100 });
  for (const [lessons, words] of [['0', '10'], ['11', '10'], ['1', '0'], ['1', '101'], ['1.5', '10'], ['', '10'], ['a', '10'], ['-1', '10'], ['1', null]]) {
    assert.deepEqual(parseGoalInputs(lessons, words), { error: 'range' }, `${lessons}/${words}`);
  }
});
