import {
  createVocabularyItem,
  deleteVocabularyItem,
  listVocabulary,
  updateVocabularyItem,
} from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

/**
 * My Words — the personal vocabulary list.
 *
 * The list endpoint returns up to 100 words and has no server-side search, so
 * filtering, status tabs and pagination are applied in the browser. Saving,
 * marking learned and deleting go through the existing vocabulary API.
 */
const PAGE_SIZE = 10;
const FILTERS = new Set(['all', 'due', 'learning', 'learned']);

const $ = (id) => document.getElementById(id);

const node = {
  error: $('vocabulary-error'),
  errorText: $('vocabulary-error-text'),
  retry: $('vocabulary-retry'),
  content: $('vocabulary-content'),
  count: $('vocabulary-count'),
  addOpen: $('vocabulary-add-open'),
  filters: $('vocabulary-filters'),
  query: $('vocabulary-query'),
  status: $('vocabulary-status'),
  list: $('vocabulary-list'),
  empty: $('vocabulary-empty'),
  emptyText: $('vocabulary-empty-text'),
  emptyAdd: $('vocabulary-empty-add'),
  emptyClear: $('vocabulary-empty-clear'),
  footer: $('vocabulary-footer'),
  range: $('vocabulary-range'),
  pages: $('vocabulary-pages'),
  dialog: $('vocabulary-dialog'),
  dialogClose: $('vocabulary-dialog-close'),
  form: $('vocabulary-form'),
  formError: $('vocabulary-form-error'),
  word: $('vocabulary-word'),
  translation: $('vocabulary-translation'),
  partOfSpeech: $('vocabulary-pos'),
  transcription: $('vocabulary-transcription'),
  topic: $('vocabulary-topic'),
  example: $('vocabulary-example'),
  submit: $('vocabulary-submit'),
  cancel: $('vocabulary-cancel'),
};

const state = {
  words: [],
  filter: 'all',
  query: '',
  page: 0,
  busy: false,
};

function icon(id) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `#${id}`);
  svg.append(use);
  return svg;
}

function wordStatus(word) {
  if (word.learned) return 'learned';
  const due = new Date(word.dueAt).getTime();
  return Number.isFinite(due) && due <= Date.now() ? 'due' : 'scheduled';
}

function dueLabel(word) {
  if (word.learned) return 'Learned';
  const due = new Date(word.dueAt).getTime();
  if (!Number.isFinite(due)) return 'Scheduled';
  if (due <= Date.now()) return 'Due now';
  const days = Math.max(1, Math.ceil((due - Date.now()) / 86400000));
  return `In ${days} ${days === 1 ? 'day' : 'days'}`;
}

function metaLabel(word) {
  return (
    [word.transcription, word.partOfSpeech, word.topic]
      .map((value) => (typeof value === 'string' ? value.trim() : ''))
      .filter(Boolean)
      .join(' · ') || 'Saved word'
  );
}

function matchesFilter(word) {
  const status = wordStatus(word);
  if (state.filter === 'due' && status !== 'due') return false;
  if (state.filter === 'learning' && status === 'learned') return false;
  if (state.filter === 'learned' && status !== 'learned') return false;
  if (!state.query) return true;
  const haystack = [
    word.word,
    word.translation,
    word.example,
    word.transcription,
    word.partOfSpeech,
    word.topic,
  ]
    .filter((value) => typeof value === 'string')
    .join(' ')
    .toLocaleLowerCase();
  return haystack.includes(state.query);
}

function announce(message) {
  node.status.hidden = false;
  node.status.textContent = message;
}

function showError(error) {
  if (error?.status === 401) {
    window.location.replace('/login.html');
    return;
  }
  node.errorText.textContent = describeApiError(error);
  node.error.hidden = false;
}

