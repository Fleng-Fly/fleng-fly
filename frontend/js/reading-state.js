// Local-only reading practice: no course XP, server grades or AI calls.
export const PASS_SCORE = 8;
export function validAnswers(reading, answers) {
  return reading.questions.map((question, index) => {
    const value = answers?.[index];
    return Number.isInteger(value) && value >= 0 && value < question.options.length ? value : null;
  });
}
export function gradeReading(reading, answers) {
  const normalized = validAnswers(reading, answers);
  const complete = normalized.every(value => value !== null);
  const score = normalized.filter((value, index) => value === reading.questions[index].answer).length;
  return { complete, score, passed: complete && score >= PASS_SCORE, total: reading.questions.length };
}
export function restoreReading(reading, raw) {
  const answers = validAnswers(reading, raw?.answers);
  const finished = raw?.finished === true && gradeReading(reading, answers).complete;
  const best = Number.isInteger(raw?.best) && raw.best >= 0 && raw.best <= reading.questions.length ? raw.best : null;
  return { answers, finished, best: finished ? Math.max(best ?? 0, gradeReading(reading, answers).score) : best };
}
