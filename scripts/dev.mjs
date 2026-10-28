// Runs the FastAPI backend, which also serves the static frontend.
// Ensures the backend virtualenv exists first. Dependency-free by design.
import { execFileSync, spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backendDir = resolve(root, 'backend');
const isWindows = process.platform === 'win32';
const venvPython = resolve(backendDir, '.venv', isWindows ? 'Scripts/python.exe' : 'bin/python');
const venvUvicorn = resolve(backendDir, '.venv', isWindows ? 'Scripts/uvicorn.exe' : 'bin/uvicorn');

if (!existsSync(venvUvicorn)) {
  console.log('Backend environment missing; running setup…');
  execFileSync(process.execPath, [resolve(root, 'scripts', 'setup.mjs')], { stdio: 'inherit' });
}

// Fail before serving HTTP if a local migration or initial seed fails.
execFileSync(venvPython, ['-m', 'app.db.prepare'], { cwd: backendDir, stdio: 'inherit' });

const children = [];
let shuttingDown = false;

function start(name, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    shell: isWindows,
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

const port = process.env.PORT ?? '3001';

// One server: FastAPI serves both /api/v1 and the static frontend on the same
// port, so the HttpOnly refresh cookie stays first-party.
start(
  'backend',
  venvUvicorn,
  ['app.main:app', '--reload', '--no-proxy-headers', '--host', '0.0.0.0', '--port', port],
  backendDir,
);
