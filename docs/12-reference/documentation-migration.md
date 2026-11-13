# Documentation preservation register

No existing technical document was moved/deleted/rewritten. Original URLs and uncommitted author work remain intact. Numbered pages consolidate current navigation/contracts; retained detailed reports remain dated evidence, not current test/hosting claims.

| Existing file | Current guide | Accuracy/reuse decision |
| --- | --- | --- |
| [ai-assistant-integration.md](../ai-assistant-integration.md) | [Current guide](../07-ai/ai-tutor.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [ai-security-audit.md](../ai-security-audit.md) | [Current guide](../10-testing/README.md) | Historical implementation/verification report preserved; new checks recorded separately. |
| [ai.md](../ai.md) | [Current guide](../07-ai/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [api.md](../api.md) | [Current guide](../03-backend/api-overview.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [architecture.md](../architecture.md) | [Current guide](../02-architecture/system-overview.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [authentication.md](../authentication.md) | [Current guide](../08-security/authentication.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [backend-completion-report.md](../backend-completion-report.md) | [Current guide](../10-testing/README.md) | Historical implementation/verification report preserved; new checks recorded separately. |
| [backend-stabilization-report.md](../backend-stabilization-report.md) | [Current guide](../10-testing/README.md) | Historical implementation/verification report preserved; new checks recorded separately. |
| [backend.md](../backend.md) | [Current guide](../03-backend/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [courses-implementation.md](../courses-implementation.md) | [Current guide](../10-testing/README.md) | Historical implementation/verification report preserved; new checks recorded separately. |
| [curriculum-a0-b2.md](../curriculum-a0-b2.md) | [Current guide](../06-learning/curriculum-a0-b2.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [curriculum-content-quality.md](../curriculum-content-quality.md) | [Current guide](../06-learning/curriculum-validation.md) | Draft/editorial/evidence snapshot preserved; not linguistic/publication approval. |
| [curriculum-sources-and-licenses.md](../curriculum-sources-and-licenses.md) | [Current guide](../06-learning/curriculum-validation.md) | Draft/editorial/evidence snapshot preserved; not linguistic/publication approval. |
| [curriculum-validation-report.md](../curriculum-validation-report.md) | [Current guide](../06-learning/curriculum-validation.md) | Draft/editorial/evidence snapshot preserved; not linguistic/publication approval. |
| [curriculum-validator.md](../curriculum-validator.md) | [Current guide](../06-learning/curriculum-validation.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [curriculum-visual-review.md](../curriculum-visual-review.md) | [Current guide](../06-learning/curriculum-preview.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [database.md](../database.md) | [Current guide](../05-database/schema.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [deployment.md](../deployment.md) | [Current guide](../09-deployment/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [development.md](../development.md) | [Current guide](../01-getting-started/development.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [frontend.md](../frontend.md) | [Current guide](../04-frontend/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [leaderboard-hosting-report.md](../leaderboard-hosting-report.md) | [Current guide](../09-deployment/troubleshooting.md) | Historical diagnosis; live host state not inferred. |
| [local-postgres-verification.md](../local-postgres-verification.md) | [Current guide](../10-testing/README.md) | Historical implementation/verification report preserved; new checks recorded separately. |
| [render-https-origin-403.md](../render-https-origin-403.md) | [Current guide](../09-deployment/troubleshooting.md) | Historical diagnosis; live host state not inferred. |
| [render-registration-origin-403.md](../render-registration-origin-403.md) | [Current guide](../09-deployment/troubleshooting.md) | Historical diagnosis; live host state not inferred. |
| [render-sqlite-registration-diagnostics.md](../render-sqlite-registration-diagnostics.md) | [Current guide](../09-deployment/troubleshooting.md) | Historical diagnosis; live host state not inferred. |
| [render-sqlite-startup.md](../render-sqlite-startup.md) | [Current guide](../09-deployment/troubleshooting.md) | Historical diagnosis; live host state not inferred. |
| [security.md](../security.md) | [Current guide](../08-security/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [testing.md](../testing.md) | [Current guide](../10-testing/README.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |
| [vocabulary-flashcards-api.md](../vocabulary-flashcards-api.md) | [Current guide](../06-learning/flashcards.md) | Detailed source retained; current guide consolidates behavior. Historical counts/heads require date context. |

## Contradictions found

- Old development prose names head 20261018_1200; current head is 20261110_1400.
- Old plans mark password reset/gamification/AI tests absent although current routers/tests implement them.
- Security plan marks body limits pending although BodyLimitMiddleware is installed; its broad anti-enumeration claim conflicts with duplicate-email registration.
- Historical test totals are dated results, not today's suite status.
- Deployment reports mix historical public checks and no-dashboard context; recorded URLs do not prove current deployed behavior.
- Netlify static publication exists but the checked-in API proxy is disabled.
- Flashcard backend does not imply dedicated UI/test grading/XP; A0 schema support does not publish drafts.
- Old /login and machine-specific paths should use /login.html and actual checkout-relative commands.
- Explicit async in-memory Settings URL duplicates the driver even though direct ORM test fixtures can work.

Retain operational evidence without duplicating full reports in new guides. Current source and the numbered guides take precedence over old stage checkboxes. External links/live hosts were not revalidated by preserving documents.
