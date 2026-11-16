# Documentation map

The [developer documentation index](../docs/README.md) is the navigation entry point for twelve numbered sections. Existing root technical documents and reports remain at their original paths; the [preservation register](../docs/12-reference/documentation-migration.md) maps every file and explains stale historical statements.

API authority: runtime FastAPI routes/Pydantic schemas. Database authority: SQLAlchemy metadata plus Alembic upgrades. Configuration authority: Settings source. Documentation checks compare those contracts without querying learner data.

The documentation-only change adds no application module or data-flow change. scripts/check-docs.py validates local links and, optionally, API examples/contracts/model columns/environment inventory. [Validation evidence](../docs/12-reference/validation-report.md) records current versus skipped/not-run checks.
