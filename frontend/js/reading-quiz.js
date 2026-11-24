/** Pure helpers for the Reading article page (no DOM), unit-tested in scripts/test-reading.mjs. */

/** Article text -> paragraphs. Blocks are separated by blank lines; single newlines become spaces. */
export function paragraphs(content) {
  return String(content ?? '')
    .split(/\n\s*\n/)
    .map((block) => block.replace(/\s*\n\s*/g, ' ').trim())
    .filter(Boolean);
}

/** `{questionId: answerId}` limited to questions that exist in the quiz. */
export function pickAnswers(questions, answers) {
  const ids = new Set(questions.map((question) => question.id));
  return Object.fromEntries(
    Object.entries(answers ?? {}).filter(([questionId]) => ids.has(questionId)),
  );
}

export function answeredCount(questions, answers) {
  return Object.keys(pickAnswers(questions, answers)).length;
}

/** Submitting needs every question answered. */
export function canSubmit(questions, answers) {
  return questions.length > 0 && answeredCount(questions, answers) === questions.length;
}

/**
 * Seconds a learner must have spent on the page before scrolling to the end counts as 100%.
 * A quarter of the estimated reading time, between 5 and 30 seconds, so opening a short article
 * that fits the screen cannot complete it instantly. (Authoritative reading time is future work.)
 */
export function requiredDwellSeconds(readingMinutes) {
  return Math.min(30, Math.max(5, Math.round(readingMinutes * 15)));
}

/** The percentage that may be reported now: capped at 99 until the dwell time has passed. */
export function reportablePercent(percent, dwellSeconds, readingMinutes) {
  const clamped = Math.max(0, Math.min(100, Math.floor(percent)));
  return dwellSeconds >= requiredDwellSeconds(readingMinutes) ? clamped : Math.min(clamped, 99);
}

/** What the result panel should say, derived only from the server's submit response. */
export function resultSummary(result) {
  return {
    passed: Boolean(result.passed),
    percent: result.scorePercent,
    xp: result.xpAwarded,
    showXp: result.passed && result.xpAwarded > 0,
    alreadyEarned: result.passed && result.xpAwarded === 0,
    correct: result.questions.filter((item) => item.isCorrect).length,
    total: result.questions.length,
  };
}

/** Label of an option in a result review: chosen/correct combinations. */
export function reviewOptionState(item, answerId) {
  const correct = answerId === item.correctAnswerId;
  const chosen = answerId === item.selectedAnswerId;
  if (correct) return chosen ? 'correct-chosen' : 'correct';
  return chosen ? 'wrong-chosen' : 'neutral';
}

/** The open (unfinished) attempt in a history list, if any. */
export const openAttempt = (history) =>
  history.find((attempt) => attempt.status === 'in_progress') ?? null;
