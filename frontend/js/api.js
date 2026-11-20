/**
 * Centralised API client (vanilla JS). Mirrors the previous TypeScript client:
 * all HTTP concerns live here and page scripts only call these functions.
 *
 * Auth model:
 * - The access token lives in a module variable (memory only), never in
 *   localStorage/sessionStorage.
 * - The refresh token is an HttpOnly cookie the browser sends automatically
 *   (`credentials: 'include'`).
 * - On a 401 the client attempts one refresh and retries the request once;
 *   concurrent refreshes are de-duplicated.
 */

/** Same origin as the page: the backend serves this static frontend. */
export const API_BASE = '/api/v1';

let accessToken = null;

/**
 * A non-secret "this browser probably has a session" hint. It only lets the landing
 * and login pages hold back their content while the session is being restored, so a
 * signed-in learner never sees a login screen flash. The refresh cookie stays the
 * only credential.
 */
const SESSION_HINT_KEY = 'fleng.session.hint';
function rememberSession(active) {
  try {
    if (active) localStorage.setItem(SESSION_HINT_KEY, '1');
    else localStorage.removeItem(SESSION_HINT_KEY);
  } catch {
    /* Storage unavailable: only the loading polish is lost. */
  }
}

export function setAccessToken(token) {
  accessToken = token;
  rememberSession(Boolean(token));
  if (token === null && typeof window !== 'undefined') {
    window.dispatchEvent(new Event('fleng:session-ended'));
  }
}

export function getAccessToken() {
  return accessToken;
}

export class ApiError extends Error {
  constructor(message, status, code, details) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function refreshAccessToken() {
  let response;
  try {
    response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    });
  } catch {
    throw new ApiError('Unable to reach the backend', 0, 'NETWORK_ERROR');
  }
  if (response.status === 401) {
    setAccessToken(null);
    return null;
  }
  if (!response.ok) {
    throw new ApiError('Unable to restore your session', response.status, 'SESSION_UNAVAILABLE');
  }
  let body;
  try {
    body = await response.json();
  } catch {
    throw new ApiError('Backend returned an invalid response', response.status, 'INVALID_RESPONSE');
  }
  if (!body.accessToken) {
    throw new ApiError('Backend returned an invalid response', response.status, 'INVALID_RESPONSE');
  }
  accessToken = body.accessToken;
  rememberSession(true);
  return accessToken;
}

let refreshInFlight = null;

// Serialize cookie mutations across same-origin tabs. Each refresh reads the
// current HttpOnly cookie only after the previous response has updated it.
function withSessionLock(action) {
  const locks = globalThis.navigator?.locks;
  if (locks?.request) return locks.request('fleng.auth-cookie', { mode: 'exclusive' }, action);
  return action();
}

function refreshOnce() {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      if (!globalThis.navigator?.locks?.request) {
        setAccessToken(null);
        return null;
      }
      let entered = false;
      try {
        return await withSessionLock(() => {
          entered = true;
          return refreshAccessToken();
        });
      } catch (error) {
        if (entered) throw error;
        setAccessToken(null);
        return null;
      }
    })().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export async function apiFetch(path, init = {}, options = {}) {
  const retryOnUnauthorized = options.retryOnUnauthorized ?? true;
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
  const headers = {
    Accept: 'application/json',
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(init.headers ?? {}),
  };

  let response;
  try {
    response = await fetch(url, {
      ...init,
      cache: 'no-store',
      credentials: 'include',
      headers,
    });
  } catch {
    throw new ApiError('Unable to reach the backend', 0, 'NETWORK_ERROR');
  }

  if (response.status === 401 && retryOnUnauthorized && !path.startsWith('/auth/')) {
    const token = await refreshOnce();
    if (token) {
      return apiFetch(path, init, { ...options, retryOnUnauthorized: false });
    }
  }

  if (!response.ok) {
    let code = 'HTTP_ERROR';
    let message = `Request failed with status ${response.status}`;
    let details;
    try {
      const body = await response.json();
      if (body.error?.code) code = body.error.code;
      if (body.error?.message) message = body.error.message;
      details = body.error?.details;
    } catch {
      // Non-JSON error body: keep the defaults above.
    }
    throw new ApiError(message, response.status, code, details);
  }

  if (options.rawResponse) return response;

  if (response.status === 204) {
    return undefined;
  }

  try {
    return await response.json();
  } catch {
    throw new ApiError('Backend returned an invalid response', response.status, 'INVALID_RESPONSE');
  }
}

/* ── Endpoint helpers ───────────────────────────────────────────────── */

export function register(input) {
  return withSessionLock(() => apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(input) }, { retryOnUnauthorized: false }));
}

export function login(email, password) {
  return withSessionLock(() => apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }, { retryOnUnauthorized: false }));
}

