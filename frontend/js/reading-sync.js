/**
 * Rate-safe background writer for Reading (progress and quiz answers).
 *
 * The API limits progress writes to 60/min and attempt writes to 30/min per learner, so the UI
 * never sends one request per scroll tick or click. `createWriter` keeps only the *latest*
 * value, waits `delayMs` after the last change (debounce), never sends twice within
 * `minIntervalMs`, never runs two requests at once, and backs off after a failure
 * (`429` waits a full minute). `flush()` sends the pending value as soon as the spacing allows,
 * which is what page-hide and submit use. With the defaults used by the pages the ceiling is
 * 12 progress writes and 20 answer writes per minute, well under the server limits.
 *
 * Timers and the clock are injectable so the behaviour is unit-tested without waiting.
 */

export const RATE_LIMIT_BACKOFF_MS = 60_000;
const MAX_ERROR_BACKOFF_MS = 30_000;

/**
 * @param {object} options
 * @param {(value: any) => Promise<void>} options.write      performs the request
 * @param {(value: any, lastSent: any) => boolean} [options.shouldSend]  skip no-op values
 * @param {number} [options.delayMs]        quiet period after the last change
 * @param {number} [options.minIntervalMs]  minimum gap between two requests
 * @param {(state: string) => void} [options.onState]  idle | pending | saving | saved | error
 */
export function createWriter({
  write,
  shouldSend = () => true,
  delayMs = 1000,
  minIntervalMs = 5000,
  onState = () => {},
  now = () => Date.now(),
  setTimer = (fn, ms) => setTimeout(fn, ms),
  clearTimer = (id) => clearTimeout(id),
}) {
  let pending;
  let hasPending = false;
  let lastSent;
  let lastSentAt = -Infinity;
  let blockedUntil = 0;
  let failures = 0;
  let timer = null;
  let inFlight = null;
  let disposed = false;

  function schedule(wait) {
    if (disposed) return;
    if (timer !== null) clearTimer(timer);
    timer = setTimer(() => {
      timer = null;
      void run();
    }, Math.max(0, wait));
  }

  function earliest(quiet) {
    const spacing = lastSentAt + minIntervalMs - now();
    return Math.max(quiet, spacing, blockedUntil - now());
  }

  async function run() {
    if (disposed || inFlight || !hasPending) return;
    const wait = earliest(0);
    if (wait > 0) {
      schedule(wait);
      return;
    }
    const value = pending;
    hasPending = false;
    if (!shouldSend(value, lastSent)) {
      onState('idle');
      return;
    }
    lastSentAt = now();
    onState('saving');
    inFlight = (async () => {
      try {
        await write(value);
        lastSent = value;
        failures = 0;
        onState(hasPending ? 'pending' : 'saved');
      } catch (error) {
        failures += 1;
        if (!hasPending) {
          pending = value;
          hasPending = true;
        }
        blockedUntil =
          error?.status === 429
            ? now() + RATE_LIMIT_BACKOFF_MS
            : now() + Math.min(MAX_ERROR_BACKOFF_MS, 2 ** failures * 1000);
        onState('error');
      }
    })();
    await inFlight;
    inFlight = null;
    if (hasPending && !disposed) schedule(earliest(delayMs));
  }

  return {
    /** Record the newest value; it replaces any value not sent yet. */
    set(value) {
      if (disposed) return;
      pending = value;
      hasPending = true;
      onState('pending');
      schedule(earliest(delayMs));
    },
    /** Send the pending value now (still honouring spacing and back-off). */
    async flush() {
      if (disposed) return;
      if (timer !== null) {
        clearTimer(timer);
        timer = null;
      }
      if (inFlight) await inFlight;
      if (hasPending) {
        const wait = earliest(0);
        if (wait > 0) {
          schedule(wait);
          return;
        }
        await run();
      }
    },
    /** True while a value waits to be sent or a request is running. */
    isDirty: () => hasPending || inFlight !== null,
    dispose() {
      disposed = true;
      if (timer !== null) clearTimer(timer);
      timer = null;
    },
  };
}

/** Share of the article the learner has scrolled through, 0-100 (whole numbers). */
export function readPercent({ top, height, viewport }) {
  if (!(height > 0)) return 0;
  const seen = Math.min(height, Math.max(0, viewport - top));
  return Math.max(0, Math.min(100, Math.floor((seen / height) * 100)));
}

/** Progress is worth sending when it moved at least 5 points, or reached 100. */
export function progressWorthSending(value, lastSent) {
  if (lastSent === undefined) return value > 0;
  return value > lastSent && (value - lastSent >= 5 || value === 100);
}
