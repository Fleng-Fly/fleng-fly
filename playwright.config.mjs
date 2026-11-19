// Lets `npx playwright test` work from the repository root. The real configuration (baseURL,
// isolated backend with a throwaway SQLite database, webServer) lives in e2e/playwright.config.mjs;
// paths are re-anchored here because Playwright resolves them against the config file's folder.
import { fileURLToPath } from 'node:url';
import base from './e2e/playwright.config.mjs';

const root = fileURLToPath(new URL('.', import.meta.url));
export default {
  ...base,
  testDir: `${root}e2e`,
  outputDir: `${root}test-results`,
  webServer: { ...base.webServer, cwd: root },
};
