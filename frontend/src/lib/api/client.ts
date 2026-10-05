/**
 * Centralised typed API client. All HTTP concerns live here; feature modules
 * only call the small functions in this folder.
 *
 * Auth model (see docs/authentication.md):
 * - The access token lives in memory only (never localStorage).
 * - The refresh token is an HttpOnly cookie the browser sends automatically.
 * - On a 401 the client attempts one refresh and retries the request once.
 */

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001/api/v1'
).replace(/\/+$/, '');

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface ApiErrorBody {
  error?: { code?: string; message?: string; details?: unknown };
}

interface RequestOptions {
  /** Retry once after a successful refresh on 401. Defaults to true. */
  retryOnUnauthorized?: boolean;
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
      accessToken = null;
      return null;
    }
    const body = (await response.json()) as { accessToken?: string };
    if (!body.accessToken) {
      accessToken = null;
      return null;
    }
    accessToken = body.accessToken;
    return accessToken;
  } catch {
    accessToken = null;
    return null;
  }
}

let refreshInFlight: Promise<string | null> | null = null;

function refreshOnce(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
  options?: RequestOptions,
): Promise<T> {
  const retryOnUnauthorized = options?.retryOnUnauthorized ?? true;
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...((init?.headers as Record<string, string> | undefined) ?? {}),
  };

  let response: Response;
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

  if (
    response.status === 401 &&
    retryOnUnauthorized &&
    !path.startsWith('/auth/')
  ) {
    const token = await refreshOnce();
    if (token) {
      return apiFetch<T>(path, init, { retryOnUnauthorized: false });
    }
  }

  if (!response.ok) {
    let code = 'HTTP_ERROR';
    let message = `Request failed with status ${response.status}`;
    let details: unknown;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body.error?.code) code = body.error.code;
      if (body.error?.message) message = body.error.message;
      details = body.error?.details;
    } catch {
      // Non-JSON error body: keep the defaults above.
    }
    throw new ApiError(message, response.status, code, details);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError('Backend returned an invalid response', response.status, 'INVALID_RESPONSE');
  }
}
