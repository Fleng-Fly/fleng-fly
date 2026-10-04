/**
 * Minimal typed API client. All HTTP concerns live here; feature components
 * only call the small functions in this folder.
 */

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001/api/v1'
).replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface ApiErrorBody {
  error?: { code?: string; message?: string };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError('Unable to reach the backend', 0, 'NETWORK_ERROR');
  }

  if (!response.ok) {
    let code = 'HTTP_ERROR';
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body.error?.code) code = body.error.code;
      if (body.error?.message) message = body.error.message;
    } catch {
      // Non-JSON error body: keep the defaults above.
    }
    throw new ApiError(message, response.status, code);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError('Backend returned an invalid response', response.status, 'INVALID_RESPONSE');
  }
}
