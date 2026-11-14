"""First-run setup for source downloads; portable Windows builds do not use pip."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if sys.version_info < (3, 11):  # noqa: UP036 -- bootstrap runs before dependency checks
        print("Потрібен Python 3.11 або новіший.")
        return 1
    directory = ROOT / ".desktop-venv"
    executable = directory / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not executable.exists():
        subprocess.run([sys.executable, "-m", "venv", str(directory)], check=True)
    marker = directory / "fleng-setup-v1"
    if not marker.exists():
        gui_packages = [] if sys.platform == "win32" else ["pywebview[qt]==6.2.1"]
        print("Перший запуск: встановлюємо залежності Fleng. Потрібен інтернет.", flush=True)
        subprocess.run(
            [str(executable), "-m", "pip", "install", "-e", str(ROOT / "backend"), *gui_packages],
            check=True,
        )
        marker.touch()
    return subprocess.call([str(executable), str(ROOT / "desktop/main.py")], cwd=ROOT)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError:
        print("Не вдалося підготувати Fleng. Перевір інтернет і прочитай DESKTOP-UA.md.")
        raise SystemExit(1) from None
