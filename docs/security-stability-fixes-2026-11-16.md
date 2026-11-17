# Fleng 1.0 security and stability follow-up

Status: partial implementation; two user-contract decisions are pending. No
commit, push, paid provider request, dependency installation or database upgrade
was performed. Learning logic, XP, courses and stylesheet design are unchanged.

## Rechecked findings and changes

- Confirmed immediate email update in `modules/users/router.py`. The proposed
  current-password/new-address verification contract is awaiting user approval;
  no email-change implementation or migration has been applied.
- Confirmed per-page refresh single-flight with no tab coordination. The browser
  API client now serializes cookie mutations with Web Locks on supporting
  browsers. Independent-tab regression checks use a shared rotating-cookie
  server model. The existing no-Web-Locks fallback remains pending approval of
  fail-closed behavior. Backend strict refresh replay detection is unchanged.
- Confirmed missing reset UI. Login now requests a reset through the existing
  API. The new reset page handles missing/expired/used tokens, mismatch,
  network errors, retry and success. Tokens stay in memory and are removed from
  the displayed URL; the page sets no-referrer. Existing backend single-use,
  expiry, rate-limit and session-revocation mechanisms remain in force.
- Confirmed opposite AI admission ordering. Chat and structured calls now reserve
  database capacity before taking the local provider guard, matching streaming.
  Local rejections release the unused reservation. Limits/timeouts are unchanged.
- Confirmed PostgreSQL-incompatible two-argument max in settlement. SQL CASE
  subtracts the output hold and floors at zero; regression executes the update
  through the database fixture and checks PostgreSQL compilation.
- Confirmed unconditional public-header Logout redirect. Failure now keeps the
  page/session state and displays an honest error with retry; only successful
  revocation redirects. A lost response does not prove whether revocation happened.

## Verification

- Targeted AI/provider/reset regressions: 186 passed.
- Full backend: 489 passed, 22 skipped, 2 failed, 68 warnings, 199.69 seconds.
  Failures are `test_install_manifest_and_icons` and
  `test_install_and_offline_routes` in unchanged `tests/test_pwa.py`: they expect
  the retired standalone manifest and manifest links. The unchanged production
  artifacts have an empty manifest and no installation links. These tests were
  not weakened or installation reintroduced as part of the security work.
- Frontend: all 6 files in `npm run frontend:test` pass; the new auth UI file
  includes 4 behavioral checks. Both `npm run test:pwa` retirement checks pass.
- Ruff passes. Mypy passes for 82 source files (existing annotation-unchecked
  note remains). Documentation contracts pass; `git diff --check` passes.
- Independent self-review checked reservation release, retained strict replay
  detection, credential storage, password-reset one-time semantics and ambiguous
  logout network failures. No schema/data change is needed for this subset.

## Remaining decisions and limits

Email change needs approval of a new expiring-token table/migration and API/UI
contract before implementation. Unsupported browsers still need an approved
refresh policy. Do not consider all six findings resolved yet.

Real browser layout, real SMTP delivery and live PostgreSQL were not verified.
PostgreSQL-dependent tests skip without TEST_DATABASE_URL. SMTP defaults disabled;
configure SMTP and public RESET_URL to deliver links. Existing query-token links
are accepted for compatibility; operators must protect/redact request URLs in
access logs. Existing access JWTs retain their configured expiry policy.
