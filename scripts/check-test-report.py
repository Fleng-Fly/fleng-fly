"""Fail CI when a mandatory PostgreSQL suite contains no tests or unexecuted tests."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    cases = list(ET.parse(Path(sys.argv[1])).getroot().iter("testcase"))

    def expected_platform_skip(case):
        skipped = case.find("skipped")
        return (
            case.get("classname") == "tests.test_curriculum_preview"
            and case.get("name")
            == "test_preview_refuses_platform_without_private_permissions"
            and skipped is not None
            and skipped.get("message") == "Non-POSIX platform guard"
        )

    invalid = [
        case
        for case in cases
        if (
            case.find("failure") is not None
            or case.find("error") is not None
            or (case.find("skipped") is not None and not expected_platform_skip(case))
        )
    ]
    required = {
        "test_postgres_migration_chain_and_drift",
        "test_migrated_database_import_and_learner_persistence",
        "test_asyncpg_transfer_and_learner_restore",
        "test_logical_backup_restore_and_authentication",
        "test_postgres_startup_account_progress_and_cards_survive_new_app_process",
        "test_failed_fresh_postgres_bootstrap_rolls_back_all_schema_and_seed",
    }
    missing = required - {case.get("name") for case in cases}
    if not cases or invalid or missing:
        raise SystemExit(
            f"Mandatory PostgreSQL evidence failed: {len(cases)} tests, "
            f"{len(invalid)} skipped/failed/errored, {len(missing)} required cases missing"
        )
    expected_skips = sum(expected_platform_skip(case) for case in cases)
    print(
        f"Mandatory PostgreSQL evidence: {len(cases) - expected_skips} executed tests passed; "
        f"{expected_skips} non-applicable platform guard skipped; no mandatory skips"
    )


if __name__ == "__main__":
    main()
