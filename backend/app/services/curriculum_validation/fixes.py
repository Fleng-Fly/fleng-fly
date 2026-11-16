"""Create a new draft snapshot; no database or publication integration."""

import difflib
import hashlib
import json
from pathlib import Path

from app.db.curriculum import Curriculum

from .validator import validate


def apply_safe_fixes(source: Path, output: Path, expected_sha: str) -> dict:
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("Source SHA mismatch")
    if source.resolve() == output.resolve():
        raise ValueError("Output must be a separate draft")
    diff_path = output.with_suffix(output.suffix + ".diff")
    if output.exists() or diff_path.exists():
        raise ValueError("Refusing to overwrite a snapshot or diff")
    data = json.loads(raw)
    if data.get("status") != "draft" or any(
        c.get("status") != "draft" for c in data.get("courses", [])
    ):
        raise ValueError("Only draft snapshots may be normalized")
    audit = validate(source)
    if any(i.severity in {"critical", "high"} for i in audit.issues):
        raise ValueError("Blocking defects require review before safe normalization")
    for fix in audit.proposed_fixes:
        target = data
        for key in fix["path"][:-1]:
            target = target[key]
        if target[fix["path"][-1]] != fix["old"]:
            raise ValueError("Fix precondition failed")
        target[fix["path"][-1]] = fix["new"]
    # New snapshot must satisfy the existing import contract.
    Curriculum.model_validate(data)
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    diff = "".join(
        difflib.unified_diff(
            raw.decode().splitlines(keepends=True),
            encoded.splitlines(keepends=True),
            fromfile=source.name,
            tofile=output.name,
        )
    )
    # Recheck immediately before writes; exclusive creation prevents accidental overwrites.
    if source.read_bytes() != raw:
        raise ValueError("Source changed during validation")
    with output.open("x", encoding="utf-8") as handle:
        handle.write(encoded)
    with diff_path.open("x", encoding="utf-8") as handle:
        handle.write(diff)
    return dict(
        applied=len(audit.proposed_fixes),
        source_sha256=expected_sha,
        output_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
        diff=str(diff_path),
    )
