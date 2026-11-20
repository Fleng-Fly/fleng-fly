// Deterministic "what should I study next" logic. Pure: no DOM, no network, no imports.
// Inputs are the existing /courses, /progress/me and placement-summary shapes.

/** The main learning line, in study order. */
export const MAIN_LINE = ['A0', 'A1', 'A2', 'B1', 'B2'];

const lineIndex = (level) => MAIN_LINE.indexOf(level);

function isCompleted(entry) {
  return Boolean(entry) && entry.lessonsTotal > 0 && entry.lessonsCompleted >= entry.lessonsTotal;
}

/**
 * Recommend the next main-line course.
 *
 * @param {object} input
 * @param {Array}  input.courses        /courses list (id, slug, title, description, level, lessonCount)
 * @param {Array}  input.progress       /progress/me `courses` array (courseId, lessonsTotal, lessonsStarted, lessonsCompleted)
 * @param {string|null} [input.placementLevel] estimated level of the latest completed placement, if any
 * @param {string|null} [input.afterSlug]      a just-completed course: only courses after it qualify
 * @returns {{status: 'next', course: object, hasCompleted: boolean}
 *         | {status: 'complete', course: null, hasCompleted: true}
 *         | {status: 'none', course: null, hasCompleted: boolean}}
 *
 * Rules: completed courses are never recommended; a course the learner is already
 * working on is "Continue", not "next", so it is skipped; courses below the placement
 * level are skipped; courses without lessons or outside A0–B2 are ignored. 'complete'
 * means every published main-line course is finished.
 */
export function recommendNextCourse({ courses, progress, placementLevel = null, afterSlug = null }) {
  const byCourse = new Map((progress || []).map((entry) => [entry.courseId, entry]));
  const line = (courses || [])
    .filter((course) => lineIndex(course.level) >= 0 && course.lessonCount > 0)
    .map((course, order) => ({ course, order, entry: byCourse.get(course.id) }))
    .sort((a, b) => lineIndex(a.course.level) - lineIndex(b.course.level) || a.order - b.order);

  const hasCompleted = line.some(({ entry }) => isCompleted(entry));
  const none = { status: 'none', course: null, hasCompleted };
  if (!line.length) return none;
  // A course with no progress row cannot be classified honestly: recommend nothing for it.
  const known = line.filter(({ entry }) => entry);
  if (known.length === line.length && known.every(({ entry }) => isCompleted(entry))) {
    return { status: 'complete', course: null, hasCompleted: true };
  }

  let from = Math.max(0, lineIndex(placementLevel));
  if (afterSlug) {
    const after = line.findIndex(({ course }) => course.slug === afterSlug);
    if (after < 0) return none;
    from = Math.max(from, lineIndex(line[after].course.level) + 1);
  }
  const candidate = known.find(
    ({ course, entry }) =>
      lineIndex(course.level) >= from && !isCompleted(entry) && !(entry.lessonsStarted > 0),
  );
  return candidate ? { status: 'next', course: candidate.course, hasCompleted } : none;
}

/** Estimated level of the newest completed placement attempt (list summaries are enough). */
export function placementLevelFrom(attempts) {
  const done = (attempts || []).find((attempt) => attempt.status === 'completed');
  return done && lineIndex(done.estimatedLevel) >= 0 ? done.estimatedLevel : null;
}

/**
 * The course the dashboard should present as "current", from /progress/me `courses`.
 * An unfinished started course wins (the furthest main-line level first, then the highest
 * completion); when everything started is finished, the furthest finished course is shown.
 * A course the learner never touched is never current.
 */
export function pickCurrentCourse(courses) {
  const started = (courses || []).filter((course) => course.lessonsStarted > 0);
  const unfinished = started.filter((course) => !isCompleted(course));
  const pool = unfinished.length ? unfinished : started;
  const ratio = (course) => (course.lessonsTotal ? course.lessonsCompleted / course.lessonsTotal : 0);
  return pool.reduce((best, course) => {
    if (!best) return course;
    const diff = lineIndex(course.level) - lineIndex(best.level);
    return diff > 0 || (diff === 0 && ratio(course) > ratio(best)) ? course : best;
  }, null);
}
