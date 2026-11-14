"""Read-only environment diagnostics. Does not read accounts or secrets."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desktop.chromium import find_browser  # noqa: E402
from desktop.runtime import default_data_dir  # noqa: E402

print("Fleng diagnostics")
print("Python:", sys.version)
print("Platform:", sys.platform)
try:
    print("Browser:", find_browser())
except RuntimeError as exc:
    print("Browser:", exc)
for name in ("fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "argon2", "pydantic_core"):
    try:
        importlib.import_module(name)
        print(name + ": OK")
    except Exception as exc:
        print(name + ":", type(exc).__name__, str(exc))
print("Logs:", default_data_dir())
