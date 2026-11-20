// Pure-function checks for the next-course recommendation.
// Run: node --test scripts/test-next-course.mjs
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { placementLevelFrom, recommendNextCourse } from '../frontend/js/next-course.js';

const LEVELS = ['A0', 'A1', 'A2', 'B1', 'B2'];
const courses = LEVELS.map((level) => ({
  id: level, slug: `fleng-${level.toLowerCase()}`, title: level, description: '', level, lessonCount: 10,
}));
// state: map level -> 'done' | 'started' (anything else = untouched)
const progress = (state = {}) =>
  LEVELS.map((level) => ({
    courseId: level,
    lessonsTotal: 10,
    lessonsStarted: state[level] ? 10 : 0,
    lessonsCompleted: state[level] === 'done' ? 10 : state[level] === 'started' ? 3 : 0,
  }));
const slug = (result) => result.course?.slug;

test('A0 completed recommends A1, and the chain continues in order', () => {
  assert.equal(slug(recommendNextCourse({ courses, progress: progress({ A0: 'done' }) })), 'fleng-a1');
  assert.equal(slug(recommendNextCourse({ courses, progress: progress({ A0: 'done', A1: 'done' }) })), 'fleng-a2');
  assert.equal(
    slug(recommendNextCourse({ courses, progress: progress({ A0: 'done', A1: 'done', A2: 'done', B1: 'done' }) })),
    'fleng-b2',
  );
});

test('never recommends a completed course, even with a stale placement level', () => {
  const result = recommendNextCourse({
    courses, progress: progress({ A0: 'done', A1: 'done' }), placementLevel: 'A1',
  });
  assert.equal(slug(result), 'fleng-a2');
});

test('placement level skips lower courses the learner has not taken', () => {
  assert.equal(slug(recommendNextCourse({ courses, progress: progress(), placementLevel: 'B1' })), 'fleng-b1');
  assert.equal(
    slug(recommendNextCourse({ courses, progress: progress({ A0: 'done' }), placementLevel: 'A2' })),
    'fleng-a2',
  );
});

test('afterSlug only offers courses after the finished one and respects placement', () => {
  const state = { A0: 'done' };
  assert.equal(slug(recommendNextCourse({ courses, progress: progress(state), afterSlug: 'fleng-a0' })), 'fleng-a1');
  assert.equal(
    slug(recommendNextCourse({ courses, progress: progress(state), afterSlug: 'fleng-a0', placementLevel: 'B1' })),
    'fleng-b1',
  );
  assert.equal(recommendNextCourse({ courses, progress: progress(state), afterSlug: 'missing' }).status, 'none');
});

test('a course already in progress is Continue, not next', () => {
  const result = recommendNextCourse({ courses, progress: progress({ A0: 'done', A1: 'started' }) });
  assert.equal(slug(result), 'fleng-a2');
  assert.equal(result.hasCompleted, true);
});

test('after B2 the main line is reported complete; B2 alone is not', () => {
  const all = progress(Object.fromEntries(LEVELS.map((level) => [level, 'done'])));
  assert.deepEqual(recommendNextCourse({ courses, progress: all, afterSlug: 'fleng-b2' }), {
    status: 'complete', course: null, hasCompleted: true,
  });
  const onlyB2 = recommendNextCourse({ courses, progress: progress({ B2: 'done' }), afterSlug: 'fleng-b2' });
  assert.equal(onlyB2.status, 'none');
});

test('nothing to show: no courses, no progress rows, no lessons, unknown levels', () => {
  assert.equal(recommendNextCourse({ courses: [], progress: [] }).status, 'none');
  assert.equal(recommendNextCourse({ courses, progress: [] }).status, 'none');
  assert.equal(recommendNextCourse({ courses: undefined, progress: undefined }).status, 'none');
  const empty = courses.map((course) => ({ ...course, lessonCount: 0 }));
  assert.equal(recommendNextCourse({ courses: empty, progress: progress({ A0: 'done' }) }).status, 'none');
  const c1 = [{ ...courses[0], level: 'C1', id: 'x', slug: 'c1' }];
  assert.equal(recommendNextCourse({ courses: c1, progress: [{ courseId: 'x', lessonsTotal: 1, lessonsStarted: 0, lessonsCompleted: 0 }] }).status, 'none');
});

test('API order is irrelevant; the line is sorted by level, ties keep API order', () => {
  const shuffled = [courses[3], courses[1], courses[0], courses[2], courses[4]];
  assert.equal(slug(recommendNextCourse({ courses: shuffled, progress: progress({ A0: 'done' }) })), 'fleng-a1');
  const twin = { ...courses[1], id: 'A1b', slug: 'a1-second' };
  const extra = [courses[0], courses[1], twin];
  const rows = [...progress({ A0: 'done' }), { courseId: 'A1b', lessonsTotal: 5, lessonsStarted: 0, lessonsCompleted: 0 }];
  assert.equal(slug(recommendNextCourse({ courses: extra, progress: rows })), 'fleng-a1');
});

test('placementLevelFrom uses only a completed attempt with a main-line level', () => {
  assert.equal(placementLevelFrom([]), null);
  assert.equal(placementLevelFrom([{ status: 'in_progress', estimatedLevel: 'B2' }]), null);
  assert.equal(placementLevelFrom([{ status: 'completed', estimatedLevel: null }]), null);
  assert.equal(
    placementLevelFrom([{ status: 'in_progress', estimatedLevel: null }, { status: 'completed', estimatedLevel: 'A2' }]),
    'A2',
  );
});

import { pickCurrentCourse } from '../frontend/js/next-course.js';

const row = (level, started, completed, total = 10) => ({
  courseId: level, level, lessonsTotal: total, lessonsStarted: started, lessonsCompleted: completed,
});

test('current course: furthest unfinished started course, never an old finished one', () => {
  assert.equal(pickCurrentCourse([row('A0', 10, 10), row('A1', 2, 1), row('A2', 0, 0)]).level, 'A1');
  // Moved on before finishing the earlier course: the later one is current.
  assert.equal(pickCurrentCourse([row('A0', 9, 9), row('A1', 1, 0)]).level, 'A1');
  // Same level: higher completion wins.
  const a = { ...row('A1', 3, 2), courseId: 'x' };
  const b = { ...row('A1', 5, 4), courseId: 'y' };
  assert.equal(pickCurrentCourse([a, b]).courseId, 'y');
});

test('current course: when everything started is finished, show the furthest finished', () => {
  assert.equal(pickCurrentCourse([row('A0', 10, 10), row('A1', 10, 10), row('A2', 0, 0)]).level, 'A1');
  assert.equal(pickCurrentCourse([row('A1', 10, 10), row('A0', 10, 10)]).level, 'A1'); // API order is irrelevant
});

test('current course: nothing started or empty data gives null', () => {
  assert.equal(pickCurrentCourse([row('A0', 0, 0)]), null);
  assert.equal(pickCurrentCourse([]), null);
  assert.equal(pickCurrentCourse(undefined), null);
});
