"""Mandatory PostgreSQL evidence must fail closed for missing or unexecuted tests."""

import runpy
import sys
from pathlib import Path

import pytest

REQUIRED = [
    "test_postgres_migration_chain_and_drift",
    "test_migrated_database_import_and_learner_persistence",
    "test_asyncpg_transfer_and_learner_restore",
    "test_logical_backup_restore_and_authentication",
    "test_postgres_startup_account_progress_and_cards_survive_new_app_process",
    "test_failed_fresh_postgres_bootstrap_rolls_back_all_schema_and_seed",
]


@pytest.mark.parametrize("damage", ["empty", "missing", "skipped", "failure", "error", None])
def test_postgres_evidence_gate(tmp_path, monkeypatch, damage):
    names = (
        REQUIRED
        if damage not in {"empty", "missing"}
        else REQUIRED[: 0 if damage == "empty" else 1]
    )
    cases = [f'<testcase name="{name}"></testcase>' for name in names]
    if damage in {"skipped", "failure", "error"}:
        cases[0] = cases[0].replace("</testcase>", f"<{damage}/></testcase>")
    report = tmp_path / "results.xml"
    report.write_text("<testsuites><testsuite>" + "".join(cases) + "</testsuite></testsuites>")
    monkeypatch.setattr(sys, "argv", ["check-test-report.py", str(report)])
    script = Path(__file__).resolve().parents[2] / "scripts/check-test-report.py"
    if damage:
        with pytest.raises(SystemExit, match="Mandatory PostgreSQL evidence failed"):
            runpy.run_path(str(script), run_name="__main__")
    else:
        runpy.run_path(str(script), run_name="__main__")


@pytest.mark.parametrize("reason", ["Non-POSIX platform guard", "missing PostgreSQL"])
def test_evidence_gate_only_exempts_exact_nonapplicable_platform_guard(
    tmp_path, monkeypatch, reason
):
    cases = "".join(f'<testcase name="{name}"/>' for name in REQUIRED)
    cases += (
        '<testcase classname="tests.test_curriculum_preview" '
        'name="test_preview_refuses_platform_without_private_permissions">'
        f'<skipped message="{reason}"/></testcase>'
    )
    report = tmp_path / "report.xml"
    report.write_text("<testsuites><testsuite>" + cases + "</testsuite></testsuites>")
    monkeypatch.setattr(sys, "argv", ["check-test-report.py", str(report)])
    script = Path(__file__).resolve().parents[2] / "scripts/check-test-report.py"
    if reason == "Non-POSIX platform guard":
        runpy.run_path(str(script), run_name="__main__")
    else:
        with pytest.raises(SystemExit):
            runpy.run_path(str(script), run_name="__main__")
