import {
  getReadingPreferences,
  listReadingArticles,
  listReadingCategories,
  setReadingPreferences,
} from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';
import { t } from './i18n.js';
import { LEVELS, bookmarkButton, levelBadge, minutesText, progressText } from './reading-ui.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';

const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 12;
const MAX_TOPIC_REQUESTS = 10;
const STATUSES = [
  ['', 'rd.sAll'],
  ['new', 'rd.sNew'],
  ['in_progress', 'rd.sInProgress'],
  ['completed', 'rd.sDone'],
];

const state = {
  categories: [],
  preferred: new Set(),
  filters: { topic: '', level: '', status: '', saved: false },
  items: [],
  total: 0,
  offset: 0,
  paged: true,
  request: 0,
  ready: false,
};

const hasFilters = () =>
  Boolean(
    state.filters.topic || state.filters.level || state.filters.status || state.filters.saved,
  );

function chip(label, pressed, onClick) {
  const button = el('button', undefined, label);
  button.type = 'button';
  button.setAttribute('aria-pressed', String(pressed));
  button.addEventListener('click', onClick);
  return button;
}

function setFilter(patch) {
  Object.assign(state.filters, patch);
  renderFilters();
  void loadArticles({ reset: true });
}

function renderFilters() {
  const { topic, level, status, saved } = state.filters;
  const ordered = [...state.categories].sort(
    (a, b) => Number(state.preferred.has(b.id)) - Number(state.preferred.has(a.id)),
  );
  const topics = [chip(t('rd.allTopics'), topic === '', () => setFilter({ topic: '' }))];
  if (state.preferred.size)
    topics.push(
      chip(`★ ${t('rd.myTopics')}`, topic === 'mine', () => setFilter({ topic: 'mine' })),
    );
  for (const category of ordered) {
    const label = `${state.preferred.has(category.id) ? '★ ' : ''}${category.title}`;
    topics.push(chip(label, topic === category.id, () => setFilter({ topic: category.id })));
  }
  $('filter-topic').replaceChildren(...topics);
  $('filter-level').replaceChildren(
    chip(t('rd.allLevels'), level === '', () => setFilter({ level: '' })),
    ...LEVELS.map((value) => chip(value, level === value, () => setFilter({ level: value }))),
  );
  $('filter-status').replaceChildren(
    ...STATUSES.map(([value, key]) =>
      chip(t(key), status === value, () => setFilter({ status: value })),
    ),
    chip(`★ ${t('rd.saved')}`, saved, () => setFilter({ saved: !saved })),
  );
}

function feedback(text = '', isError = false) {
  $('reading-feedback').textContent = text;
  $('reading-feedback').classList.toggle('is-error', isError);
}

function card(article) {
  const node = el('article', 'reading-card dashboard-card');
  const href = `/reading-article.html?slug=${encodeURIComponent(article.slug)}`;
  if (article.coverImageUrl) {
    const image = el('img', 'reading-cover');
    image.src = article.coverImageUrl;
    image.alt = article.coverAlt || '';
    image.loading = 'lazy';
    node.append(image);
  }
  const body = el('div', 'reading-card-body');
  const meta = el('div', 'reading-meta');
  meta.append(
    levelBadge(article.level),
    el('span', undefined, minutesText(article.readingMinutes)),
    el('span', undefined, article.category.title),
  );
  const title = el('h2', 'reading-card-title');
  const link = el('a', undefined, article.title);
  link.href = href;
  title.append(link);
  body.append(meta, title, el('p', 'dashboard-muted', article.description));

  const status = progressText(article.progress);
  if (status) {
    const row = el(
      'p',
      `reading-status${article.progress.status === 'completed' ? ' is-done' : ''}`,
      status,
    );
    if (article.progress.bestScorePercent != null) {
      row.append(
        el('span', undefined, ` · ${t('rd.best', { score: article.progress.bestScorePercent })}`),
      );
    }
    body.append(row);
  }

  const actions = el('div', 'reading-actions');
  const done = article.progress?.status === 'completed';
  const started = article.progress?.readPercent > 0;
  const open = el(
    'a',
    'lesson-button lesson-button-primary',
    done
      ? t('rd.readAgain')
      : started
        ? t('rd.continue', { percent: article.progress.readPercent })
        : t('rd.start'),
  );
  open.href = href;
  actions.append(
    open,
    bookmarkButton(article, {
      onChange: (on) => {
        feedback();
        if (!on && state.filters.saved) {
          state.items = state.items.filter((item) => item.id !== article.id);
          state.total = Math.max(0, state.total - 1);
          render();
        }
      },
      onError: (message) => feedback(message, true),
    }),
  );
  node.append(body, actions);
  return node;
}

function showEmpty(title, text, clearable) {
  $('reading-empty-title').textContent = title;
  $('reading-empty-text').textContent = text;
  $('reading-clear').hidden = !clearable;
  $('reading-empty').hidden = false;
}

