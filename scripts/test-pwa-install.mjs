// Browser install offers stay suppressed; offline registration remains available.
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';
const source = readFileSync(new URL('../frontend/js/pwa.js', import.meta.url), 'utf8');
function setup({ secure = true, worker = true, failWorker = false } = {}) {
  const events = {};
  const registrations = [];
  const warnings = [];
  runInNewContext(source, {
    window: {
      isSecureContext: secure,
      addEventListener: (name, fn) => { events[name] = fn; },
    },
    navigator: worker ? { serviceWorker: { register: async (path, options) => {
      registrations.push({ path, options });
      if (failWorker) throw new Error('Unavailable');
    } } } : {},
    console: { warn: (...args) => warnings.push(args) },
  });
  return { events, registrations, warnings };
}
const app = setup();
let suppressed = false;
app.events.beforeinstallprompt({ preventDefault() { suppressed = true; },
  prompt() { assert.fail('Must not offer installation'); } });
assert.equal(suppressed, true);
assert.equal(app.events.appinstalled, undefined);
app.events.load();
assert.equal(app.registrations.length, 1);
assert.equal(app.registrations[0].path, '/sw.js');
assert.equal(app.registrations[0].options.updateViaCache, 'none');
assert.equal(setup({ secure: false }).events.load, undefined);
assert.equal(setup({ worker: false }).events.load, undefined);
const failed = setup({ failWorker: true });
failed.events.load();
await new Promise((resolve) => setTimeout(resolve, 0));
assert.equal(failed.warnings.length, 1);
console.log('PWA: installation offers suppressed; registration, HTTPS and error handling passed.');
