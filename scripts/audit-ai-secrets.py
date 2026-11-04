"""Read-only secret scan; prints locations/counts, never secret values or matching lines."""

import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
patterns = [re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{20,}")]
values = [os.environ.get("OPENROUTER_API_KEY", "")]
for location in (ROOT / ".env", ROOT / "backend/.env"):
    if location.is_file():
        for line in location.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENROUTER_API_KEY":
                values.append(value.strip().strip("\"'"))
# Known local values are compared in memory and are never printed.
for value in values:
    if len(value) >= 16 and not any(word in value.lower() for word in ("example", "change-me", "your-key", "placeholder")):
        patterns.append(re.compile(re.escape(value.encode())))

tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
paths = {os.fsdecode(path) for path in tracked if path}
paths.update(str(path.relative_to(ROOT)) for path in (ROOT / "frontend").rglob("*") if path.is_file())
for directory in (ROOT / "logs", ROOT / "backend/logs"):
    if directory.is_dir():
        paths.update(str(path.relative_to(ROOT)) for path in directory.rglob("*.log"))
findings = []
checked = 0
for name in sorted(paths):
    path = ROOT / name
    if not path.is_file():
        continue
    data = path.read_bytes()
    checked += 1
    if any(pattern.search(data) for pattern in patterns):
        findings.append(("working tree", name))
    if name.encode() in tracked:
        staged = subprocess.run(["git", "show", ":" + name], cwd=ROOT, capture_output=True)
        if staged.returncode == 0 and any(pattern.search(staged.stdout) for pattern in patterns):
            findings.append(("Git index", name))
print(f"Scanned {checked} files plus Git index; concrete OpenRouter secret findings: {len(findings)}")
for source, name in findings:
    print(f"Potential secret location: {source}: {name}")
raise SystemExit(bool(findings))
