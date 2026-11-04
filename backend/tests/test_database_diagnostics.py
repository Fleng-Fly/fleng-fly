"""SQLite exception diagnostics must never echo user-controlled messages/SQL."""

import json
import sqlite3

import pytest
from sqlalchemy.exc import OperationalError

from app.db.diagnostics import error_details


@pytest.mark.parametrize(
    ("message", "reason"),
    [
        ("no such table: private@example.com", "missing_table"),
        ("no such column: private@example.com", "missing_column"),
        ("no such function: private@example.com", "missing_function"),
        ("attempt to write a readonly database", "readonly"),
        ("database is locked", "locked"),
        ("unable to open database file", "cannot_open"),
        ("database or disk is full", "disk_full"),
        ('near "RETURNING": syntax error', "sql_syntax"),
        ("private@example.com", "other_sqlite_error"),
    ],
)
def test_error_classification_is_allowlisted(message, reason):
    cause = sqlite3.OperationalError(message)
    cause.sqlite_errorcode = sqlite3.SQLITE_ERROR
    cause.sqlite_errorname = "SQLITE_ERROR"
    error = OperationalError("private SQL", {"password": "private password"}, cause)
    details = error_details(error)
    assert details == {
        "exception": "OperationalError",
        "sqlite_code": sqlite3.SQLITE_ERROR,
        "sqlite_name": "SQLITE_ERROR",
        "reason": reason,
    }
    assert "private" not in json.dumps(details)


def test_non_sqlite_exception_is_not_dumped():
    assert error_details(OSError("private credentials")) == {"exception": "OSError"}
