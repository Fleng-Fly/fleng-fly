# Production checklist

These are release recommendations, not evidence of production readiness.

1. Verify deployed revision and build/start commands, including static/migration files.
2. Configure production secrets, HTTPS origins, cookies, ingress trust and durable storage.
3. Back up and apply migrations once; compare current/head.
4. Check ready and static pages; SELECT 1 does not prove schema completeness.
5. Register/login/reload to test refresh; reject untrusted Origin.
6. Submit twice and verify once-only XP/dashboard/streak/leaderboard, including restart persistence.
7. Check private paths and frontend-only publication; validate Netlify proxy if used.
8. Test real SSE/SMTP only if enabled, including a usable reset UI.
9. Complete backup/restore drill and record passed/failed/skipped/not-run checks.
10. Plan compatible code/schema rollback without reset/stamp/delete shortcuts.

No deployment, paid calls or production writes were performed by this documentation task.

[Section index](README.md) · [Documentation home](../README.md)
