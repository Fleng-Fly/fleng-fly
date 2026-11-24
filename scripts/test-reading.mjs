import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  answeredCount,
  canSubmit,
  openAttempt,
  paragraphs,
  pickAnswers,
  reportablePercent,
  requiredDwellSeconds,
  resultSummary,
  reviewOptionState,
} from '../frontend/js/reading-quiz.js';

const questions = [{ id: 'q1' }, { id: 'q2' }];

test('paragraphs split on blank lines and join wrapped lines', () => {
  assert.deepEqual(paragraphs('One\nstill one.\n\n\nTwo.\n  \nThree.'), [
    'One still one.',
    'Two.',
    'Three.',
  ]);
  assert.deepEqual(paragraphs(''), []);
  assert.deepEqual(paragraphs(null), []);
  assert.deepEqual(paragraphs('<b>x</b>'), ['<b>x</b>']); // markup stays text; the page uses textContent
});

test('answer counting ignores unknown questions and gates submit on completeness', () => {
  assert.equal(answeredCount(questions, { q1: 'a', zzz: 'b' }), 1);
  assert.deepEqual(pickAnswers(questions, { q1: 'a', zzz: 'b' }), { q1: 'a' });
  assert.equal(canSubmit(questions, { q1: 'a' }), false);
  assert.equal(canSubmit(questions, { q1: 'a', q2: 'b' }), true);
  assert.equal(canSubmit([], {}), false);
  assert.equal(canSubmit(questions, undefined), false);
});

test('a short article cannot reach 100% before the dwell time has passed', () => {
  assert.equal(requiredDwellSeconds(1), 15);
  assert.equal(requiredDwellSeconds(0), 5);
  assert.equal(requiredDwellSeconds(10), 30);
  assert.equal(reportablePercent(100, 3, 1), 99);
  assert.equal(reportablePercent(100, 15, 1), 100);
  assert.equal(reportablePercent(40, 0, 1), 40);
  assert.equal(reportablePercent(150, 99, 1), 100);
  assert.equal(reportablePercent(-5, 99, 1), 0);
});

test('result summary and review states come only from the submit response', () => {
  const result = {
    passed: true,
    scorePercent: 80,
    xpAwarded: 5,
    questions: [{ isCorrect: true }, { isCorrect: false }],
  };
  assert.deepEqual(resultSummary(result), {
    passed: true,
    percent: 80,
    xp: 5,
    showXp: true,
    alreadyEarned: false,
    correct: 1,
    total: 2,
  });
  const again = resultSummary({ ...result, xpAwarded: 0 });
  assert.equal(again.showXp, false);
  assert.equal(again.alreadyEarned, true);
  const failed = resultSummary({ ...result, passed: false, xpAwarded: 0 });
  assert.equal(failed.alreadyEarned, false);

  const item = { correctAnswerId: 'a', selectedAnswerId: 'b' };
  assert.equal(reviewOptionState(item, 'a'), 'correct');
  assert.equal(reviewOptionState(item, 'b'), 'wrong-chosen');
  assert.equal(reviewOptionState(item, 'c'), 'neutral');
  assert.equal(
    reviewOptionState({ correctAnswerId: 'a', selectedAnswerId: 'a' }, 'a'),
    'correct-chosen',
  );
  assert.equal(reviewOptionState({ correctAnswerId: 'a', selectedAnswerId: null }, 'a'), 'correct');
});

test('the open attempt is found in the history', () => {
  assert.equal(openAttempt([{ status: 'submitted' }]), null);
  assert.deepEqual(openAttempt([{ status: 'submitted' }, { id: 'x', status: 'in_progress' }]), {
    id: 'x',
    status: 'in_progress',
  });
});
