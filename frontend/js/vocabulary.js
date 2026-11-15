import { addVocabulary, listVocabulary, reviewVocabulary, updateVocabulary } from './api.js';
import { el } from './layout.js';
import { describeApiError } from './errors.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { letterTiles } from './letter-tiles.js';

const $ = (id) => document.getElementById(id);
const modes = ['list', 'flashcards', 'choice', 'write', 'letters'];
const initialMode = new URLSearchParams(location.search).get('mode');
const state = { words: [], filter: 'all', mode: modes.includes(initialMode) ? initialMode : 'list', loading: false, busy: false, queue: [], index: 0, remembered: new Set(), needsPractice: new Set(), reviewing: null, request: 0 };
const normalize = (value) => value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('en');
const isDue = (word) => new Date(word.dueAt).getTime() <= Date.now();

function control(text, action, className = 'lesson-button lesson-button-secondary') {
  const node = el('button', className, text);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}

function feedback(text = '', error = false) {
  $('word-feedback').textContent = text;
  $('word-feedback').classList.toggle('is-error', error);
}

function speak(word) {
  if (!('speechSynthesis' in window)) {
    feedback('Your browser does not support word playback.', true);
    return;
  }
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(word);
  utterance.lang = 'en-US';
  utterance.rate = .85;
  utterance.onerror = () => feedback('Word playback is unavailable on this device.', true);
  speechSynthesis.speak(utterance);
}

function speakButton(word) {
  const node = control('', () => speak(word), 'word-speak');
  node.setAttribute('aria-label', `Listen to ${word}`);
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', 'M11 5 6 9H3v6h3l5 4V5ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14');
  svg.append(path);
  node.append(svg);
  return node;
}

function filteredWords() {
  const query = normalize($('word-search').value);
  return state.words.filter((word) => (
    (state.filter === 'all' || (state.filter === 'learned' ? word.learned : state.filter === 'learning' ? !word.learned : isDue(word))) &&
    (!query || normalize(`${word.word} ${word.translation} ${word.example}`).includes(query))
  ));
}

function renderStats() {
  const stats = [['Saved words', state.words.length], ['Learning', state.words.filter((w) => !w.learned).length], ['Learned', state.words.filter((w) => w.learned).length], ['Due today', state.words.filter(isDue).length]];
  $('words-stats').replaceChildren(...stats.map(([label, value]) => {
    const card = el('div', 'word-stat');
    const copy = el('div');
    copy.append(el('strong', undefined, String(value)), el('span', undefined, label));
    card.append(copy);
    return card;
  }));
}

function empty(target, title, description) {
  const card = el('div', 'word-empty');
  card.append(el('h2', undefined, title), el('p', 'dashboard-muted', description));
  target.replaceChildren(card);
  return card;
}

function updateWord(updated) {
  const index = state.words.findIndex((word) => word.id === updated.id);
  if (index !== -1) state.words[index] = updated;
  renderStats();
}

function renderWords() {
  const words = filteredWords();
  const target = $('word-list');
  target.replaceChildren();
  $('word-count').textContent = `${words.length} ${words.length === 1 ? 'word' : 'words'}`;
  if (!words.length) {
    const card = empty(target, state.words.length ? 'No matching words' : 'Your collection starts here', state.words.length ? 'Try another search or choose All words.' : 'Add your first word and start practising.');
    if (!state.words.length) card.append(control('＋ Add your first word', openAddDialog, 'lesson-button lesson-button-primary'));
    return;
  }
  for (const word of words) {
    const row = el('article', 'word-row');
    const copy = el('div', 'word-copy');
    copy.append(el('h3', undefined, word.word), el('p', undefined, word.translation));
    if (word.example) copy.append(el('small', undefined, word.example));
    const status = el('span', `word-status${word.learned ? ' is-learned' : ''}`, word.learned ? '✓ Learned' : isDue(word) ? 'Due today' : 'Learning');
    const actions = el('div', 'word-row-actions');
    const toggle = control(word.learned ? 'Keep learning' : 'Mark learned', async () => {
      toggle.disabled = true;
      try {
        updateWord(await updateVocabulary(word.id, !word.learned));
        renderWords();
        feedback('Vocabulary updated.');
      } catch (error) {
        feedback(describeApiError(error), true);
        toggle.disabled = false;
      }
    });
    actions.append(toggle, control('Practise ↗', () => setMode('flashcards', word.id), 'lesson-button lesson-button-primary'));
    row.append(speakButton(word.word), copy, status, actions);
    target.append(row);
  }
}

function setControlsDisabled(disabled) {
  for (const node of document.querySelectorAll('[data-mode], [data-filter], #word-search, #add-word')) node.disabled = disabled;
}

function shuffle(items) {
  const result = [...items];
  for (let index = result.length - 1; index > 0; index--) {
    const swap = Math.floor(Math.random() * (index + 1));
    [result[index], result[swap]] = [result[swap], result[index]];
  }
  return result;
}

