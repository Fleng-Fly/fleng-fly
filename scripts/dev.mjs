// Runs the FastAPI backend, which also serves the static frontend.
// Ensures the backend virtualenv exists first. Dependency-free by design.
import { execFileSync, spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { busyPortMessage, describeListener, portInUse, resolveVenv } from './dev-helpers.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backendDir = resolve(root, 'backend');
const port = process.env.PORT ?? '3001';

// Never start preparation (backup, migrations, imports) when the port is taken: the old
// server would keep serving a possibly different checkout.
if (await portInUse(port)) {
  console.error(busyPortMessage(port, root, await describeListener(port)));
  process.exit(1);
}

let venv = resolveVenv(root);
if (!venv) {
  console.log('Backend environment missing; running setup…');
  execFileSync(process.execPath, [resolve(root, 'scripts', 'setup.mjs')], { stdio: 'inherit' });
  venv = resolveVenv(root);
}
const venvPython = venv.python;
const venvUvicorn = venv.uvicorn;
console.log(`Using the Python environment of the ${venv.source}; application code: ${backendDir}`);

// Back up local data, prepare migrations and import unpublished development drafts.
// This entry point refuses hosted/production databases before any preparation.
try {
  execFileSync(venvPython, ['-m', 'app.development'], { cwd: backendDir, stdio: 'inherit' });
} catch (error) {
  // The launcher already printed why it refused (or what failed); skip the Node stack trace.
  process.exit(typeof error.status === 'number' ? error.status : 1);
}

const children = [];
let shuttingDown = false;

function start(name, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    shell: false,
    env: process.env,
  });
  child.on('exit', (code) => {
    if (!shuttingDown) {
      process.exitCode = code ?? 1;
      console.log(`[${name}] exited with code ${code}`);
      shutdown();
    }
  });
  child.on('error', (error) => {
    console.error(`[${name}] ${error.message}`);
    process.exitCode = 1;
    shutdown();
  });
  children.push(child);
}

function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (!child.killed) child.kill('SIGTERM');
  }
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// One server: FastAPI serves both /api/v1 and the static frontend on the same
// port, so the HttpOnly refresh cookie stays first-party.
start(
  'backend',
  venvUvicorn,
  ['app.development:create_development_app', '--factory', '--app-dir', backendDir, '--reload', '--reload-dir', backendDir, '--no-proxy-headers', '--host', '127.0.0.1', '--port', port],
  backendDir,
);
