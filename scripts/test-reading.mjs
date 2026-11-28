import assert from 'node:assert/strict';
import { test } from 'node:test';
import { READINGS, READING_LEVELS } from '../frontend/js/reading-content.js';
import { gradeReading, restoreReading } from '../frontend/js/reading-state.js';

test('30 original texts, six per published level, with 300 valid questions and unique IDs', () => {
  assert.equal(READINGS.length, 30);
  assert.equal(new Set(READINGS.map(r => r.id)).size, 30);
  for (const level of READING_LEVELS) assert.equal(READINGS.filter(r => r.level === level).length, 6);
  for (const reading of READINGS) {
    assert.ok(reading.title && reading.titleUk && reading.paragraphs.length);
    assert.equal(reading.questions.length, 10);
    assert.equal(reading.questions.filter(q => q.type === 'true_false').length, 4);
    assert.equal(reading.questions.filter(q => q.type === 'choice').length, 6);
    assert.deepEqual(reading.questions.filter(q => q.type === 'true_false').map(q => q.answer).sort(), [0, 0, 1, 1]);
    assert.ok(reading.paragraphs.length >= 6);
    const size = reading.paragraphs.join(" ").split(/\s+/).length;
    assert.ok(size >= { A0: 300, A1: 650, A2: 1000, B1: 1400, B2: 1800 }[reading.level]);
    for (const q of reading.questions.slice(5)) assert.ok(reading.paragraphs.join(" ").toLowerCase().includes(q.evidence.toLowerCase()));
    for (const q of reading.questions) {
      assert.ok(q.prompt && q.evidence);
      assert.equal(new Set(q.options).size, q.options.length);
      assert.ok(Number.isInteger(q.answer) && q.answer >= 0 && q.answer < q.options.length);
    }
    assert.deepEqual(gradeReading(reading, reading.questions.map(q => q.answer)), { complete: true, score: 10, passed: true, total: 10 });
  }
});
test('pass threshold, incomplete and failed tests', () => {
  const r = READINGS[0];
  const correct = r.questions.map(q => q.answer);
  const wrong = r.questions.map(q => (q.answer + 1) % q.options.length);
  assert.equal(gradeReading(r, wrong).score, 0);
  assert.equal(gradeReading(r, [...wrong.slice(0, 2), ...correct.slice(2)]).passed, true);
  assert.equal(gradeReading(r, [...wrong.slice(0, 3), ...correct.slice(3)]).passed, false);
  assert.equal(gradeReading(r, [null, ...correct.slice(1)]).passed, false);
  assert.equal(gradeReading(r, []).complete, false);
});
test('restore drafts and results, reject invalid answers and preserve best score', () => {
  const r = READINGS[0];
  assert.deepEqual(restoreReading(r, { answers: [0, -1, 99, '1', null], finished: true, best: 11 }), { answers: [0,...Array(9).fill(null)], finished: false, best: null });
  assert.deepEqual(restoreReading(r, { answers: [0], best: 5 }), { answers: [0,...Array(9).fill(null)], finished: false, best: 5 });
  const answers = r.questions.map(q => q.answer);
  assert.deepEqual(restoreReading(r, { answers, finished: true, best: 2 }), { answers, finished: true, best: 10 });
});
