// Install UI behavior in a minimal DOM: browser event availability, dismissal,
// acceptance, standalone mode, insecure context and service-worker failures.
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';
const source = readFileSync(new URL('../frontend/js/pwa.js', import.meta.url), 'utf8');
function setup({ secure = true, standalone = false, failWorker = false } = {}) {
  const events = {};
  const clicks = {};
  const button = { hidden: true, addEventListener: (name, fn) => { clicks[name] = fn; } };
  const status = { textContent: '' };
  const window = {
    isSecureContext: secure, navigator: { standalone },
    matchMedia: () => ({ matches: standalone }),
    addEventListener: (name, fn) => { events[name] = fn; },
  };
  runInNewContext(source, {
    window,
    navigator: { serviceWorker: { register: async () => {
      if (failWorker) throw new Error('Unavailable');
    } } },
    document: {
      getElementById: (id) => id === 'install-app' ? button : status,
      addEventListener: (name, fn) => { events[name] = fn; },
    }, console: { warn() {} },
  });
  events.DOMContentLoaded();
  return { events, button, status, clicks };
}
const app = setup();
assert.equal(app.button.hidden, true);
let shown = 0;
app.events.beforeinstallprompt({ preventDefault() {}, prompt: async () => { shown++; },
  userChoice: Promise.resolve({ outcome: 'dismissed' }) });
assert.equal(app.button.hidden, false);
await app.clicks.click();
assert.equal(shown, 1);
assert.equal(app.button.hidden, true);
assert.ok(!app.status.textContent.includes('щойно встановлено'));
app.events.appinstalled();
assert.ok(app.status.textContent.includes('щойно встановлено'));
const installed = setup({ standalone: true });
assert.equal(installed.button.hidden, true);
assert.ok(installed.status.textContent.includes('як додаток'));
assert.ok(setup({ secure: false }).status.textContent.includes('HTTPS'));
const failed = setup({ failWorker: true });
failed.events.load();
await new Promise((resolve) => setTimeout(resolve, 0));
assert.ok(failed.status.textContent.includes('Не вдалося'));
console.log('PWA install UI: prompt, cancellation, installed/standalone, HTTPS and registration error passed.');
