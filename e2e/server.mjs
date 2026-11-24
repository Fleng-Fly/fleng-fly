// Starts the real Fleng backend (FastAPI, serving the static frontend) for browser E2E tests.
//
// - Database: a brand-new SQLite file in a private temp directory. It is migrated and seeded with
//   the normal `app.db.prepare` step, so the catalog is the one the real app publishes.
// - Isolation: only this process's environment is overridden; no .env value, production service or
//   existing database file is used. AI and password-reset email are disabled.
// - Cleanup: the temp directory is removed when the server stops (SIGTERM/SIGINT/exit).
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backendDir = join(root, 'backend');
const isWindows = process.platform === 'win32';
const python =
  process.env.E2E_PYTHON ??
  join(backendDir, '.venv', isWindows ? 'Scripts/python.exe' : 'bin/python');
const port = process.env.E2E_PORT ?? '3101';

if (!existsSync(python)) {
  console.error(`Python not found at ${python}. Run "npm run setup" or set E2E_PYTHON.`);
  process.exit(1);
}

const dataDir = mkdtempSync(join(tmpdir(), 'fleng-e2e-'));
const env = {
  ...process.env,
  APP_ENV: 'development',
  PORT: port,
  DATABASE_URL: `sqlite+aiosqlite:///${dataDir.replaceAll('\\', '/')}/e2e.sqlite3`,
  JWT_ACCESS_SECRET: 'e2e-only-secret-never-used-outside-tests-0123456789',
  AI_ENABLED: 'false',
  RESET_DELIVERY: 'disabled',
  // Every test registers its own learner from the same IP. The default throttles (10 registrations
  // per IP per hour) are a real security control covered by the backend tests; they are only
  // raised here, through the app's own settings, so the browser suite can run repeatedly.
  AUTH_REGISTER_IP_PER_HOUR: '10000',
  AUTH_LOGIN_IP_PER_MINUTE: '1000',
  OPENROUTER_API_KEY: '',
  // The backend also reads <repo>/.env and backend/.env as defaults. A real-looking local .env
  // (e.g. Google OAuth) must never reach the test server, so every optional integration is
  // blanked here; process environment variables take precedence over dotenv files.
  GOOGLE_CLIENT_ID: '',
  GOOGLE_CLIENT_SECRET: '',
  GOOGLE_REDIRECT_URI: '',
};

let child;
let cleaned = false;
function cleanup() {
  if (cleaned) return;
  cleaned = true;
  if (child && child.exitCode === null) child.kill('SIGTERM');
  rmSync(dataDir, { recursive: true, force: true });
}
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
  process.on(signal, () => {
    cleanup();
    process.exit(0);
  });
}
process.on('exit', cleanup);
// If the test runner is killed without a chance to stop us, do not leave a server (and its
// temp database) behind: exit when the parent process goes away.
const parent = process.ppid;
setInterval(() => {
  if (process.ppid !== parent) {
    cleanup();
    process.exit(0);
  }
}, 1000).unref();

const prepared = spawnSync(python, ['-m', 'app.db.prepare'], {
  cwd: backendDir,
  env,
  stdio: 'inherit',
});
if (prepared.status !== 0) {
  cleanup();
  process.exit(prepared.status ?? 1);
}

// Reading demo articles are seeded as drafts (the product never auto-publishes them). The
// browser suite needs readable articles, so this private test database publishes them here.
const publishDemoReading = `
import asyncio
from sqlalchemy import select
from app.db.models import ReadingArticle
from app.db.reading_seed import import_reading
from app.db.session import SessionLocal
from app.modules.reading import content

async def main():
    async with SessionLocal() as db:
        await import_reading(db)
        for article in (await db.scalars(select(ReadingArticle))).all():
            await content.set_status(db, article, "published")

asyncio.run(main())
`;
const seeded = spawnSync(python, ['-c', publishDemoReading], { cwd: backendDir, env, stdio: 'inherit' });
if (seeded.status !== 0) {
  cleanup();
  process.exit(seeded.status ?? 1);
}

child = spawn(
  python,
  [
    '-m',
    'uvicorn',
    'app.main:app',
    '--host',
    '127.0.0.1',
    '--port',
    port,
    '--log-level',
    'warning',
  ],
  { cwd: backendDir, env, stdio: 'inherit' },
);
child.on('exit', (code) => {
  cleanup();
  process.exit(code ?? 0);
});
