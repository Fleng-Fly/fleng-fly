import { getAuthProviders, getCurrentUser, setAccessToken } from './api.js';
import { t } from './i18n.js';

/**
 * Resolve the current session. `getCurrentUser()` transparently refreshes the
 * access token from the HttpOnly refresh cookie when needed. Dashboard can
 * request distinct network/service errors instead of treating them as logout.
 */
export async function loadSession({ throwOnUnavailable = false } = {}) {
  try {
    return await getCurrentUser();
  } catch (error) {
    if (throwOnUnavailable && error?.status !== 401) throw error;
    setAccessToken(null);
    return null;
  }
}

/**
 * Guard a protected page: returns the user, or redirects to the login page and
 * returns `null` when unauthenticated.
 */
export async function requireSession(options) {
  const user = await loadSession(options);
  if (!user) {
    window.location.replace('/login.html');
    return null;
  }
  return user;
}

/**
 * Entry pages (landing, login, register): send a signed-in learner straight to the
 * dashboard. Resolves to the user when a redirect is under way, otherwise to `null`
 * after revealing the page.
 */
export async function redirectIfSignedIn() {
  const user = await loadSession();
  if (user) {
    window.location.replace('/dashboard.html');
    return user;
  }
  document.documentElement.classList.remove('session-pending');
  return null;
}

const GOOGLE_ERRORS = {
  google_denied: 'auth.googleDenied',
  google_unverified: 'auth.googleUnverified',
  google_unavailable: 'auth.googleUnavailable',
  google_rate_limited: 'errors.429',
};

/**
 * Login/register pages: reveal the Google button only when the server has Google
 * configured, and show why a previous Google attempt (`?error=google_*`) failed.
 * Returns the message to display, or an empty string.
 */
export async function setupGoogleSignIn() {
  try {
    const providers = await getAuthProviders();
    if (providers?.google) document.getElementById('google-block')?.classList.remove('hidden');
  } catch {
    /* Providers unavailable: email/password sign-in still works. */
  }
  const code = new URLSearchParams(window.location.search).get('error');
  if (!code || !code.startsWith('google_')) return '';
  return t(GOOGLE_ERRORS[code] ?? 'auth.googleFailed');
}
