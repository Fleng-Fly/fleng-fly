// Creates the backend virtualenv and installs Python dependencies.
// Cross-platform (Linux/macOS; Windows uses Scripts/python.exe).
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backendDir = resolve(root, 'backend');
const isWindows = process.platform === 'win32';
const venvPython = resolve(backendDir, '.venv', isWindows ? 'Scripts/python.exe' : 'bin/python');

function run(command, args) {
  execFileSync(command, args, { cwd: backendDir, stdio: 'inherit' });
}

if (!existsSync(venvPython)) {
  console.log('Creating backend virtualenv (.venv)…');
  run(isWindows ? 'python' : 'python3', ['-m', 'venv', '.venv']);
}

console.log('Installing backend dependencies…');
run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip']);
run(venvPython, ['-m', 'pip', 'install', '-e', '.[dev]']);
console.log('Backend setup complete.');
