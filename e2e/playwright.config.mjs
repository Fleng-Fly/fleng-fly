import { defineConfig, devices } from '@playwright/test';

const port = process.env.E2E_PORT ?? '3101';
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  outputDir: '../test-results',
  // Every test registers its own learner, so tests share no state and may run in any order.
  fullyParallel: true,
  workers: process.env.CI ? 2 : undefined,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  reporter: [['list']],
  use: { baseURL, locale: 'en-US', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'node e2e/server.mjs',
    cwd: '..',
    url: `${baseURL}/api/v1/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    gracefulShutdown: { signal: 'SIGTERM', timeout: 10_000 },
  },
});
