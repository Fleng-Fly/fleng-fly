import { getCurrentUser, setAccessToken } from './api.js';

/**
 * Resolve the current session. `getCurrentUser()` transparently refreshes the
 * access token from the HttpOnly refresh cookie when needed; a failure means
 * there is no valid session.
 */
export async function loadSession() {
  try {
    return await getCurrentUser();
  } catch {
    setAccessToken(null);
    return null;
  }
}

/**
 * Guard a protected page: returns the user, or redirects to the login page and
 * returns `null` when unauthenticated.
 */
export async function requireSession() {
  const user = await loadSession();
  if (!user) {
    window.location.replace('/login.html');
    return null;
  }
  return user;
}
