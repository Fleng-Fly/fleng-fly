import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
// Import the browser ES module without introducing a package/build configuration.
const source = await readFile(new URL('../frontend/js/ai-stream.js', import.meta.url), 'utf8');
const { readAIEvents } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);
const encoder = new TextEncoder();
function body(bytes, size) {
  return new ReadableStream({
    start(controller) {
      for (let i = 0; i < bytes.length; i += size) controller.enqueue(bytes.slice(i, i + size));
      controller.close();
    },
  });
}
for (const size of [1, 2, 7, 10000])
  test(`UTF-8, CRLF, comments, multiline JSON and chunk size ${size}`, async () => {
    const text =
      ': keepalive\r\n\r\nevent: delta\r\ndata: {"content": "Привет 👋 <script>"}\r\n\r\nevent: done\ndata: {"conversationId":"id",\ndata: "message":{"content":"Привет 👋 <script>"}}\n\n';
    const events = [];
    for await (const event of readAIEvents(body(encoder.encode(text), size))) events.push(event);
    assert.deepEqual(
      events.map((item) => item.name),
      ['delta', 'done'],
    );
    assert.equal(events[0].data.content, 'Привет 👋 <script>');
    assert.equal(events[1].data.message.content, events[0].data.content);
  });
test('truncated network response cannot become success', async () => {
  await assert.rejects(async () => {
    for await (const event of readAIEvents(
      body(encoder.encode('event: delta\ndata: {"content":"Hi"}\n\n'), 3),
    ))
      assert.equal(event.name, 'delta');
  }, /before the response was saved/);
});
test('provider error is terminal and never triggers another request', async () => {
  const events = [];
  for await (const event of readAIEvents(
    body(
      encoder.encode('event: error\ndata: {"code":"AI_TIMEOUT"}\n\nevent: done\ndata: {}\n\n'),
      2,
    ),
  ))
    events.push(event);
  assert.equal(events.length, 1);
  assert.equal(events[0].name, 'error');
});
test('malformed event rejected', async () => {
  await assert.rejects(async () => {
    for await (const event of readAIEvents(
      body(encoder.encode('event: delta\ndata: invalid\n\n'), 2),
    ))
      void event;
  }, SyntaxError);
});