function row(word) {
  const status = wordStatus(word);
  const item = el('li', 'vocabulary-row');
  item.dataset.status = status;

  const main = el('div', 'vocabulary-row-main');
  const dot = el('span', `vocabulary-dot is-${status}`);
  dot.setAttribute('aria-hidden', 'true');
  const copy = el('div', 'vocabulary-word');
  copy.append(el('strong', undefined, word.word), el('small', undefined, metaLabel(word)));
  main.append(dot, copy);

  const translation = el('p', 'vocabulary-translation', word.translation);

  const side = el('div', 'vocabulary-row-side');
  side.append(el('span', `vocabulary-chip is-${status}`, dueLabel(word)));

  const actions = el('div', 'vocabulary-actions');
  const toggle = el('button', 'vocabulary-action');
  toggle.type = 'button';
  toggle.title = word.learned
    ? `Mark “${word.word}” as still learning`
    : `Mark “${word.word}” as learned`;
  toggle.setAttribute('aria-label', toggle.title);
  toggle.append(icon(word.learned ? 'icon-undo' : 'icon-check'));
  toggle.addEventListener('click', () => toggleLearned(word));

  const remove = el('button', 'vocabulary-action is-danger');
  remove.type = 'button';
  remove.title = `Delete “${word.word}”`;
  remove.setAttribute('aria-label', remove.title);
  remove.append(icon('icon-trash'));
  remove.addEventListener('click', () => removeWord(word));

  actions.append(toggle, remove);
  side.append(actions);
  item.append(main, translation, side);
  return item;
}

function pageButton(label, disabled, action, { active = false, ariaLabel } = {}) {
  const button = el('button', 'vocabulary-page', label);
  button.type = 'button';
  button.disabled = disabled;
  if (active) {
    button.classList.add('is-active');
    button.setAttribute('aria-current', 'page');
  }
  if (ariaLabel) button.setAttribute('aria-label', ariaLabel);
  button.addEventListener('click', action);
  return button;
}

function renderPages(total, pageCount) {
  node.pages.replaceChildren();
  node.footer.hidden = total === 0;
  if (total === 0) return;

  const start = state.page * PAGE_SIZE + 1;
  const end = Math.min(total, (state.page + 1) * PAGE_SIZE);
  node.range.textContent = `${start}–${end} of ${total} ${total === 1 ? 'word' : 'words'}`;

  node.pages.append(
    pageButton(
      '‹',
      state.page === 0,
      () => {
        state.page -= 1;
        render();
      },
      { ariaLabel: 'Previous page' },
    ),
  );

  for (let page = 0; page < pageCount; page += 1) {
    node.pages.append(
      pageButton(
        String(page + 1),
        false,
        () => {
          state.page = page;
          render();
        },
        { active: page === state.page, ariaLabel: `Page ${page + 1}` },
      ),
    );
  }

  node.pages.append(
    pageButton(
      '›',
      state.page >= pageCount - 1,
      () => {
        state.page += 1;
        render();
      },
      { ariaLabel: 'Next page' },
    ),
  );
}

function render() {
  const visible = state.words.filter(matchesFilter);
  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  state.page = Math.min(Math.max(state.page, 0), pageCount - 1);

  const start = state.page * PAGE_SIZE;
  const pageWords = visible.slice(start, start + PAGE_SIZE);

  node.count.textContent = String(state.words.length);
  node.list.replaceChildren(...pageWords.map(row));
  node.list.hidden = pageWords.length === 0;
  node.status.hidden = true;
  node.status.textContent = '';

  const filtered = state.filter !== 'all' || state.query.length > 0;
  node.empty.hidden = pageWords.length > 0;
  if (pageWords.length === 0) {
    node.emptyText.textContent = filtered
      ? 'No words match this filter or search.'
      : 'Add your first word or save one from a lesson.';
    node.emptyClear.hidden = !filtered;
    node.emptyAdd.hidden = filtered;
  }

  renderPages(visible.length, pageCount);
}

function syncFilters() {
  for (const button of node.filters.querySelectorAll('[data-filter]')) {
    const active = button.dataset.filter === state.filter;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-selected', String(active));
  }
}

