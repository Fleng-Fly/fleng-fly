import { getCurrentUser, logout as logoutRequest, setAccessToken } from './api.js';
import { applyUserLanguage, createLanguageSwitch, t } from './i18n.js';

/** Small DOM helper: create an element with text content (never innerHTML). */
export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Read a query-string parameter (e.g. `?slug=...`). */
export function queryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

/**
 * Render a card with a heading and message into `container`, optionally with a
 * retry button. Used for loading, empty and error states.
 */
export function renderMessage(container, title, message, onRetry) {
  container.textContent = '';
  const card = el('div', 'card');
  if (title) card.append(el('h3', undefined, title));
  if (message) card.append(el('p', 'muted text-sm', message));
  if (onRetry) {
    const retry = el('button', 'btn btn-secondary', t('common.tryAgain'));
    retry.type = 'button';
    retry.addEventListener('click', onRetry);
    card.append(retry);
  }
  container.append(card);
}

const NAV_ITEMS = [
  { href: '/index.html', key: 'home', label: 'nav.home', signedInOnly: false, guestOnly: true },
  { href: '/courses.html', key: 'courses', label: 'nav.courses', signedInOnly: true },
  { href: '/dashboard.html', key: 'dashboard', label: 'nav.dashboard', signedInOnly: true },
];

/**
 * Render the shared public header. When `user` is omitted the session is resolved here;
 * pass a resolved user (e.g. from `requireSession()`) to avoid a second request.
 * Signed-out visitors only see links they can use (no pages that bounce to login).
 */
export async function mountHeader(active = '', user) {
  const header = document.getElementById('site-header');
  if (!header) return user;

  header.textContent = '';
  const inner = el('div', 'container header-inner');

  const brand = el('a', 'brand');
  brand.href = '/index.html';
  brand.append(el('span', 'brand-mark', '✦'), el('span', 'brand-name', 'Fleng'));

  const nav = el('nav', 'nav');
  nav.dataset.i18nAttr = 'aria-label:nav.main';
  nav.setAttribute('aria-label', t('nav.main'));
  const authArea = el('div', 'auth-area');
  let signedIn = false;
  authArea.append(createLanguageSwitch(() => signedIn));
  inner.append(brand, nav, authArea);
  header.append(inner);

  let current = user;
  if (current === undefined) {
    try {
      current = await getCurrentUser();
    } catch {
      current = null;
    }
  }
  signedIn = Boolean(current);
  // The logo leads to the learner's home: the dashboard when signed in.
  if (current) brand.href = '/dashboard.html';
  if (current) await applyUserLanguage(current);

  for (const item of NAV_ITEMS) {
    if ((item.signedInOnly && !current) || (item.guestOnly && current)) continue;
    const link = el('a', undefined, t(item.label));
    link.dataset.i18n = item.label;
    link.href = item.href;
    if (item.key === active) {
      link.className = 'active';
      link.setAttribute('aria-current', 'page');
    }
    nav.append(link);
  }

  if (current) {
    const name = el('span', 'user-name', current.displayName);
    const button = el('button', 'btn btn-ghost btn-sm', t('auth.logout'));
    button.dataset.i18n = 'auth.logout';
    button.type = 'button';
    const logoutError = el('p', 'alert alert-error hidden');
    logoutError.setAttribute('role', 'alert');
    button.addEventListener('click', async () => {
      button.disabled = true;
      logoutError.classList.add('hidden');
      try {
        await logoutRequest();
        setAccessToken(null);
        window.location.href = '/index.html';
      } catch {
        logoutError.textContent = t('auth.logoutFailed');
        logoutError.classList.remove('hidden');
        button.disabled = false;
      }
    });
    authArea.append(name, button, logoutError);
  } else {
    const login = el('a', 'btn btn-ghost btn-sm', t('auth.login'));
    login.dataset.i18n = 'auth.login';
    login.href = '/login.html';
    const signup = el('a', 'btn btn-primary btn-sm', t('auth.signup'));
    signup.dataset.i18n = 'auth.signup';
    signup.href = '/register.html';
    authArea.append(login, signup);
  }

  return current;
}
