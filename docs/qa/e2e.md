# Browser E2E tests: core student journey

Real-browser tests (Playwright, Chromium) for the main learning path. They use the real FastAPI
backend, the real static frontend and a temporary SQLite database. No API response is mocked or
intercepted.

## What is covered

`e2e/learning-journey.spec.mjs`, 9 tests:

| Area                     | Test                                                                                                                                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Registration and sign-in | Register through the UI, land on the dashboard, stay signed in after a reload                                                                                                                        |
|                          | Registering the same email twice is refused                                                                                                                                                          |
|                          | Log out, a wrong password is refused, then log in again                                                                                                                                              |
| Catalog                  | Course cards match what the real `/courses` API publishes; level filter and search; open a course and its first lesson                                                                               |
| Exercise and XP          | A correct answer awards +1 XP once; progress and the saved answer survive a reload; answering the same exercise again does not pay again; the total matches on the lesson, dashboard and course page |
|                          | A wrong answer earns nothing and the exercise can still be completed afterwards                                                                                                                      |
|                          | XP belongs to the learner who earned it (a second learner has 0)                                                                                                                                     |
| Logout and private pages | After logout the server returns 401 for `/users/me` and `/auth/refresh`, and every private page redirects to the login page                                                                          |
|                          | An anonymous visitor is redirected from every private page and gets 401 from private APIs                                                                                                            |

The journey uses the published seed course "English Foundations" and its first lesson
("Greetings and introductions"; the correct answer to question 1 is "Hello").

## Running

```bash
npm run setup                 # backend virtualenv, once
pnpm install --frozen-lockfile
npm run test:e2e:install      # downloads Chromium, once
npm run test:e2e
```

Settings (environment variables):

- `E2E_PYTHON`: Python to run the backend with (default `backend/.venv`).
- `E2E_PORT`: server port (default `3101`).
- `PLAYWRIGHT_BROWSERS_PATH`: where Playwright looks for browsers.

## Isolation and cleanup

- `e2e/server.mjs` creates a private temp directory, points `DATABASE_URL` at a new SQLite file in
  it, runs the normal `app.db.prepare` step (migrations and the published catalog), and starts
  uvicorn on `127.0.0.1`. AI and password-reset email are disabled, and only this process's
  environment is overridden.
- The temp directory is removed when the server stops. A watchdog also stops it if the test runner
  is killed.
- Every test registers its own learner with a random email, so tests share no state. They were run
  in three sequential rounds, in parallel with four workers, and one at a time, with identical
  results.
- The registration and login throttles (10 registrations per IP per hour by default) are a real
  security control that the backend tests cover. The test server raises them only through the
  app's own settings (`AUTH_REGISTER_IP_PER_HOUR`, `AUTH_LOGIN_IP_PER_MINUTE`); the suite
  registers more learners than the default allows.

## Limits

- **Not in CI yet.** `.github/workflows/database.yml` does not install Node dependencies or the
  browser. Adding it needs a pnpm install and `playwright install --with-deps chromium` step.
- Chromium and a desktop viewport only. No mobile viewport, no Firefox or WebKit.
- The tests depend on the seed catalog text ("English Foundations", "Hello").
- Not covered: vocabulary review, AI tutor, password reset, settings, the A0–B2 lessons. Streaks and
  achievements were not tested.
- On an OS Playwright does not officially support, `playwright install` may unpack an incomplete
  browser. If Chromium fails to launch, unpack the downloaded archive manually or install a
  supported browser and set `PLAYWRIGHT_BROWSERS_PATH`.
