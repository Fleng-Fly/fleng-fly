// Sequential, fail-fast local verification. No setup, downloads or production operations.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
if (args.some(arg => arg !== '--skip-e2e')) {
  console.error('Usage: npm run check:all -- [--skip-e2e]');
  process.exit(2);
}
for (const path of ['.env', 'backend/.env']) {
  if (existsSync(join(root, path))) {
    console.error(`Refusing private configuration ${path}. Run checks in a clean worktree without .env files.`);
    process.exit(2);
  }
}
const python = join(root, 'backend/.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
if (!existsSync(python)) {
  console.error('Backend environment missing. Run npm run setup first.');
  process.exit(2);
}
const allowed = new Set(['PATH', 'HOME', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT',
  'TEMP', 'TMP', 'TMPDIR', 'LANG', 'LC_ALL', 'CI', 'PLAYWRIGHT_BROWSERS_PATH']);
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => allowed.has(key.toUpperCase())));
const directory = mkdtempSync(join(tmpdir(), 'fleng-check-all-'));
Object.assign(env, {
  APP_ENV: 'development', DATABASE_URL: `sqlite+aiosqlite:///${join(directory, 'checks.sqlite3').replaceAll('\\', '/')}`,
  AI_ENABLED: 'false', OPENROUTER_API_KEY: '', RESET_DELIVERY: 'disabled',
  JWT_ACCESS_SECRET: 'disposable-local-check-secret-at-least-32-characters',
});
// npm supplies the CLI path on all supported platforms; direct invocation has a fallback.
const npmCli = process.env.npm_execpath;
const npm = name => npmCli ? [process.execPath, [npmCli, 'run', name]] :
  [process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', name]];
const steps = [
  ['Python dependency consistency', python, ['-m', 'pip', 'check']],
  ['Pinned dependencies', python, ['scripts/check-dependencies.py']],
  ...['backend:lint', 'backend:typecheck', 'frontend:test', 'test:pwa', 'docs:check', 'curriculum:validate', 'db:smoke', 'backend:test']
    .map(name => [name, ...npm(name)]),
  ...(!args.includes('--skip-e2e') ? [['test:e2e', ...npm('test:e2e')]] : []),
  ['Whitespace', 'git', ['diff', '--check']],
];
let status = 0;
try {
  for (const [label, command, parameters] of steps) {
    console.log(`\n=== ${label} ===`);
    const result = spawnSync(command, parameters, { cwd: root, env, stdio: 'inherit',
      shell: process.platform === 'win32' && command === 'npm.cmd' });
    if (result.error || result.status !== 0) {
      console.error(`FAILED: ${label}${result.error ? `: ${result.error.message}` : ''}. Later checks were not run.`);
      status = result.status || 1;
      break;
    }
  }
} finally {
  rmSync(directory, { recursive: true, force: true });
}
console.log(status ? '\nProject checks failed.' : `\nProject checks passed.${args.length ? ' E2E was explicitly skipped.' : ''}`);
process.exit(status);
