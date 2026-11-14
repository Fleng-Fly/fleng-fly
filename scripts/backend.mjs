// Run backend modules with the virtualenv Python on Windows, Linux and macOS.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backendDir = resolve(root, 'backend');
const python = resolve(
  backendDir,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
);
const [moduleName, ...args] = process.argv.slice(2);

if (!moduleName) {
  console.error('Usage: node scripts/backend.mjs <python-module> [arguments]');
  process.exit(2);
}
if (!existsSync(python)) {
  console.error('Backend environment missing. Run npm run setup first.');
  process.exit(1);
}

const result = spawnSync(python, ['-m', moduleName, ...args], {
  cwd: backendDir,
  stdio: 'inherit',
  shell: false,
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