async function load() {
  node.error.hidden = true;
  node.status.hidden = false;
  node.status.textContent = 'Loading words…';
  node.list.hidden = true;
  node.empty.hidden = true;
  node.footer.hidden = true;

  try {
    const words = await listVocabulary({ limit: 100 });
    state.words = [...words].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
    state.page = 0;
    render();
  } catch (error) {
    showError(error);
  }
}

async function toggleLearned(word) {
  if (state.busy) return;
  state.busy = true;
  try {
    const updated = await updateVocabularyItem(word.id, { learned: !word.learned });
    state.words = state.words.map((item) => (item.id === updated.id ? updated : item));
    render();
    announce(
      updated.learned
        ? `“${updated.word}” marked as learned.`
        : `“${updated.word}” is back in your review queue.`,
    );
  } catch (error) {
    showError(error);
  } finally {
    state.busy = false;
  }
}

async function removeWord(word) {
  if (state.busy) return;
  if (!window.confirm(`Delete “${word.word}” from My Words?`)) return;
  state.busy = true;
  try {
    await deleteVocabularyItem(word.id);
    state.words = state.words.filter((item) => item.id !== word.id);
    render();
    announce(`Deleted “${word.word}”.`);
  } catch (error) {
    showError(error);
  } finally {
    state.busy = false;
  }
}

function openDialog() {
  node.formError.hidden = true;
  node.form.reset();
  if (!node.dialog.open) node.dialog.showModal();
  node.word.focus();
}

function closeDialog() {
  if (node.dialog.open) node.dialog.close();
}

async function submitForm(event) {
  event.preventDefault();
  if (state.busy) return;

  const input = {
    word: node.word.value.trim(),
    translation: node.translation.value.trim(),
    example: node.example.value.trim(),
    transcription: node.transcription.value.trim(),
    partOfSpeech: node.partOfSpeech.value.trim(),
    topic: node.topic.value.trim(),
  };

  if (!input.word || !input.translation) {
    node.formError.textContent = 'Word and translation are required.';
    node.formError.hidden = false;
    return;
  }

  state.busy = true;
  node.submit.disabled = true;
  node.submit.textContent = 'Saving…';
  node.formError.hidden = true;

  try {
    const created = await createVocabularyItem(input);
    closeDialog();
    state.filter = 'all';
    state.query = '';
    node.query.value = '';
    syncFilters();
    state.words = [created, ...state.words.filter((item) => item.id !== created.id)];
    state.page = 0;
    render();
    announce(`Added “${created.word}”.`);
  } catch (error) {
    if (error?.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    node.formError.textContent = describeApiError(error);
    node.formError.hidden = false;
  } finally {
    state.busy = false;
    node.submit.disabled = false;
    node.submit.textContent = 'Save word';
  }
}

node.filters.addEventListener('click', (event) => {
  const button = event.target.closest('[data-filter]');
  if (!button || !FILTERS.has(button.dataset.filter)) return;
  state.filter = button.dataset.filter;
  state.page = 0;
  syncFilters();
  render();
});

node.query.addEventListener('input', () => {
  state.query = node.query.value.trim().toLocaleLowerCase();
  state.page = 0;
  render();
});

node.emptyClear.addEventListener('click', () => {
  state.filter = 'all';
  state.query = '';
  state.page = 0;
  node.query.value = '';
  syncFilters();
  render();
});

node.addOpen.addEventListener('click', openDialog);
node.emptyAdd.addEventListener('click', openDialog);
node.dialogClose.addEventListener('click', closeDialog);
node.cancel.addEventListener('click', closeDialog);
node.form.addEventListener('submit', submitForm);
node.dialog.addEventListener('click', (event) => {
  if (event.target === node.dialog) closeDialog();
});
node.retry.addEventListener('click', load);

async function main() {
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    node.error.hidden = true;
    node.content.hidden = false;
    await load();
  } catch (error) {
    showError(error);
  }
}

mountWorkspace('vocabulary');
main();
