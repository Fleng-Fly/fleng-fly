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

export function setAccessToken(token) {
  accessToken = token;
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
    accessToken = null;
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
  return accessToken;
}

let refreshInFlight = null;

function refreshOnce() {
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => {
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
      return apiFetch(path, init, { retryOnUnauthorized: false });
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
  return apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(input) });
}

export function login(email, password) {
  return apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function logout() {
  return apiFetch('/auth/logout', { method: 'POST' }, { retryOnUnauthorized: false });
}

export function getCurrentUser() {
  return apiFetch('/users/me');
}

export function getMyProgress() {
  return apiFetch('/progress/me');
}

export function getMyStreak() {
  return apiFetch('/streaks/me');
}

export function getVocabularyStats() {
  return apiFetch('/vocabulary/stats');
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