export function getAuthProviders() {
  return apiFetch('/auth/providers', {}, { retryOnUnauthorized: false });
}

export async function logout() {
  await withSessionLock(() => apiFetch('/auth/logout', { method: 'POST' }, { retryOnUnauthorized: false }));
  setAccessToken(null);
  try {
    localStorage.setItem('fleng.session.logout', crypto.randomUUID());
  } catch {
    /* Cross-tab notification is optional. */
  }
}

export function getCurrentUser() {
  return apiFetch('/users/me');
}

export function updateCurrentUser(input) {
  return apiFetch('/users/me', { method: 'PATCH', body: JSON.stringify(input) });
}

export function changePassword(input) {
  return apiFetch('/users/me/password', { method: 'POST', body: JSON.stringify(input) });
}

export function getIdentities() {
  return apiFetch('/auth/identities');
}

/** Re-authenticate with the account password; resolves to `{ url }`, Google's consent page. */
export function startGoogleLink(password) {
  return apiFetch('/auth/google/link', { method: 'POST', body: JSON.stringify({ password }) });
}

export function requestPasswordReset(email) {
  return apiFetch('/auth/password-reset/request', {
    method: 'POST', body: JSON.stringify({ email }),
  }, { retryOnUnauthorized: false });
}

export function confirmPasswordReset(token, password) {
  return apiFetch('/auth/password-reset/confirm', {
    method: 'POST', body: JSON.stringify({ token, password }),
  }, { retryOnUnauthorized: false });
}

export function getMyProgress() {
  return apiFetch('/progress/me');
}

export function getDailyGoals() {
  return apiFetch('/progress/daily');
}

export function getMyStreak() {
  return apiFetch('/streaks/me');
}

export function getVocabularyStats() {
  return apiFetch('/vocabulary/stats');
}

export function listVocabulary(offset = 0, limit = 100) {
  return apiFetch(`/vocabulary?${new URLSearchParams({ offset: String(offset), limit: String(limit) })}`);
}

export function getVocabularyGroups() {
  return apiFetch('/vocabulary/groups');
}

export function addVocabulary(input) {
  return apiFetch('/vocabulary', { method: 'POST', body: JSON.stringify(input) });
}

export function reviewVocabulary(id, remembered) {
  return apiFetch(`/vocabulary/${encodeURIComponent(id)}/review`, {
    method: 'POST', body: JSON.stringify({ remembered }),
  });
}

export function updateVocabulary(id, learned) {
  return apiFetch(`/vocabulary/${encodeURIComponent(id)}`, {
    method: 'PATCH', body: JSON.stringify({ learned }),
  });
}

export function deleteVocabulary(id) {
  return apiFetch(`/vocabulary/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function getLessonVocabulary(lessonId, offset = 0, limit = 30) {
  const query = new URLSearchParams({ lessonId, offset: String(offset), limit: String(limit) });
  return apiFetch(`/vocabulary?${query}`);
}

export function getHealth() {
  return apiFetch('/health');
}

export function listCourses() {
  return apiFetch('/courses');
}

export function getCourse(slug) {
  return apiFetch(`/courses/${encodeURIComponent(slug)}`);
}

export function getLesson(slug) {
  return apiFetch(`/lessons/${encodeURIComponent(slug)}`);
}

export function startLesson(slug) {
  return apiFetch(`/lessons/${encodeURIComponent(slug)}/start`, { method: 'POST' });
}

export function getLessonProgress(slug) {
  return apiFetch(`/lessons/${encodeURIComponent(slug)}/progress`);
}

export function submitAnswer(slug, payload) {
  return apiFetch(`/lessons/${encodeURIComponent(slug)}/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getAIStatus() {
  return apiFetch('/ai/status');
}
export function listAIConversations() {
  return apiFetch('/ai/conversations?limit=100');
}
export function getAIHistory(id, offset = 0) {
  return apiFetch(`/ai/conversations/${encodeURIComponent(id)}?limit=100&offset=${offset}`);
}
export function streamAIChat(payload, { signal } = {}) {
  return apiFetch(
    '/ai/chat/stream',
    {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { Accept: 'text/event-stream' },
      signal,
    },
    { rawResponse: true },
  );
}

export function getLeaderboard() {
  return apiFetch('/leaderboard');
}

export function requestEmailChange(input) {
  return apiFetch('/users/me/email-change/request', { method: 'POST', body: JSON.stringify(input) });
}
export function confirmEmailChange(token) {
  return apiFetch('/users/me/email-change/confirm', { method: 'POST', body: JSON.stringify({ token }) }, { retryOnUnauthorized: false });
}

export function listCourseWords(courseId = '', offset = 0, limit = 100) {
  const query = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  if (courseId) query.set('courseId', courseId);
  return apiFetch(`/vocabulary/course-words?${query}`);
}
