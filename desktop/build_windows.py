"""Build a portable Windows x64 folder from verified runtime and wheel inputs.

Run with Python containing ziglang. No global installation or user data enters
the distributable. Build inputs are recorded with SHA-256 checksums.
"""

from __future__ import annotations

import argparse
import email
import hashlib
import io
import json
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
PYTHON_SHA256 = "90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--wheels", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if digest(args.runtime) != PYTHON_SHA256:
        raise SystemExit("Python runtime SHA-256 does not match the official release.")
    if args.output.exists():
        raise SystemExit("Output directory already exists; choose a new empty destination.")
    args.output.mkdir(parents=True)
    # Only committed source enters a release. Do not recursively copy a worktree
    # which might contain .env, local databases, virtualenvs or editor files.
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
    import tarfile

    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(args.output, filter="data")
    runtime = args.output / "runtime"
    runtime.mkdir()
    with zipfile.ZipFile(args.runtime) as source:
        source.extractall(runtime)
    packages = runtime / "Lib/site-packages"
    packages.mkdir(parents=True)
    inventory = []
    versions = []
    dependencies = {}
    for wheel in sorted(args.wheels.glob("*.whl")):
        with zipfile.ZipFile(wheel) as source:
            metadata_name = next(n for n in source.namelist() if n.endswith(".dist-info/METADATA"))
            metadata = email.message_from_bytes(source.read(metadata_name))
            versions.append(f"{metadata['Name']}=={metadata['Version']}")
            dependencies[canonicalize_name(metadata["Name"])] = metadata
            for member in source.infolist():
                if member.is_dir():
                    continue
                path = Path(member.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise SystemExit("Unsafe wheel path")
                parts = path.parts
                if parts[0].endswith(".data"):
                    if len(parts) < 3 or parts[1] not in ("purelib", "platlib"):
                        continue
                    path = Path(*parts[2:])
                target = packages / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read(member))
        inventory.append({"wheel": wheel.name, "sha256": digest(wheel)})
    environment = {
        **default_environment(),
        "python_version": "3.14",
        "python_full_version": "3.14.10",
        "sys_platform": "win32",
        "platform_system": "Windows",
        "platform_machine": "AMD64",
        "os_name": "nt",
        "extra": "",
    }
    for metadata in dependencies.values():
        for text in metadata.get_all("Requires-Dist", []):
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate(environment):
                continue
            dependency = dependencies.get(canonicalize_name(requirement.name))
            if dependency is None or not requirement.specifier.contains(dependency["Version"]):
                raise SystemExit(f"Unsatisfied Windows dependency: {metadata['Name']} -> {text}")
    (runtime / "python314._pth").write_text(
        "python314.zip\n.\nLib/site-packages\n..\n../backend\nimport site\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ziglang",
            "cc",
            "-target",
            "x86_64-windows-gnu",
            "-O2",
            "-s",
            "-municode",
            "-Wl,--subsystem,windows",
            str(ROOT / "desktop/launcher.c"),
            "-luser32",
            "-o",
            str(args.output / "Fleng.exe"),
        ],
        check=True,
    )
    data = (args.output / "Fleng.exe").read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if struct.unpack_from("<H", data, pe + 24 + 68)[0] != 2:
        raise SystemExit("The launcher must use the Windows GUI subsystem.")
    (args.output / "WINDOWS-DEPENDENCIES.txt").write_text(
        "\n".join(versions) + "\n", encoding="utf-8"
    )
    (args.output / "BUILD-MANIFEST.json").write_text(
        json.dumps(
            {
                "python": "3.14.10 x64",
                "python_url": "https://www.python.org/ftp/python/3.14.10/"
                "python-3.14.10-embed-amd64.zip",
                "python_sha256": PYTHON_SHA256,
                "source_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "wheels": inventory,
                "windows_dependency_graph_validated": True,
                "windows_gui_tested": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # Every third-party wheel retains its dist-info and bundled licenses. Python
    # retains LICENSE.txt. Own launcher and application source are included too.
    shutil.copyfile(ROOT / "DESKTOP-UA.md", args.output / "ПОЧНИ-ТУТ.txt")
    print(f"Portable Windows folder prepared: {args.output}")


if __name__ == "__main__":
    main()
