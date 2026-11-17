import {
  completeFlashcardSession,
  createFlashcardSession,
  reviewVocabularyItem,
} from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

/**
 * The review endpoint schedules by `remembered` only (1 day vs 7 days), so the
 * two answers map directly onto the two scheduling buckets.
 */
const RATINGS = {
  correct: { remembered: true },
  incorrect: { remembered: false },
};
const RATING_KEYS = ['correct', 'incorrect'];
const HINT_FRONT = ['Click the card or press ', 'Space', ' to flip the translation'];
const HINT_BACK = ['Mark the answer — keys ', '1–2', ' also work'];

const node = {
  deck: document.getElementById('flashcards-deck'),
  counter: document.getElementById('flashcards-counter'),
  position: document.getElementById('flashcards-position'),
  total: document.getElementById('flashcards-total'),
  dots: document.getElementById('flashcards-dots'),
  error: document.getElementById('flashcards-error'),
  errorText: document.getElementById('flashcards-error-text'),
  retry: document.getElementById('flashcards-retry'),
  status: document.getElementById('flashcards-status'),
  content: document.getElementById('flashcards-content'),
  card: document.getElementById('flashcards-card'),
  topic: document.getElementById('flashcards-topic'),
  word: document.getElementById('flashcards-word'),
  transcription: document.getElementById('flashcards-transcription'),
  example: document.getElementById('flashcards-example'),
  translation: document.getElementById('flashcards-translation'),
  hint: document.getElementById('flashcards-hint'),
  flip: document.getElementById('flashcards-flip'),
  ratings: document.getElementById('flashcards-ratings'),
  empty: document.getElementById('flashcards-empty'),
  summary: document.getElementById('flashcards-summary'),
  summaryTitle: document.getElementById('flashcards-summary-title'),
  summaryStats: document.getElementById('flashcards-summary-stats'),
  again: document.getElementById('flashcards-again'),
};

const state = {
  sessionId: null,
  cards: [],
  index: 0,
  revealed: false,
  busy: false,
  tally: { correct: 0, incorrect: 0 },
};

function currentCard() {
  return state.cards[state.index] ?? null;
}

function resetState() {
  state.sessionId = null;
  state.cards = [];
  state.index = 0;
  state.revealed = false;
  state.busy = false;
  state.tally = { correct: 0, incorrect: 0 };
}

function hideAll() {
  node.error.hidden = true;
  node.status.hidden = true;
  node.content.hidden = true;
  node.empty.hidden = true;
  node.summary.hidden = true;
}

function showError(error) {
  if (error?.status === 401) {
    window.location.replace('/login.html');
    return;
  }
  node.errorText.textContent = describeApiError(error);
  node.error.hidden = false;
}

function setRatingsDisabled(disabled) {
  for (const button of node.ratings.querySelectorAll('button')) {
    button.disabled = disabled;
  }
}

function setHint(parts) {
  const [before, key, after] = parts;
  node.hint.replaceChildren(
    document.createTextNode(before),
    el('kbd', undefined, key),
    document.createTextNode(after),
  );
}

function buildDots() {
  node.dots.replaceChildren();
  for (let index = 0; index < state.cards.length; index += 1) {
    node.dots.append(el('span', 'flashcards-dot'));
  }
}

function updateProgress() {
  const total = state.cards.length;
  const position = Math.min(state.index + 1, total);
  node.position.textContent = String(position);
  node.total.textContent = String(total);
  const dots = node.dots.children;
  for (let index = 0; index < dots.length; index += 1) {
    dots[index].classList.toggle('is-done', index < state.index);
    dots[index].classList.toggle('is-current', index === state.index);
  }
}

function describeCard(card) {
  const parts = [`Word: ${card.word}`];
  if (card.transcription) parts.push(`Transcription: ${card.transcription}`);
  if (card.partOfSpeech) parts.push(`Part of speech: ${card.partOfSpeech}`);
  if (card.example) parts.push(`Example: ${card.example}`);
  parts.push('Activate to reveal the translation.');
  return parts.join(' ');
}

function topicLabel(card) {
  return [card.topic, card.partOfSpeech].filter(Boolean).join(' · ') || 'Word';
}

