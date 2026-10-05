import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch, getAccessToken, setAccessToken } from './client';

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

function mockFetch(impl: (url: string, init?: RequestInit) => Promise<Response>): void {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => impl(String(input), init)),
  );
}

describe('apiFetch', () => {
  afterEach(() => {
    setAccessToken(null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('returns parsed JSON on success', async () => {
    mockFetch(async () => json({ status: 'ok' }));

    await expect(apiFetch('/health')).resolves.toEqual({ status: 'ok' });
  });

  it('throws an ApiError carrying the backend code on HTTP errors', async () => {
    mockFetch(async () =>
      json({ error: { code: 'DATABASE_UNAVAILABLE', message: 'Database is unavailable' } }, 503),
    );

    const error = await apiFetch('/users/me').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 503, code: 'DATABASE_UNAVAILABLE' });
  });

  it('throws NETWORK_ERROR when the backend is unreachable', async () => {
    mockFetch(async () => {
      throw new Error('connection refused');
    });

    await expect(apiFetch('/health')).rejects.toMatchObject({ status: 0, code: 'NETWORK_ERROR' });
  });

  it('throws INVALID_RESPONSE when the body is not JSON', async () => {
    mockFetch(async () => new Response('not json', { status: 200 }));

    await expect(apiFetch('/health')).rejects.toMatchObject({ code: 'INVALID_RESPONSE' });
  });

  it('returns undefined for a 204 response', async () => {
    mockFetch(async () => new Response(null, { status: 204 }));

    await expect(apiFetch('/auth/logout')).resolves.toBeUndefined();
  });

  it('attaches the access token as a Bearer header', async () => {
    let captured: RequestInit | undefined;
    mockFetch(async (_url, init) => {
      captured = init;
      return json({ ok: true });
    });

    setAccessToken('access-123');
    await apiFetch('/users/me');

    const headers = captured?.headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer access-123');
    expect(captured?.credentials).toBe('include');
  });

  it('refreshes once and retries a request after a 401', async () => {
    let protectedAttempts = 0;
    const authHeaders: Array<string | undefined> = [];
    mockFetch(async (url, init) => {
      if (url.endsWith('/auth/refresh')) {
        return json({ accessToken: 'fresh-token' });
      }
      protectedAttempts += 1;
      authHeaders.push((init?.headers as Record<string, string> | undefined)?.Authorization);
      if (protectedAttempts === 1) {
        return json({ error: { code: 'UNAUTHORIZED', message: 'expired' } }, 401);
      }
      return json({ id: 'user-1' });
    });

    setAccessToken('expired-token');
    await expect(apiFetch('/users/me')).resolves.toEqual({ id: 'user-1' });

    expect(protectedAttempts).toBe(2);
    expect(authHeaders[0]).toBe('Bearer expired-token');
    expect(authHeaders[1]).toBe('Bearer fresh-token');
    expect(getAccessToken()).toBe('fresh-token');
  });

  it('clears the token and surfaces the 401 when refresh fails', async () => {
    mockFetch(async (url) =>
      url.endsWith('/auth/refresh')
        ? json({ error: { code: 'INVALID_REFRESH_TOKEN' } }, 401)
        : json({ error: { code: 'UNAUTHORIZED', message: 'expired' } }, 401),
    );

    setAccessToken('expired-token');
    await expect(apiFetch('/users/me')).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBeNull();
  });
});
