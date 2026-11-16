// Shared, deterministic rules for the vocabulary study/test flow.
export const TEST_MODES = ['choice', 'write', 'letters'];
export const normalizeAnswer = (value) => String(value).normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('en');
export function shuffleCopy(items, random = Math.random) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
export function testCards(cards, mode) {
  return mode === 'letters' ? cards.filter((card) => /^[a-zA-Z]{2,24}$/.test(card.word)) : [...cards];
}
export function translationChoices(card, cards) {
  const unique = new Map();
  for (const item of cards) {
    const key = normalizeAnswer(item.translation);
    if (key !== normalizeAnswer(card.translation) && !unique.has(key)) unique.set(key, item.translation);
  }
  return shuffleCopy([card.translation, ...shuffleCopy([...unique.values()]).slice(0, 3)]);
}
export function sessionMetrics(answers, start, finish) {
  const correct = answers.filter((answer) => answer.correct).length;
  const seconds = Math.max(0, Math.floor((finish - start) / 1000));
  return { correct, total: answers.length, mistakes: answers.filter((answer) => !answer.correct),
    accuracy: answers.length ? Math.round(correct / answers.length * 100) : 0,
    time: `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}` };
}
