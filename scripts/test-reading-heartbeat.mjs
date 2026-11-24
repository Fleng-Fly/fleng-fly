import './require-vm-modules.mjs';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  HEARTBEAT_INTERVAL_MS,
  IDLE_AFTER_MS,
  RATE_LIMIT_PAUSE_MS,
  createHeartbeat,
  durationParts,
} from '../frontend/js/reading-heartbeat.js';

function setup(overrides = {}) {
  const page = { visible: true, focus: true, time: 0 };
  const sent = [];
  const results = [];
  const hb = createHeartbeat({
    send:
      overrides.send ??
      (async () => {
        sent.push(page.time);
        return { creditedSeconds: 1 };
      }),
    onResult: (r) => results.push(r),
    isVisible: () => page.visible,
    hasFocus: () => page.focus,
    now: () => page.time,
    setTimer: () => 1,
    clearTimer: () => {},
  });
  return { page, sent, results, hb };
}
const advance = async (page, hb, ms) => {
  page.time += ms;
  await hb.tick();
};

test('beats only after the learner interacted, while visible and focused', async () => {
  const { page, sent, hb } = setup();
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 0); // never interacted: no heartbeat just for opening the page
  hb.markInteraction();
  await advance(page, hb, 1_000);
  assert.equal(sent.length, 1);
});

test('a hidden tab or a window without focus sends nothing', async () => {
  const { page, sent, hb } = setup();
  hb.markInteraction();
  page.visible = false;
  await advance(page, hb, 15_000);
  page.visible = true;
  page.focus = false;
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 0);
  page.focus = true;
  hb.markInteraction();
  await advance(page, hb, 1_000);
  assert.equal(sent.length, 1);
});

test('idle learners stop beating after 45 seconds without interaction', async () => {
  const { page, sent, hb } = setup();
  hb.markInteraction();
  await advance(page, hb, 15_000);
  await advance(page, hb, 15_000);
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 3); // up to and including 45 s
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 3);
  hb.markInteraction();
  await advance(page, hb, 1_000);
  assert.equal(sent.length, 4);
  assert.equal(IDLE_AFTER_MS, 45_000);
  assert.equal(HEARTBEAT_INTERVAL_MS, 15_000);
});

test('requests never overlap', async () => {
  let release;
  let calls = 0;
  const { page, hb } = setup({
    send: () =>
      ++calls === 1
        ? new Promise((r) => {
            release = r;
          })
        : Promise.resolve({}),
  });
  hb.markInteraction();
  const first = hb.tick();
  await hb.tick(); // second tick while the first is still running
  assert.equal(calls, 1);
  release({});
  await first;
  await advance(page, hb, 1);
  assert.equal(calls, 2);
});

test('a 429 pauses beats for a minute; other failures are skipped without retry or queue', async () => {
  let mode = '429';
  const attempts = [];
  const { page, hb } = setup({
    send: async () => {
      attempts.push(page.time);
      if (mode === '429') throw Object.assign(new Error('limit'), { status: 429 });
      if (mode === '500') throw Object.assign(new Error('boom'), { status: 500 });
      return {};
    },
  });
  hb.markInteraction();
  await advance(page, hb, 1);
  assert.equal(attempts.length, 1);
  for (let i = 0; i < 3; i++) {
    hb.markInteraction();
    await advance(page, hb, 15_000);
  }
  assert.equal(attempts.length, 1); // still paused
  mode = '500'; // the pause is over: the next beat goes out and fails differently
  page.time += RATE_LIMIT_PAUSE_MS; // the learner is still reading when the pause ends
  hb.markInteraction();
  await hb.tick();
  assert.equal(attempts.length, 2);
  mode = 'ok';
  hb.markInteraction();
  await advance(page, hb, 15_000);
  assert.equal(attempts.length, 3); // the failed beat was not replayed or queued
});

test('401 and 404 stop the controller for good', async () => {
  for (const status of [401, 404]) {
    let calls = 0;
    const { page, hb } = setup({
      send: async () => {
        calls++;
        throw Object.assign(new Error('x'), { status });
      },
    });
    hb.markInteraction();
    await advance(page, hb, 1);
    hb.markInteraction();
    await advance(page, hb, 15_000);
    assert.equal(calls, 1, `status ${status}`);
    assert.equal(hb.isRunning(), false);
  }
});

test('pausing and stopping suppress beats; results are reported', async () => {
  const { page, sent, results, hb } = setup();
  hb.markInteraction();
  hb.setPaused(true);
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 0);
  hb.setPaused(false);
  hb.markInteraction();
  await advance(page, hb, 1);
  assert.equal(sent.length, 1);
  assert.deepEqual(results, [{ creditedSeconds: 1 }]);
  hb.stop();
  hb.markInteraction();
  await advance(page, hb, 15_000);
  assert.equal(sent.length, 1);
});

test('start schedules one timer, stop clears it', () => {
  const calls = { set: 0, cleared: 0 };
  const hb = createHeartbeat({
    send: async () => ({}),
    isVisible: () => true,
    hasFocus: () => true,
    now: () => 0,
    setTimer: () => {
      calls.set++;
      return 7;
    },
    clearTimer: () => {
      calls.cleared++;
    },
  });
  hb.start();
  hb.start();
  assert.equal(calls.set, 1);
  assert.equal(hb.isRunning(), true);
  hb.stop();
  assert.equal(calls.cleared, 1);
});

test('durations: below a minute is a label, otherwise whole minutes', () => {
  assert.deepEqual(durationParts(0), { under: true, minutes: 0 });
  assert.deepEqual(durationParts(59), { under: true, minutes: 0 });
  assert.deepEqual(durationParts(60), { under: false, minutes: 1 });
  assert.deepEqual(durationParts(185), { under: false, minutes: 3 });
  assert.deepEqual(durationParts(-5), { under: true, minutes: 0 });
  assert.deepEqual(durationParts('x'), { under: true, minutes: 0 });
});
