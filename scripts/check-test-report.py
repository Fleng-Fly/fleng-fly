"""Fail CI when a mandatory PostgreSQL suite contains no tests or unexecuted tests."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    cases = list(ET.parse(Path(sys.argv[1])).getroot().iter("testcase"))
    invalid = [case for case in cases if any(
        case.find(tag) is not None for tag in ("skipped", "failure", "error")
    )]
    required = {
        "test_postgres_migration_chain_and_drift",
        "test_migrated_database_import_and_learner_persistence",
        "test_asyncpg_transfer_and_learner_restore",
        "test_logical_backup_restore_and_authentication",
    }
    missing = required - {case.get("name") for case in cases}
    if not cases or invalid or missing:
        raise SystemExit(
            f"Mandatory PostgreSQL evidence failed: {len(cases)} tests, "
            f"{len(invalid)} skipped/failed/errored, {len(missing)} required cases missing"
        )
    print(f"Mandatory PostgreSQL evidence: {len(cases)} executed tests passed; no skips")


if __name__ == "__main__":
    main()