function render() {
  $('reading-loading').hidden = true;
  $('reading-empty').hidden = true;
  $('reading-list').hidden = !state.items.length;
  $('reading-list').replaceChildren(...state.items.map(card));
  const more = state.paged && state.items.length < state.total;
  $('reading-more').hidden = !state.items.length || (!more && state.total <= PAGE_SIZE);
  $('reading-load-more').hidden = !more;
  $('reading-count').textContent = state.paged
    ? t('rd.showing', { shown: state.items.length, total: state.total })
    : t('rd.topicsMerged');
  if (!state.items.length) {
    if (state.filters.topic === 'mine' && !state.preferred.size)
      showEmpty(t('rd.noPreferences'), t('rd.topicsHint'), true);
    else if (hasFilters()) showEmpty(t('rd.noMatchTitle'), t('rd.noMatchText'), true);
    else showEmpty(t('rd.emptyTitle'), t('rd.emptyText'), false);
  }
}

function showError(message) {
  $('reading-loading').hidden = true;
  $('reading-error-text').textContent = message;
  $('reading-error').hidden = false;
}

function query(extra = {}) {
  const { topic, level, status, saved } = state.filters;
  return {
    categoryId: topic && topic !== 'mine' ? topic : undefined,
    level: level || undefined,
    progress: status || undefined,
    bookmarked: saved ? true : undefined,
    ...extra,
  };
}

async function loadArticles({ reset }) {
  const request = ++state.request;
  $('reading-error').hidden = true;
  feedback();
  if (reset) {
    state.items = [];
    state.offset = 0;
    $('reading-list').hidden = true;
    $('reading-more').hidden = true;
    $('reading-empty').hidden = true;
    $('reading-loading').hidden = false;
  }
  $('reading-load-more').disabled = true;
  try {
    if (state.filters.topic === 'mine') {
      state.paged = false;
      const ids = [...state.preferred].slice(0, MAX_TOPIC_REQUESTS);
      const pages = await Promise.all(
        ids.map((categoryId) =>
          listReadingArticles(query({ categoryId, limit: PAGE_SIZE, offset: 0 })),
        ),
      );
      if (request !== state.request) return;
      state.items = pages
        .flatMap((page) => page.items)
        .sort((a, b) => String(b.publishedAt).localeCompare(String(a.publishedAt)));
      state.total = state.items.length;
    } else {
      state.paged = true;
      const page = await listReadingArticles(query({ limit: PAGE_SIZE, offset: state.offset }));
      if (request !== state.request) return;
      state.items = reset ? page.items : [...state.items, ...page.items];
      state.total = page.total;
      state.offset = state.items.length;
    }
    render();
  } catch (error) {
    if (request !== state.request) return;
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    showError(describeApiError(error));
  } finally {
    $('reading-load-more').disabled = false;
  }
}

function openTopics() {
  const box = $('topics-options');
  $('topics-status').textContent = '';
  $('topics-status').classList.remove('is-error');
  if (!state.categories.length) {
    box.replaceChildren(el('p', 'dashboard-muted', t('rd.topicsNone')));
  } else {
    box.replaceChildren(
      ...state.categories.map((category) => {
        const label = el('label', 'lesson-option');
        const input = el('input');
        input.type = 'checkbox';
        input.value = category.id;
        input.checked = state.preferred.has(category.id);
        label.append(input, el('span', undefined, category.title));
        return label;
      }),
    );
  }
  $('topics-save').disabled = !state.categories.length;
  $('topics-dialog').showModal();
}

async function saveTopics(event) {
  event.preventDefault();
  const ids = [...$('topics-options').querySelectorAll('input:checked')].map(
    (input) => input.value,
  );
  $('topics-save').disabled = true;
  try {
    const saved = await setReadingPreferences(ids);
    state.preferred = new Set(saved.categories.map((category) => category.id));
    if (state.filters.topic === 'mine' && !state.preferred.size) state.filters.topic = '';
    $('topics-dialog').close();
    renderFilters();
    if (state.filters.topic === 'mine') void loadArticles({ reset: true });
    feedback(t('rd.topicsSaved'));
  } catch (error) {
    $('topics-status').textContent = error.status ? describeApiError(error) : t('rd.topicsFailed');
    $('topics-status').classList.add('is-error');
  } finally {
    $('topics-save').disabled = false;
  }
}

async function init() {
  $('reading-error').hidden = true;
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    setWorkspaceUser(user);
    const [categories, preferences] = await Promise.all([
      listReadingCategories(),
      getReadingPreferences().catch(() => ({ categories: [] })), // preferences are optional
    ]);
    state.categories = categories;
    state.preferred = new Set(preferences.categories.map((category) => category.id));
    state.ready = true;
    renderFilters();
    $('reading-filters').hidden = false;
    $('topics-open').disabled = false; // needs the category list
    await loadArticles({ reset: true });
  } catch (error) {
    if (error.status === 401) {
      window.location.replace('/login.html');
      return;
    }
    showError(describeApiError(error));
  }
}

$('reading-retry').addEventListener('click', () => {
  if (state.ready) void loadArticles({ reset: true });
  else void init();
});
$('reading-load-more').addEventListener('click', () => void loadArticles({ reset: false }));
$('reading-clear').addEventListener('click', () => {
  state.filters = { topic: '', level: '', status: '', saved: false };
  renderFilters();
  void loadArticles({ reset: true });
});
$('topics-open').addEventListener('click', openTopics);
$('topics-close').addEventListener('click', () => $('topics-dialog').close());
$('topics-form').addEventListener('submit', saveTopics);

mountWorkspace('reading');
void init();
