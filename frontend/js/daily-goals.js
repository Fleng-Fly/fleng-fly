// Pure helpers for the daily-goals card. No DOM, no network, no imports.

export const GOAL_LIMITS = {
  lessons: { min: 1, max: 10 },
  words: { min: 1, max: 100 },
};

/** The browser's IANA time zone, or null when it cannot be determined. */
export function browserTimeZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch {
    return null;
  }
}

/** The profile is the source of truth; only a differing, known zone is sent. */
export function needsTimeZoneSync(user, zone) {
  return Boolean(zone) && Boolean(user) && user.timezone !== zone;
}

/** Bar width: goal met or exceeded is capped at 100; a missing/zero goal is 0. */
export function goalPercent(done, goal) {
  if (!(goal > 0) || !(done > 0)) return 0;
  return Math.min(100, Math.round((done / goal) * 100));
}

export const goalMet = (entry) => entry.goal > 0 && entry.done >= entry.goal;

/** Parse the two edit-form inputs; returns the PATCH payload or an error code. */
export function parseGoalInputs(lessonsValue, wordsValue) {
  const read = (value, { min, max }) => {
    const text = String(value ?? '').trim();
    if (!/^\d+$/.test(text)) return null;
    const number = Number(text);
    return number >= min && number <= max ? number : null;
  };
  const dailyLessonsGoal = read(lessonsValue, GOAL_LIMITS.lessons);
  const dailyWordsGoal = read(wordsValue, GOAL_LIMITS.words);
  if (dailyLessonsGoal === null || dailyWordsGoal === null) return { error: 'range' };
  return { value: { dailyLessonsGoal, dailyWordsGoal } };
}
