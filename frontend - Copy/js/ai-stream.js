/** Incremental UTF-8 SSE framing, including CRLF and arbitrary byte boundaries. */
export async function* readAIEvents(body) {
  if (!body) throw new Error('Streaming is unavailable in this browser.');
  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let pending = '';
  let frame = [];
  let ended = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      pending += done ? decoder.decode() : decoder.decode(value, { stream: true });
      if (pending.length > 262144) throw new Error('AI event exceeded limits.');
      let newline;
      while ((newline = pending.indexOf('\n')) >= 0) {
        const line = pending.slice(0, newline).replace(/\r$/, '');
        pending = pending.slice(newline + 1);
        if (line) frame.push(line);
        else if (frame.length) {
          const name = frame
            .find((item) => item.startsWith('event:'))
            ?.slice(6)
            .trim();
          const data = frame
            .filter((item) => item.startsWith('data:'))
            .map((item) => item.slice(5).replace(/^ /, ''))
            .join('\n');
          frame = [];
          if (data) {
            const event = { name, data: JSON.parse(data) };
            if (name === 'done' || name === 'error') ended = true;
            yield event;
            if (ended) return;
          }
        }
        if (frame.join('\n').length > 262144) throw new Error('AI event exceeded limits.');
      }
      if (done) break;
    }
    if (!ended) throw new Error('Connection ended before the response was saved. Reload history.');
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