function startPractice(firstId) {
  let words = filteredWords();
  if (state.mode === 'letters') words = words.filter((word) => /^[a-zA-Z]{2,24}$/.test(word.word));
  state.queue = shuffle(words.map((word) => word.id));
  if (firstId && state.queue.includes(firstId)) state.queue = [firstId, ...state.queue.filter((id) => id !== firstId)];
  state.index = 0;
  state.remembered.clear();
  state.needsPractice.clear();
  state.reviewing = null;
  renderPractice();
}

function setMode(mode, firstId) {
  if (state.busy) return;
  state.mode = mode;
  const url = new URL(location.href);
  if (mode === 'list') url.searchParams.delete('mode');
  else url.searchParams.set('mode', mode);
  history.replaceState(null, '', url);
  for (const node of document.querySelectorAll('[data-mode]')) node.setAttribute('aria-pressed', String(node.dataset.mode === mode));
  for (const node of document.querySelectorAll('.sidebar-link[data-section]')) {
    const selected = node.dataset.section === (mode === 'list' ? 'words' : 'practice');
    node.classList.toggle('active', selected);
    if (selected) node.setAttribute('aria-current', 'page');
    else node.removeAttribute('aria-current');
  }
  $('word-list-panel').hidden = mode !== 'list';
  $('word-practice-panel').hidden = mode === 'list';
  feedback();
  if (mode === 'list') renderWords();
  else startPractice(firstId);
}

function renderPractice() {
  const target = $('word-practice');
  target.replaceChildren();
  if (!state.queue.length) {
    empty(target, 'No words for this activity', state.mode === 'letters' ? 'Add a single English word with 2–24 letters, or choose another activity.' : 'Add some words or change your filters to begin.');
    return;
  }
  if (state.index >= state.queue.length) {
    const card = empty(target, 'Practice complete!', `${state.remembered.size} remembered · ${state.needsPractice.size} to practise again. Your review progress has been saved.`);
    const actions = el('div', 'word-practice-actions');
    actions.append(control('Practise again', () => startPractice(), 'lesson-button lesson-button-primary'), control('Back to my words', () => setMode('list')));
    card.append(actions);
    return;
  }
  const word = state.words.find((item) => item.id === state.queue[state.index]);
  state.reviewing = word.id;
  const modeLabels = { flashcards: 'FLASHCARDS', choice: 'MULTIPLE CHOICE', write: 'WRITE THE WORD', letters: 'MISSING LETTERS' };
  const meta = el('div', 'word-practice-meta');
  meta.append(el('span', undefined, modeLabels[state.mode]), el('span', undefined, `${state.index + 1} / ${state.queue.length}`));
  const card = el('div', 'word-practice-card');
  const heading = el('h2', undefined, state.mode === 'write' || state.mode === 'letters' ? word.translation : word.word);
  card.append(el('span', 'lesson-chip', state.mode === 'flashcards' ? 'WORD CARD' : 'VOCABULARY PRACTICE'), heading);
  const result = el('p', 'word-practice-result');
  result.setAttribute('role', 'status');
  const actions = el('div', 'word-practice-actions');
  target.append(meta, card);

  async function grade(remembered) {
    if (state.busy) return;
    state.busy = true;
    setControlsDisabled(true);
    const localControls = [...card.querySelectorAll('button, input')];
    for (const node of localControls) node.disabled = true;
    let saved = false;
    try {
      updateWord(await reviewVocabulary(word.id, remembered));
      if (remembered) { state.remembered.add(word.id); state.needsPractice.delete(word.id); }
      else { state.needsPractice.add(word.id); state.remembered.delete(word.id); }
      saved = true;
      result.classList.toggle('is-error', !remembered);
      result.textContent = `${remembered ? '✓ Well done!' : 'Keep practising.'} ${word.word} — ${word.translation}`;
      if (word.example) result.append(el('span', undefined, ` · ${word.example}`));
      actions.replaceChildren(control(state.index + 1 === state.queue.length ? 'See results →' : 'Next word →', () => { state.index++; renderPractice(); }, 'lesson-button lesson-button-primary'));
      actions.querySelector('button').focus();
    } catch (error) {
      result.classList.add('is-error');
      result.textContent = `Your review was not saved. ${describeApiError(error)} Try again.`;
    } finally {
      state.busy = false;
      setControlsDisabled(false);
      if (!saved) for (const node of localControls) node.disabled = false;
    }
  }

  if (state.mode === 'flashcards') {
    card.append(speakButton(word.word), el('p', 'dashboard-muted', 'Think of the translation, then reveal the answer.'));
    const translation = el('div');
    translation.hidden = true;
    translation.append(el('h3', undefined, word.translation));
    if (word.example) translation.append(el('p', 'dashboard-muted', word.example));
    card.append(translation);
    actions.append(control('Reveal translation', () => {
      translation.hidden = false;
      actions.replaceChildren(control('I need practice', () => grade(false)), control('I knew it ✓', () => grade(true), 'lesson-button lesson-button-primary'));
    }, 'lesson-button lesson-button-primary'));
  } else if (state.mode === 'choice') {
    card.append(speakButton(word.word), el('p', 'dashboard-muted', 'Choose the correct translation.'));
    const alternatives = [...new Set(state.words.map((item) => item.translation))].filter((translation) => normalize(translation) !== normalize(word.translation));
    if (!alternatives.length) {
      card.append(el('p', 'dashboard-muted', 'Add at least two words with different translations to use Multiple choice.'));
      actions.append(control('Try flashcards', () => setMode('flashcards'), 'lesson-button lesson-button-primary'));
    } else {
      const choices = el('div', 'word-choice-list');
      for (const choice of shuffle([word.translation, ...shuffle(alternatives).slice(0, 3)])) choices.append(control(choice, () => grade(normalize(choice) === normalize(word.translation)), 'word-choice'));
      card.append(choices);
    }
  } else {
    const form = el('form');
    let readAnswer;
    if (state.mode === 'write') {
      const label = el('label', 'lesson-answer-label', 'Type the English word');
      const input = el('input', 'lesson-answer');
      input.required = true;
      input.autocomplete = 'off';
      input.spellcheck = false;
      input.maxLength = 120;
      input.setAttribute('autocapitalize', 'none');
      label.append(input);
      form.append(label);
      readAnswer = () => input.value;
    } else {
      const letters = [...word.word];
      const pattern = letters.map((letter, index) => index % 3 === 0 ? letter : '_').join('');
      const bank = shuffle(letters.filter((_, index) => index % 3 !== 0));
      const tiles = letterTiles({ pattern, letters: bank }, '', null, () => { result.textContent = ''; });
      form.append(tiles.field);
      readAnswer = tiles.readAnswer;
    }
    const check = el('button', 'lesson-button lesson-button-primary', 'Check answer');
    check.type = 'submit';
    const formActions = el('div', 'word-practice-actions');
    formActions.append(check);
    form.append(formActions);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const answer = readAnswer();
      if (!answer.trim()) { result.classList.add('is-error'); result.textContent = 'Complete your answer first.'; return; }
      grade(normalize(answer) === normalize(word.word));
    });
    card.append(form);
  }
  card.append(result, actions);
}

