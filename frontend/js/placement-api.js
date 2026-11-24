import { apiFetch } from './api.js';

const base = '/placement-test/attempts';
export const startPlacement = () => apiFetch(base, { method: 'POST' });
export const listPlacements = (offset = 0) => apiFetch(`${base}?limit=20&offset=${offset}`);
export const getPlacement = (id) => apiFetch(`${base}/${encodeURIComponent(id)}`);
export const savePlacementAnswer = (id, questionId, optionId) => apiFetch(`${base}/${encodeURIComponent(id)}/answers`, {
  method: 'PUT', body: JSON.stringify({ answers: [{ questionId, optionId }] }),
});
export const completePlacement = (id) => apiFetch(`${base}/${encodeURIComponent(id)}/complete`, { method: 'POST' });
export const retryPlacementMistakes = (id) => apiFetch(`${base}/${encodeURIComponent(id)}/retry-mistakes`, { method: 'POST' });
