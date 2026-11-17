// Pure helpers for scripts/dev.mjs (kept separate so they can be unit-tested).
import { existsSync, readFileSync, statSync } from 'node:fs';
import net from 'node:net';
import { dirname, isAbsolute, resolve } from 'node:path';

/** Main checkout when `root` is a linked git worktree (`.git` is a file), else null. */
export function primaryCheckout(root) {
  const marker = resolve(root, '.git');
  try {
    if (!statSync(marker).isFile()) return null;
    const line = readFileSync(marker, 'utf8').split('\n')[0];
    if (!line.startsWith('gitdir:')) return null;
    let gitdir = line.slice('gitdir:'.length).trim();
    if (!isAbsolute(gitdir)) gitdir = resolve(root, gitdir);
    // <main>/.git/worktrees/<name> -> <main>
    return dirname(dirname(dirname(resolve(gitdir))));
  } catch {
    return null;
  }
}

/**
 * Pick the backend virtualenv. A checkout's own `.venv` always wins. A linked worktree
 * without one may reuse the main checkout's interpreter (only the interpreter and
 * packages: the application code always comes from the current checkout).
 */
export function resolveVenv(root, platform = process.platform) {
  const bin = platform === 'win32' ? 'Scripts' : 'bin';
  const exe = platform === 'win32' ? '.exe' : '';
  const at = (base) => ({
    python: resolve(base, 'backend', '.venv', bin, `python${exe}`),
    uvicorn: resolve(base, 'backend', '.venv', bin, `uvicorn${exe}`),
  });
  const local = at(root);
  if (existsSync(local.uvicorn)) return { ...local, source: 'checkout' };
  const primary = primaryCheckout(root);
  if (primary) {
    const shared = at(primary);
    if (existsSync(shared.uvicorn)) return { ...shared, source: `main checkout (${primary})` };
  }
  return null;
}

/** True when something already accepts connections on host:port. */
export function portInUse(port, host = '127.0.0.1', timeoutMs = 500) {
  return new Promise((done) => {
    const socket = net.connect({ port: Number(port), host });
    const finish = (value) => {
      socket.destroy();
      done(value);
    };
    socket.setTimeout(timeoutMs, () => finish(false));
    socket.once('connect', () => finish(true));
    socket.once('error', () => finish(false));
  });
}

/** Ask a busy Fleng dev server which checkout it serves (header set by app.development). */
export async function describeListener(port, host = '127.0.0.1', timeoutMs = 1000) {
  try {
    const response = await fetch(`http://${host}:${port}/api/v1/health`, {
      signal: AbortSignal.timeout(timeoutMs),
    });
    return {
      checkout: response.headers.get('x-fleng-checkout'),
      mode: response.headers.get('x-fleng-mode'),
    };
  } catch {
    return { checkout: null, mode: null };
  }
}

export function busyPortMessage(port, root, listener) {
  const lines = [`Port ${port} is already in use; Fleng did not start.`];
  if (listener.checkout && listener.checkout === root) {
    lines.push('It is already served by THIS checkout (the dev server is running).');
  } else if (listener.checkout) {
    lines.push(`It is served by another Fleng checkout: ${listener.checkout}`);
    lines.push(`This checkout is: ${root}`);
  } else {
    lines.push('Another process owns it (it did not identify itself as a Fleng dev server).');
  }
  lines.push(`Stop that process yourself, or start this checkout on another port: PORT=${Number(port) + 1} npm run dev`);
  return lines.join('\n');
}
