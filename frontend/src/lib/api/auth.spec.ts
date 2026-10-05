import { afterEach, describe, expect, it, vi } from 'vitest';
import { login, logout, register } from './auth';
import { getMyProgress } from './progress';

interface Call {
  url: string;
  init?: RequestInit;
}

function mockFetch(impl: (url: string, init?: RequestInit) => Promise<Response>): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      return impl(url, init);
    }),
  );
  return calls;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('auth API functions', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('posts credentials to /auth/login', async () => {
    const calls = mockFetch(async () => json({ accessToken: 't', user: { id: '1' } }));

    await login('a@example.com', 'secret123');

    expect(calls[0].url).toMatch(/\/auth\/login$/);
    expect(calls[0].init?.method).toBe('POST');
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      email: 'a@example.com',
      password: 'secret123',
    });
  });

  it('posts the full payload to /auth/register', async () => {
    const calls = mockFetch(async () => json({ accessToken: 't', user: { id: '1' } }, 201));

    await register({ email: 'a@example.com', password: 'secret123', displayName: 'Alex' });

    expect(calls[0].url).toMatch(/\/auth\/register$/);
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      email: 'a@example.com',
      password: 'secret123',
      displayName: 'Alex',
    });
  });

  it('posts to /auth/logout without retrying on 401', async () => {
    const calls = mockFetch(async () => new Response(null, { status: 204 }));

    await logout();

    expect(calls[0].url).toMatch(/\/auth\/logout$/);
    expect(calls[0].init?.method).toBe('POST');
    expect(calls).toHaveLength(1);
  });

  it('gets the current user progress', async () => {
    const calls = mockFetch(async () => json({ userId: 'u1', lessonsCompleted: 0 }));

    await getMyProgress();

    expect(calls[0].url).toMatch(/\/progress\/me$/);
  });
});
