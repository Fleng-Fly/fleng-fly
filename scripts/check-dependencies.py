"""Check installed Python versions against committed constraints (no network or changes)."""

import json
from importlib import metadata
from pathlib import Path

import yaml
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
failures = []
for line in (ROOT / "backend/constraints.txt").read_text().splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    requirement = Requirement(line)
    if requirement.marker and not requirement.marker.evaluate():
        continue
    # uvloop is an optional Uvicorn extra unavailable on Windows.
    if requirement.name == "uvloop":
        import sys

        if sys.platform == "win32":
            continue
    try:
        version = metadata.version(requirement.name)
    except metadata.PackageNotFoundError:
        failures.append(f"Missing pinned package: {requirement.name}")
        continue
    if not requirement.specifier.contains(version):
        failures.append(
            f"{requirement.name}: installed {version}, expected {requirement.specifier}"
        )
# pnpm 12 stores tool metadata and workspace dependencies in separate YAML documents.
manifest = json.loads((ROOT / "package.json").read_text())
lock_documents = list(yaml.safe_load_all((ROOT / "pnpm-lock.yaml").read_text()))
manager = manifest.get("packageManager", "")
manager_pins = [
    doc.get("importers", {}).get(".", {}).get("packageManagerDependencies", {})
    for doc in lock_documents
    if doc
]
if not any(
    f"pnpm@{pin.get('pnpm', {}).get('version', '')}" == manager for pin in manager_pins
):
    failures.append("Pinned package manager differs between manifest and lock")
workspace = next(
    (
        doc["importers"]["."]
        for doc in lock_documents
        if doc and doc.get("importers", {}).get(".", {}).get("devDependencies")
    ),
    None,
)
if workspace is None:
    failures.append("Missing root dependency importer in pnpm-lock.yaml")
else:
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        declared = manifest.get(section, {})
        locked = workspace.get(section, {})
        if set(declared) != set(locked):
            failures.append(f"JS {section} manifest/lock names differ")
        for name, specifier in declared.items():
            pin = locked.get(name, {})
            if pin.get("specifier") != specifier:
                failures.append(f"JS lock specifier drift: {name}")
            installed = ROOT / "node_modules" / name / "package.json"
            if not installed.exists():
                failures.append(f"Missing JS package: {name}; run frozen pnpm install")
            elif (
                json.loads(installed.read_text())["version"]
                != pin.get("version", "").split("(")[0]
            ):
                failures.append(f"JS installed/lock version mismatch: {name}")
if failures:
    raise SystemExit("Dependency integrity failed:\n" + "\n".join(failures))
print("Python constraints and JS manifest/lock/installed versions match.")
