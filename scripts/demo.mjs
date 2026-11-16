// Prepare the local demo, start Fleng if needed, and check the presentation flow.
import { execFileSync, spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const port = process.env.PORT ?? '3001';
const base = `http://localhost:${port}`;
const credentialsFile = resolve(root, 'backend/data/demo-credentials.json');
const venvPython = resolve(
  root,
  'backend/.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
);
const accounts = [
  'beginner.demo@example.com',
  'active.demo@example.com',
  'advanced.demo@example.com',
];

async function request(path, options) {
  return fetch(`${base}${path}`, { signal: AbortSignal.timeout(3000), ...options });
}

async function isListening() {
  try {
    await request('/api/v1/health');
    return true;
  } catch {
    return false;
  }
}

async function waitForServer(child) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (child.exitCode !== null) throw new Error(`Server exited with code ${child.exitCode}`);
    if (await isListening()) return;
    await new Promise((done) => setTimeout(done, 500));
  }
  throw new Error('Server did not become ready within 20 seconds');
}

async function check() {
  const healthResponse = await request('/api/v1/health');
  const health = await healthResponse.json();
  if (!healthResponse.ok || health.service !== 'backend' || health.database !== 'up') {
    throw new Error('FastAPI or the database is not ready');
  }
  for (const path of ['/', '/login.html', '/dashboard.html', '/courses.html', '/lesson.html']) {
    if (!(await request(path)).ok) throw new Error(`Page failed: ${path}`);
  }
  const credentials = JSON.parse(readFileSync(credentialsFile, 'utf8'));
  for (const email of accounts) {
    const login = await request('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: credentials[email] }),
    });
    if (!login.ok) throw new Error(`Demo login failed: ${email}`);
    const { accessToken } = await login.json();
    const headers = { Authorization: `Bearer ${accessToken}` };
    const progressResponse = await request('/api/v1/progress/me', { headers });
    if (!progressResponse.ok) throw new Error(`Progress failed: ${email}`);
    const progress = await progressResponse.json();
    if (email === accounts[0] && (progress.xp !== 0 || progress.lessonsCompleted !== 0)) {
      throw new Error('Beginner Demo is no longer at its starting state');
    }
    if (email === accounts[1] && progress.xp < 1) {
      throw new Error('Active Demo has no completed exercises');
    }
    if (email === accounts[2] && progress.lessonsCompleted < 3) {
      throw new Error('Advanced Demo has insufficient lesson progress');
    }
    console.log(`✓ ${email}: ${progress.xp} XP, ${progress.lessonsCompleted} lessons`);
  }
  const coursesResponse = await request('/api/v1/courses');
  const courses = await coursesResponse.json();
  if (!coursesResponse.ok || courses.length < 2) throw new Error('Catalog is not ready');
  console.log(`✓ Landing, database, login, progress and ${courses.length} courses`);
}

let child;
try {
  if (!existsSync(venvPython)) {
    console.log('Installing backend dependencies…');
    execFileSync('npm', ['run', 'setup'], { cwd: root, stdio: 'inherit' });
  }
  console.log('Preparing persistent SQLite and demo accounts…');
  execFileSync('npm', ['run', 'demo:prepare'], { cwd: root, stdio: 'inherit' });
  if (await isListening()) {
    console.log(`Server already running at ${base}; checking it.`);
  } else {
    child = spawn(process.execPath, [resolve(root, 'scripts/dev.mjs')], {
      cwd: root,
      stdio: 'inherit',
    });
    await waitForServer(child);
  }
  await check();
  console.log(`Demo ready: ${base}`);
  if (child) {
    const stop = () => child.kill('SIGTERM');
    process.on('SIGINT', stop);
    process.on('SIGTERM', stop);
    await new Promise((done) => child.once('exit', done));
  }
} catch (error) {
  if (child) child.kill('SIGTERM');
  console.error(`Demo check failed: ${error.message}`);
  process.exitCode = 1;
}
