import en from './i18n/en.js';
import { t } from './i18n.js';

const limitations = new Map(Object.entries(en)
  .filter(([key]) => key.startsWith('pt.limit.'))
  .map(([key, text]) => [text, key]));

export function placementLimitation(text) {
  return t(limitations.get(text) ?? text);
}

export function placementLabel(result) {
  if (result.insufficientEvidence) return t('pt.result.insufficient');
  if (result.estimatedLevel === 'B2') return t('pt.result.b2');
  if (result.estimatedLevel) return t('pt.result.estimated', { level: result.estimatedLevel });
  if (result.insufficientEvidence === false) return t('pt.result.below');
  return result.label;
}

export function placementRecommendation(attempt) {
  if (attempt.result.insufficientEvidence) return t('pt.recommendation.insufficient');
  const level = attempt.result.estimatedLevel ?? 'A0';
  return t(attempt.recommendedCourses.length ? 'pt.recommendation.match' : 'pt.recommendation.missing', { level });
}