function renderCard() {
  const card = currentCard();
  if (!card) return;
  node.topic.textContent = topicLabel(card);
  node.word.textContent = card.word;
  node.transcription.textContent = card.transcription || '';
  node.translation.textContent = card.translation;
  node.example.textContent = card.example || '';
  node.card.classList.remove('is-revealed');
  node.card.setAttribute('aria-label', describeCard(card));
  node.ratings.hidden = true;
  node.flip.hidden = false;
  state.revealed = false;
  setRatingsDisabled(false);
  setHint(HINT_FRONT);
  updateProgress();
}

function reveal() {
  if (state.revealed || state.busy) return;
  const card = currentCard();
  if (!card) return;
  state.revealed = true;
  node.card.classList.add('is-revealed');
  node.card.setAttribute(
    'aria-label',
    `Translation: ${card.translation}. Choose correct or incorrect.`,
  );
  node.flip.hidden = true;
  node.ratings.hidden = false;
  setHint(HINT_BACK);
}

async function rate(rating) {
  const config = RATINGS[rating];
  const card = currentCard();
  if (!config || !card || state.busy || !state.revealed) return;

  state.busy = true;
  setRatingsDisabled(true);
  try {
    await reviewVocabularyItem(card.wordId, config.remembered);
    node.error.hidden = true;
    state.tally[rating] += 1;
    advance();
  } catch (error) {
    showError(error);
  } finally {
    state.busy = false;
    setRatingsDisabled(false);
  }
}

function advance() {
  state.index += 1;
  state.revealed = false;
  if (state.index >= state.cards.length) {
    finish();
    return;
  }
  renderCard();
  node.card.focus();
}

async function finish() {
  node.content.hidden = true;
  node.status.hidden = true;
  node.counter.hidden = true;
  try {
    await completeFlashcardSession(state.sessionId);
  } catch (error) {
    // The local tally is still useful, so show the summary and report the
    // completion failure without blocking the result.
    showError(error);
  }
  renderSummary();
}

function renderSummary() {
  node.summaryStats.replaceChildren();
  for (const key of RATING_KEYS) {
    const item = el('div', 'flashcards-summary-stat');
    item.append(
      el('dt', undefined, key[0].toLocaleUpperCase() + key.slice(1)),
      el('dd', undefined, String(state.tally[key])),
    );
    node.summaryStats.append(item);
  }
  const total = state.cards.length;
  node.summaryTitle.textContent = `You reviewed ${total} ${total === 1 ? 'word' : 'words'}`;
  node.summary.hidden = false;
  node.again.focus();
}

function showEmpty() {
  hideAll();
  node.counter.hidden = true;
  node.deck.hidden = true;
  node.empty.hidden = false;
}

async function load() {
  resetState();
  hideAll();
  node.counter.hidden = true;
  node.deck.hidden = true;
  node.status.hidden = false;
  node.status.textContent = 'Loading cards…';

  try {
    const session = await createFlashcardSession({ source: 'my_words' });
    state.sessionId = session.sessionId;
    state.cards = session.cards ?? [];
    if (session.status === 'empty' || state.cards.length === 0) {
      showEmpty();
      return;
    }
    node.status.hidden = true;
    node.content.hidden = false;
    node.deck.hidden = false;
    node.counter.hidden = false;
    buildDots();
    renderCard();
  } catch (error) {
    hideAll();
    showError(error);
  }
}

node.card.addEventListener('click', reveal);
node.flip.addEventListener('click', reveal);
node.ratings.addEventListener('click', (event) => {
  const button = event.target.closest('[data-rating]');
  if (button) rate(button.dataset.rating);
});
node.retry.addEventListener('click', load);
node.again.addEventListener('click', load);

document.addEventListener('keydown', (event) => {
  if (event.target.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (event.key === ' ' || event.key === 'Spacebar') {
    if (!state.revealed && !state.busy && currentCard()) {
      event.preventDefault();
      reveal();
    }
    return;
  }
  if (!state.revealed || state.busy) return;
  const selected = { 1: 'correct', 2: 'incorrect' }[event.key];
  if (!selected) return;
  event.preventDefault();
  rate(selected);
});

mountWorkspace('flashcards');
load();
