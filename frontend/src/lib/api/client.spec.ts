import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from './client';

function mockFetch(impl: () => Promise<Response>): void {
  vi.stubGlobal('fetch', vi.fn(impl));
}

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('returns parsed JSON on success', async () => {
    mockFetch(async () =>
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    );

    await expect(apiFetch('/health')).resolves.toEqual({ status: 'ok' });
  });

  it('throws an ApiError carrying the backend code on HTTP errors', async () => {
    mockFetch(async () =>
      new Response(
        JSON.stringify({ error: { code: 'DATABASE_UNAVAILABLE', message: 'Database is unavailable' } }),
        { status: 503, headers: { 'content-type': 'application/json' } },
      ),
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
});
