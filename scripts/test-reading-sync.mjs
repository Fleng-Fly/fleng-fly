import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  RATE_LIMIT_BACKOFF_MS,
  createWriter,
  progressWorthSending,
  readPercent,
} from '../frontend/js/reading-sync.js';

/** Deterministic clock + timers: `advance(ms)` fires due timers in order. */
function clock() {
  let time = 0,
    nextId = 1;
  const timers = new Map();
  return {
    now: () => time,
    setTimer: (fn, ms) => {
      const id = nextId++;
      timers.set(id, { fn, at: time + ms });
      return id;
    },
    clearTimer: (id) => {
      timers.delete(id);
    },
    async advance(ms) {
      const target = time + ms;
      for (;;) {
        const due = [...timers.entries()]
          .filter(([, t]) => t.at <= target)
          .sort((a, b) => a[1].at - b[1].at)[0];
        if (!due) break;
        timers.delete(due[0]);
        time = Math.max(time, due[1].at);
        due[1].fn();
        for (let i = 0; i < 5; i++) await Promise.resolve();
      }
      time = target;
      for (let i = 0; i < 5; i++) await Promise.resolve();
    },
  };
}

function setup(options = {}) {
  const c = clock();
  const sent = [];
  const states = [];
  const writer = createWriter({
    write: async (value) => {
      if (options.fail) throw options.fail;
      sent.push({ value, at: c.now() });
    },
    onState: (s) => states.push(s),
    now: c.now,
    setTimer: c.setTimer,
    clearTimer: c.clearTimer,
    ...options.config,
  });
  return { c, sent, states, writer };
}

test('a burst of changes sends only the latest value after the quiet period', async () => {
  const { c, sent, writer } = setup({ config: { delayMs: 1000, minIntervalMs: 5000 } });
  for (let i = 1; i <= 50; i++) writer.set(i);
  await c.advance(999);
  assert.equal(sent.length, 0);
  await c.advance(2);
  assert.deepEqual(
    sent.map((s) => s.value),
    [50],
  );
});

test('never sends twice within the minimum interval and stays far below 60 per minute', async () => {
  const { c, sent, writer } = setup({ config: { delayMs: 200, minIntervalMs: 5000 } });
  for (let second = 0; second < 120; second++) {
    writer.set(second);
    await c.advance(1000);
  }
  const gaps = sent.slice(1).map((s, i) => s.at - sent[i].at);
  assert.ok(
    gaps.every((gap) => gap >= 5000),
    `gaps: ${gaps}`,
  );
  const perMinute = sent.filter((s) => s.at < 60_000).length;
  assert.ok(perMinute <= 12, `sent ${perMinute} in the first minute`);
  assert.equal(sent.at(-1).value >= 110, true); // trailing value is not lost
});

test('requests never overlap', async () => {
  const c = clock();
  let running = 0,
    peak = 0,
    calls = 0;
  let release;
  const writer = createWriter({
    write: () => {
      calls++;
      running++;
      peak = Math.max(peak, running);
      return new Promise((resolve) => {
        release = () => {
          running--;
          resolve();
        };
      });
    },
    delayMs: 0,
    minIntervalMs: 0,
    now: c.now,
    setTimer: c.setTimer,
    clearTimer: c.clearTimer,
  });
  writer.set(1);
  await c.advance(1);
  writer.set(2);
  await c.advance(10);
  assert.equal(calls, 1);
  release();
  await c.advance(0); // let the writer notice completion and schedule the next write
  await c.advance(10);
  assert.equal(calls, 2);
  release();
  assert.equal(peak, 1);
});

test('shouldSend skips values that do not change anything', async () => {
  const { c, sent, writer } = setup({
    config: { shouldSend: progressWorthSending, delayMs: 0, minIntervalMs: 0 },
  });
  writer.set(3);
  await c.advance(5);
  writer.set(6); // +3 only
  await c.advance(5);
  writer.set(9); // +6 vs last sent 3
  await c.advance(5);
  writer.set(9);
  await c.advance(5);
  assert.deepEqual(
    sent.map((s) => s.value),
    [3, 9],
  );
});

test('flush sends right away when spacing allows and still honours it otherwise', async () => {
  const { c, sent, writer } = setup({ config: { delayMs: 5000, minIntervalMs: 3000 } });
  writer.set('a');
  await writer.flush();
  assert.deepEqual(
    sent.map((s) => s.value),
    ['a'],
  );
  writer.set('b');
  await writer.flush(); // too soon: deferred, not dropped
  assert.equal(sent.length, 1);
  await c.advance(3000);
  assert.deepEqual(
    sent.map((s) => s.value),
    ['a', 'b'],
  );
  assert.equal(writer.isDirty(), false);
});

test('a failed write keeps the value and retries later with back-off', async () => {
  const c = clock();
  const sent = [];
  let failing = true;
  const states = [];
  const writer = createWriter({
    write: async (value) => {
      if (failing) throw Object.assign(new Error('x'), { status: 500 });
      sent.push(value);
    },
    onState: (s) => states.push(s),
    delayMs: 0,
    minIntervalMs: 0,
    now: c.now,
    setTimer: c.setTimer,
    clearTimer: c.clearTimer,
  });
  writer.set('kept');
  await c.advance(1);
  assert.equal(states.at(-1), 'error');
  assert.equal(writer.isDirty(), true);
  failing = false;
  await c.advance(5000);
  assert.deepEqual(sent, ['kept']);
  assert.equal(states.at(-1), 'saved');
});

test('429 pauses all writes for a full minute', async () => {
  const c = clock();
  let attempts = 0;
  const writer = createWriter({
    write: async () => {
      attempts++;
      if (attempts === 1) throw Object.assign(new Error('limit'), { status: 429 });
    },
    delayMs: 0,
    minIntervalMs: 0,
    now: c.now,
    setTimer: c.setTimer,
    clearTimer: c.clearTimer,
  });
  writer.set(1);
  await c.advance(1);
  assert.equal(attempts, 1);
  writer.set(2);
  await c.advance(RATE_LIMIT_BACKOFF_MS - 100);
  assert.equal(attempts, 1);
  await c.advance(200);
  assert.equal(attempts, 2);
});

test('dispose stops everything', async () => {
  const { c, sent, writer } = setup({ config: { delayMs: 10 } });
  writer.set(1);
  writer.dispose();
  await c.advance(1000);
  assert.equal(sent.length, 0);
});

test('readPercent measures how much of the article has been scrolled past', () => {
  assert.equal(readPercent({ top: 100, height: 1000, viewport: 700 }), 60);
  assert.equal(readPercent({ top: 900, height: 1000, viewport: 700 }), 0);
  assert.equal(readPercent({ top: -2000, height: 1000, viewport: 700 }), 100);
  assert.equal(readPercent({ top: 0, height: 0, viewport: 700 }), 0);
  assert.equal(readPercent({ top: 0, height: 1000, viewport: 999 }), 99);
});

test('progressWorthSending only reports growth of at least 5 points, or completion', () => {
  assert.equal(progressWorthSending(0, undefined), false);
  assert.equal(progressWorthSending(2, undefined), true);
  assert.equal(progressWorthSending(7, 5), false);
  assert.equal(progressWorthSending(10, 5), true);
  assert.equal(progressWorthSending(100, 98), true);
  assert.equal(progressWorthSending(50, 60), false);
});
