import { getCurrentUser, getHealth, logout as logoutRequest, setAccessToken } from './api.js';

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
    const retry = el('button', 'btn btn-secondary', 'Try again');
    retry.type = 'button';
    retry.addEventListener('click', onRetry);
    card.append(retry);
  }
  container.append(card);
}

const NAV_ITEMS = [
  { href: '/index.html', label: 'Home', key: 'home' },
  { href: '/courses.html', label: 'Courses', key: 'courses' },
  { href: '/dashboard.html', label: 'Dashboard', key: 'dashboard' },
];

/**
 * Render the shared header. When `user` is omitted the session is resolved here;
 * pass a resolved user (e.g. from `requireSession()`) to avoid a second request.
 */
export async function mountHeader(active = '', user) {
  const header = document.getElementById('site-header');
  if (!header) return user;

  header.textContent = '';
  const inner = el('div', 'container header-inner');

  const brand = el('a', 'brand');
  brand.href = '/index.html';
  brand.append(el('span', 'brand-mark', 'F'), el('span', 'brand-name', 'Fleng'));

  const nav = el('nav', 'nav');
  for (const item of NAV_ITEMS) {
    const link = el('a', undefined, item.label);
    link.href = item.href;
    if (item.key === active) link.className = 'active';
    nav.append(link);
  }

  const authArea = el('div', 'auth-area');
  authArea.append(el('span', 'muted', '…'));
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

  authArea.textContent = '';
  if (current) {
    authArea.append(el('span', 'user-name', current.displayName));
    const button = el('button', 'btn btn-ghost btn-sm', 'Log out');
    button.type = 'button';
    button.addEventListener('click', async () => {
      try {
        await logoutRequest();
      } finally {
        setAccessToken(null);
        window.location.href = '/index.html';
      }
    });
    authArea.append(button);
  } else {
    const link = el('a', 'btn btn-ghost btn-sm', 'Log in');
    link.href = '/login.html';
    authArea.append(link);
  }

  return current;
}

/** Render the live backend status badge from GET /api/v1/health. */
export function mountBackendStatus(containerId = 'backend-status') {
  const target = document.getElementById(containerId);
  if (!target) return;

  const check = async () => {
    target.textContent = '';
    target.append(el('span', 'muted text-sm', 'Backend'));
    try {
      const health = await getHealth();
      const badge = el('span', 'badge badge-success', `● Online · db ${health.database}`);
      target.append(badge);
    } catch {
      target.append(el('span', 'badge badge-danger', '● Offline'));
    }
  };

  check();
  window.setInterval(check, 15000);
}
