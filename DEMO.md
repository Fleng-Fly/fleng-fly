# Fleng live demo

## Prepare once

Use Node 20+ and Python 3.11+. From the repository root:

```bash
./start.sh                # prepare, start, and check http://localhost:3001
```

The script installs backend dependencies if needed. It checks the landing page,
database, catalog and login/progress
for all three demo accounts. If the server is already running, it checks that
server and exits. Use `npm run demo:prepare` for preparation only, or
`npm run dev` to start without the account checks. `npm run dev` also applies
pending SQLite migrations. It preserves existing
users and progress. The demo preparation command is explicit and repeatable;
it refuses existing account email addresses without matching local credentials.
The environment is `APP_ENV=development` unless set otherwise, and the default
database is the persistent, Git-ignored `backend/data/fleng.db`. Keep
`DATABASE_URL` unset for this walkthrough. Neither the existing learning flow
nor startup needs an AI API key or PostgreSQL server.

## Accounts

Passwords are generated per machine in the Git-ignored
`backend/data/demo-credentials.json` (file mode 0600). Open that file locally
before presenting. Never copy it into slides or Git. The file contains:

| Learner | Email | Starting state |
| --- | --- | --- |
| Beginner Demo | beginner.demo@example.com | A1, 0 XP, no lessons |
| Active Demo | active.demo@example.com | Started English Foundations, completed exercises, XP |
| Advanced Demo | advanced.demo@example.com | Four completed lessons, visible course progress |

Demo preparation retains account progress on repeat runs. To show a fresh
exercise, use the Beginner account or an uncompleted lesson in Active.

## Presentation walkthrough (about four minutes)

1. **Landing (30 s):** Open `/`, point out the dark learning interface and live backend status.
2. **Beginner (45 s):** Log in with Beginner Demo. Show 0 XP on the dashboard, then open Courses → English Foundations → Greetings and introductions. Read the theory.
3. **Practice (90 s):** Answer the first question incorrectly, then correctly. Show feedback and the XP increase. Refresh the lesson to show the saved answer. Submitting the same correct answer again adds no XP.
4. **Progress (45 s):** Return to the dashboard, log out, and log back in. The progress remains.
5. **Switch learner (45 s):** Log out and sign in as Advanced Demo. Show four completed lessons and progress in two courses. Open Settings to show the account profile.

## Troubleshooting

- If port 3001 is busy, stop the existing server or set `PORT=3002 npm run dev` and open that port.
- If the catalog is empty, run `npm run demo:prepare` again. It updates only the seed catalog and the three identified fictional accounts.
- If login fails, use the exact password in the local credentials file. The seed refuses to change an existing account's password.
- If startup reports a database error, check `APP_ENV` and `DATABASE_URL`. The walkthrough uses `APP_ENV=development` and local SQLite.
