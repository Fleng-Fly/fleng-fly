import { getCurrentUser, setAccessToken } from './api.js';

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
