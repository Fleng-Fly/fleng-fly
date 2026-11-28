import { READINGS, READING_LEVELS } from './reading-content.js';
import { gradeReading, restoreReading, PASS_SCORE } from './reading-state.js';
import { el } from './layout.js';
import { t, getLang, applyUserLanguage } from './i18n.js';
import { requireSession } from './session.js';
import { mountWorkspace, setWorkspaceUser } from './workspace.js';
import { catalogMessage } from './catalog-ui.js';
import { describeApiError } from './errors.js';

const $ = id => document.getElementById(id);
const catalog = $('reading-catalog');
const player = $('reading-player');
const search = $('reading-search');
let level = 'All';
let storageKey = null;
let progress = Object.create(null);
let ready = false;
let loading = false;
let storageFailed = false;

function button(label, action, className = 'catalog-button') {
  const node = el('button', className, label);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}
function stateFor(reading) { return restoreReading(reading, progress[reading.id]); }
function store(reading, state) {
  progress[reading.id] = state;
  try { window.localStorage.setItem(storageKey, JSON.stringify(progress)); }
  catch { storageFailed = true; $('reading-storage-warning').hidden = false; }
}
function heading(reading) {
  const title = el('h2', undefined, reading.title);
  title.lang = 'en';
  return title;
}
function showCatalog() {
  const filters = $('reading-filters');
  filters.replaceChildren();
  for (const value of ['All', ...READING_LEVELS]) {
    const filter = button(value === 'All' ? t('courses.all') : value, () => {
      level = value;
      showCatalog();
      filters.querySelector('[aria-pressed="true"]')?.focus();
    }, '');
    filter.setAttribute('aria-pressed', String(level === value));
    filters.append(filter);
  }
  const query = search.value.trim().toLocaleLowerCase();
  const results = READINGS.filter(reading => (level === 'All' || reading.level === level) &&
    `${reading.title} ${reading.titleUk} ${reading.paragraphs.join(' ')}`.toLocaleLowerCase().includes(query));
  const passed = READINGS.filter(reading => (stateFor(reading).best ?? 0) >= PASS_SCORE).length;
  $('reading-count').textContent = t('reading.count', { count: results.length, passed, total: READINGS.length });
  const grid = $('reading-grid');
  grid.replaceChildren();
  if (!results.length) catalogMessage(grid, t('reading.empty'), t('reading.emptyDetail'));
  for (const reading of results) {
    const state = stateFor(reading);
    const card = el('article', 'catalog-panel catalog-card');
    const meta = el('div', 'catalog-card-meta');
    meta.append(el('span', 'catalog-badge', reading.level));
    if (state.best !== null) meta.append(el('span', 'catalog-status', t('reading.best', { score: state.best, total: reading.questions.length })));
    card.append(meta, heading(reading));
    if (getLang() === 'uk') card.append(el('p', 'catalog-description', reading.titleUk));
    const words = reading.paragraphs.join(' ').trim().split(/\s+/).length;
    card.append(el('p', 'catalog-description', t('reading.details', { words, total: reading.questions.length })));
    const link = el('a', 'catalog-button', state.finished ? t('reading.results') : state.answers.some(x => x !== null) ? t('reading.resume') : t('reading.open'));
    link.href = `/reading.html?text=${reading.id}`;
    card.append(link);
    grid.append(card);
  }
}
function showReading(reading) {
  catalog.hidden = true;
  const state = stateFor(reading);
  player.replaceChildren();
  const back = el('a', 'catalog-back', t('reading.back'));
  back.href = '/reading.html';
  player.append(back);
  if (storageFailed) player.append(el('p', 'lesson-fine-print', t('reading.storageWarning')));
  const article = el('article', 'catalog-panel catalog-hero');
  article.append(el('span', 'catalog-badge', reading.level), heading(reading));
  if (getLang() === 'uk') article.append(el('p', 'catalog-description', reading.titleUk));
  const jump = el('a', 'catalog-button', t('reading.test'));
  jump.href = '#reading-test';
  article.append(jump);
  const passage = el('div', 'lesson-question');
  passage.lang = 'en';
  for (const text of reading.paragraphs) passage.append(el('p', undefined, text));
  article.append(passage);
  player.append(article);
  const section = el('section', 'catalog-lessons');
  section.id = 'reading-test';
  section.append(el('h2', undefined, state.finished ? t('reading.results') : t('reading.test')));
  const summary = el('div', 'catalog-panel');
  const status = el('p', 'dashboard-muted');
  status.setAttribute('role', 'status');
  const track = el('div', 'catalog-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', t('reading.test'));
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', String(reading.questions.length));
  const fill = el('span', 'catalog-fill');
  track.append(fill);
  summary.append(status, track);
  section.append(summary);
  const form = el('form', 'lesson-answer-form');
  const list = el('div', 'catalog-lesson-list');
  const submit = el('button', 'lesson-button lesson-button-primary', t('reading.submit'));
  submit.type = 'submit';
  const update = () => {
    const answered = state.answers.filter(value => value !== null).length;
    track.setAttribute('aria-valuenow', String(answered));
    fill.style.width = `${answered / reading.questions.length * 100}%`;
    status.textContent = t('reading.answered', { answered, total: reading.questions.length });
    submit.disabled = answered !== reading.questions.length;
  };
  for (const [index, question] of reading.questions.entries()) {
    const card = el('section', 'lesson-card lesson-question');
    const field = el('fieldset');
    field.disabled = state.finished;
    const legend = el('legend', 'lesson-question-meta', `${index + 1}. ${t(question.type === 'true_false' ? 'reading.trueFalse' : 'reading.choice')}`);
    field.append(legend);
    const prompt = el('h2', undefined, question.prompt);
    prompt.id = `reading-question-${index}`;
    prompt.lang = 'en';
    field.setAttribute('aria-describedby', prompt.id);
    field.append(prompt);
    const options = el('div', 'lesson-options');
    for (const [optionIndex, text] of question.options.entries()) {
      const label = el('label', 'lesson-option');
      if (state.finished && optionIndex === question.answer) label.classList.add('is-correct');
      else if (state.finished && optionIndex === state.answers[index]) label.classList.add('is-incorrect');
      const input = el('input');
      input.type = 'radio';
      input.name = `question-${index}`;
      input.value = String(optionIndex);
      input.checked = state.answers[index] === optionIndex;
      input.addEventListener('change', () => {
        if (state.finished) return;
        state.answers[index] = optionIndex;
        store(reading, state);
        update();
      });
      const option = el('span', 'lesson-option-text', text);
      option.lang = 'en';
      label.append(input, option);
      options.append(label);
    }
    field.append(options);
    card.append(field);
    if (state.finished) {
      const correct = state.answers[index] === question.answer;
      const feedback = el('div', `lesson-feedback ${correct ? 'is-correct' : 'is-incorrect'}`);
      feedback.append(el('strong', undefined, t(correct ? 'reading.correct' : 'reading.incorrect')),
        el('p', undefined, t('reading.answer', { answer: question.options[question.answer] })));
      const evidence = el('p', undefined, question.evidence);
      evidence.lang = 'en';
      feedback.append(el('strong', undefined, t('reading.evidence')), evidence);
      card.append(feedback);
    }
    list.append(card);
  }
  form.append(list);
  const actions = el('div', 'lesson-question-navigation');
  if (state.finished) {
    const grade = gradeReading(reading, state.answers);
    const result = el('div', `lesson-feedback ${grade.passed ? 'is-correct' : 'is-incorrect'}`);
    result.setAttribute('role', 'status');
    result.append(el('strong', undefined, t('reading.score', { score: grade.score, total: grade.total })),
      el('p', undefined, t(grade.passed ? 'reading.passed' : 'reading.notPassed')));
    summary.append(result);
    actions.append(button(t('reading.retry'), () => {
      store(reading, { answers: reading.questions.map(() => null), finished: false, best: state.best });
      showReading(reading);
      player.querySelector('a').focus();
    }, 'lesson-button lesson-button-secondary'));
    const next = READINGS[READINGS.indexOf(reading) + 1];
    if (next) {
      const link = el('a', 'lesson-button lesson-button-primary', t('reading.next'));
      link.href = `/reading.html?text=${next.id}`;
      actions.append(link);
    }
  } else {
    actions.append(el('span', undefined, t('reading.passRule')), submit);
    form.addEventListener('submit', event => {
      event.preventDefault();
      const grade = gradeReading(reading, state.answers);
      if (!grade.complete || state.finished) return;
      state.finished = true;
      state.best = Math.max(state.best ?? 0, grade.score);
      store(reading, state);
      showReading(reading);
      const result = player.querySelector('[role="status"].lesson-feedback');
      result.tabIndex = -1;
      result.focus();
    });
  }
  form.append(actions);
  section.append(form);
  player.append(section);
  update();
}
function render() {
  if (!ready) return;
  const id = new URLSearchParams(window.location.search).get('text');
  const reading = READINGS.find(item => item.id === id);
  if (reading) showReading(reading);
  else {
    player.replaceChildren();
    catalog.hidden = false;
    if (id) catalogMessage(player, t('reading.notFound'), t('reading.emptyDetail'));
    showCatalog();
  }
}
async function init() {
  if (loading) return;
  loading = true;
  ready = false;
  catalog.hidden = true;
  player.setAttribute('aria-busy', 'true');
  catalogMessage(player, t('reading.loading'), '');
  try {
    const user = await requireSession({ throwOnUnavailable: true });
    if (!user) return;
    await applyUserLanguage(user);
    setWorkspaceUser(user);
    storageKey = `fleng.reading.v2:${user.id}`;
    storageFailed = false;
    progress = Object.create(null);
    try {
      const raw = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
      for (const reading of READINGS) if (raw && Object.hasOwn(raw, reading.id)) progress[reading.id] = restoreReading(reading, raw[reading.id]);
    } catch { storageFailed = true; }
    $('reading-storage-warning').hidden = !storageFailed;
    ready = true;
    render();
  } catch (error) {
    catalogMessage(player, t('reading.loadFailed'), describeApiError(error), init);
  } finally {
    loading = false;
    player.setAttribute('aria-busy', 'false');
  }
}
mountWorkspace('reading');
search.addEventListener('input', showCatalog);
window.addEventListener('fleng:language-changed', render);
window.addEventListener('pageshow', event => { if (event.persisted) init(); });
init();
