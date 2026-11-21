/**
 * Reading heartbeat controller: tells the server "this learner is actively reading".
 *
 * It sends one request per `intervalMs` (15 s) and only while ALL of these hold: the tab is
 * visible, the window has focus, the learner interacted within `idleMs` (45 s), the page is not
 * paused (e.g. while a request is running) and no back-off is active. The server decides how
 * much time to credit from its own clock, so the client sends no time. There is deliberately no
 * queue and no retry of missed beats: a lost beat is simply lost (the server credits nothing
 * for the gap), and a 429 pauses beats for a minute. 401/404 stop the controller for good.
 *
 * Timers, the clock and the page state are injectable so the rules are unit-tested.
 */

export const HEARTBEAT_INTERVAL_MS = 15_000;
export const IDLE_AFTER_MS = 45_000;
export const RATE_LIMIT_PAUSE_MS = 60_000;

export function createHeartbeat({
  send,
  onResult = () => {},
  intervalMs = HEARTBEAT_INTERVAL_MS,
  idleMs = IDLE_AFTER_MS,
  isVisible = () => document.visibilityState === 'visible',
  hasFocus = () => document.hasFocus(),
  now = () => Date.now(),
  setTimer = (fn, ms) => setInterval(fn, ms),
  clearTimer = (id) => clearInterval(id),
}) {
  let lastInteraction = -Infinity;
  let pausedUntil = 0;
  let paused = false;
  let inFlight = false;
  let stopped = false;
  let timer = null;

  function eligible() {
    return (
      !stopped &&
      !paused &&
      !inFlight &&
      now() >= pausedUntil &&
      isVisible() &&
      hasFocus() &&
      now() - lastInteraction <= idleMs
    );
  }

  async function tick() {
    if (!eligible()) return;
    inFlight = true;
    try {
      onResult(await send());
    } catch (error) {
      if (error?.status === 429) pausedUntil = now() + RATE_LIMIT_PAUSE_MS;
      else if (error?.status === 401 || error?.status === 404) stop();
      // Any other failure (network, 5xx): skip this beat, never queue or replay it.
    } finally {
      inFlight = false;
    }
  }

  function stop() {
    stopped = true;
    if (timer !== null) clearTimer(timer);
    timer = null;
  }

  return {
    /** Call on scroll, key, pointer and touch events. */
    markInteraction() {
      lastInteraction = now();
    },
    start() {
      if (timer === null && !stopped) timer = setTimer(() => void tick(), intervalMs);
    },
    /** Temporarily stop beating (for example while the quiz is being submitted). */
    setPaused(value) {
      paused = Boolean(value);
    },
    stop,
    tick,
    isRunning: () => timer !== null && !stopped,
  };
}

/** `seconds` as a short label: "less than a minute" below 60 s, otherwise whole minutes. */
export function durationParts(seconds) {
  const safe = Math.max(0, Math.floor(Number(seconds) || 0));
  return safe < 60 ? { under: true, minutes: 0 } : { under: false, minutes: Math.floor(safe / 60) };
}
