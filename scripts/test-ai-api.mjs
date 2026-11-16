import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
const source = await readFile(new URL('../frontend/js/api.js', import.meta.url), 'utf8');
const api = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('streaming preserves raw response after one auth refresh', async () => {
  const original = globalThis.fetch;
  const calls = [];
  const stream = new Response('event: done\ndata: {}\n\n', {
    headers: { 'Content-Type': 'text/event-stream' },
  });
  try {
    api.setAccessToken('expired-test-token');
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      if (calls.length === 1) return new Response('{}', { status: 401 });
      if (calls.length === 2) return Response.json({ accessToken: 'renewed-test-token' });
      return stream;
    };
    const result = await api.streamAIChat({ message: 'Why does she go?', requestId: 'test-id' });
    assert.equal(result, stream);
    assert.equal(calls.length, 3);
    assert.equal(calls[1].url, '/api/v1/auth/refresh');
    assert.equal(calls[2].init.headers.Authorization, 'Bearer renewed-test-token');
    assert.equal(calls[0].init.body, calls[2].init.body);
    assert.equal(calls[2].init.credentials, 'include');
  } finally {
    globalThis.fetch = original;
    api.setAccessToken(null);
  }
});

for (const kind of ['network', 'provider'])
  test(`${kind} failures never automatically replay a paid request`, async () => {
    const original = globalThis.fetch;
    let count = 0;
    try {
      globalThis.fetch = async () => {
        count++;
        if (kind === 'network') throw new TypeError('connection interrupted');
        return Response.json(
          { error: { code: 'AI_UNAVAILABLE', message: 'AI service is unavailable' } },
          { status: 503 },
        );
      };
      await assert.rejects(api.streamAIChat({ message: 'Help' }), api.ApiError);
      assert.equal(count, 1);
    } finally {
      globalThis.fetch = original;
    }
  });