function openAddDialog() {
  if (state.busy) return;
  $('word-form-error').hidden = true;
  $('word-dialog').showModal();
}

async function load() {
  if (state.loading) return;
  state.loading = true;
  const request = ++state.request;
  $('words-error').hidden = true;
  $('words-loading').hidden = false;
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user || request !== state.request) return;
    setWorkspaceUser(user);
    const words = [];
    for (let offset = 0; ; offset += 100) {
      const page = await listVocabulary(offset);
      if (request !== state.request) return;
      words.push(...page);
      if (page.length < 100) break;
    }
    state.words = words;
    $('words-content').hidden = false;
    renderStats();
    setMode(state.mode);
  } catch (error) {
    if (request !== state.request) return;
    $('words-error-text').textContent = describeApiError(error);
    $('words-error').hidden = false;
  } finally {
    if (request === state.request) { state.loading = false; $('words-loading').hidden = true; }
  }
}

mountWorkspace(state.mode === 'list' ? 'words' : 'practice');
$('add-word').addEventListener('click', openAddDialog);
$('word-dialog-close').addEventListener('click', () => $('word-dialog').close());
$('words-retry').addEventListener('click', load);
for (const button of document.querySelectorAll('[data-mode]')) button.addEventListener('click', () => setMode(button.dataset.mode));
for (const button of document.querySelectorAll('[data-filter]')) button.addEventListener('click', () => {
  if (state.busy) return;
  state.filter = button.dataset.filter;
  for (const node of document.querySelectorAll('[data-filter]')) node.setAttribute('aria-pressed', String(node === button));
  if (state.mode === 'list') renderWords();
  else startPractice();
});
$('word-search').addEventListener('input', () => { if (state.mode === 'list') renderWords(); else startPractice(); });
$('word-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!$('word-form').reportValidity()) return;
  const save = $('word-save');
  save.disabled = true;
  $('word-form-error').hidden = true;
  try {
    const word = await addVocabulary({ word: $('new-word').value.trim(), translation: $('new-translation').value.trim(), example: $('new-example').value.trim() });
    state.words.push(word);
    $('word-dialog').close();
    $('word-form').reset();
    renderStats();
    setMode('list');
    feedback(`Saved “${word.word}” to your vocabulary.`);
  } catch (error) {
    $('word-form-error').textContent = error.code === 'WORD_EXISTS' ? 'This word is already in your collection.' : describeApiError(error);
    $('word-form-error').hidden = false;
  } finally { save.disabled = false; }
});
window.addEventListener('pagehide', () => { if ('speechSynthesis' in window) speechSynthesis.cancel(); });
window.addEventListener('fleng:session-ended', () => {
  state.request++;
  state.words = [];
  state.queue = [];
  $('words-content').hidden = true;
  $('word-dialog').close();
  if ('speechSynthesis' in window) speechSynthesis.cancel();
});
window.addEventListener('pageshow', (event) => { if (event.persisted) load(); });
load();
