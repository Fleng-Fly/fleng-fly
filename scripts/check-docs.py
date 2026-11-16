"""Check repository Markdown links; optionally compare documented runtime contracts.

Run python3 scripts/check-docs.py for links, or backend/.venv/bin/python
scripts/check-docs.py --contracts for API/schema/model/configuration checks too.
No database connection, network request or private configuration read is needed
in contract mode: environment and Settings are isolated before importing app.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def stripped(text: str) -> str:
    return re.sub(r"^(`{3,}|~{3,}).*?^\1\s*$", "", text, flags=re.M | re.S)


def anchors(path: Path) -> set[str]:
    result: set[str] = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", stripped(path.read_text()), re.M):
        heading = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug + (f"-{count}" if count else ""))
    result.update(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', path.read_text()))
    return result


def links() -> list[str]:
    failures: list[str] = []
    checked = 0
    paths = sorted((ROOT / "docs").rglob("*.md"))
    for path in paths:
        text = stripped(path.read_text())
        targets = re.findall(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", text)
        targets += re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", text, re.M)
        for raw in targets:
            target = raw.strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("//"):
                continue
            checked += 1
            resolved = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing target {target}")
            elif parsed.fragment and resolved.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(resolved):
                    failures.append(f"{path.relative_to(ROOT)}: missing anchor {target}")
        if not text.strip():
            failures.append(f"{path.relative_to(ROOT)}: empty document")
        if path.read_text().count("```") % 2:
            failures.append(f"{path.relative_to(ROOT)}: unbalanced code fences")
    print(f"Markdown: {len(paths)} files, {checked} local links checked")
    return failures


def contracts() -> list[str]:
    # Do not load private .env values or connect to application storage.
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.config import Settings

    Settings.model_config["env_file"] = None
    for field in Settings.model_fields:
        os.environ.pop(field.upper(), None)
    os.environ.update(APP_ENV="development", DATABASE_URL="sqlite:///:memory:")
    from app.db import models  # noqa: F401
    from app.db.base import Base
    from app.main import app
    from pydantic import TypeAdapter

    failures: list[str] = []
    spec = app.openapi()
    expected = {(m.upper(), p) for p, ops in spec["paths"].items() for m in ops}
    documented: list[tuple[str, str]] = []
    for path in (ROOT / "docs/03-backend").glob("*-api.md"):
        text = path.read_text()
        documented.extend(re.findall(r"^## `(\w+) (/api/v1[^`]*)`", text, re.M))
    if set(documented) != expected or len(documented) != len(expected):
        failures.append(
            f"API operation mismatch: missing={expected - set(documented)}, "
            f"extra={set(documented) - expected}, "
            f"duplicates={len(documented) - len(set(documented))}"
        )
    schema_text = (ROOT / "docs/03-backend/api-schemas.md").read_text()
    found = dict(re.findall(r"^## (\w+)\n\n```json\n(.*?)\n```", schema_text, re.M | re.S))
    for name, value in spec["components"]["schemas"].items():
        if name not in found or json.loads(found[name]) != value:
            failures.append(f"API schema drift: {name}")
    model_text = (ROOT / "docs/05-database/schema.md").read_text()
    for mapper in Base.registry.mappers:
        name = mapper.class_.__name__
        match = re.search(rf"^## {name}\n(.*?)(?=^## |\Z)", model_text, re.M | re.S)
        if not match:
            failures.append(f"Missing model: {name}")
            continue
        for col in mapper.local_table.columns:
            if f"| {col.name} | {col.type} | {col.nullable} |" not in match[1]:
                failures.append(f"Column drift: {name}.{col.name}")
    config_text = (ROOT / "docs/12-reference/configuration-reference.md").read_text()
    documented_settings = set(re.findall(r"^\| `([A-Z_]+)` \|", config_text, re.M))
    if documented_settings != {name.upper() for name in Settings.model_fields}:
        failures.append("Settings environment inventory drift")
    import importlib

    from pydantic import BaseModel

    model_types = {}
    for schema_file in (ROOT / "backend/app/modules").glob("*/schemas.py"):
        module = importlib.import_module(f"app.modules.{schema_file.parent.name}.schemas")
        for name, value in vars(module).items():
            if isinstance(value, type) and issubclass(value, BaseModel):
                model_types[name] = value

    def contract_type(schema):
        if "$ref" in schema:
            return model_types.get(schema["$ref"].split("/")[-1])
        if schema.get("type") == "array":
            item = contract_type(schema["items"])
            return list[item] if item else None
        return None

    example_count = 0
    for route_path, operations in spec["paths"].items():
        for method, operation in operations.items():
            heading = f"## `{method.upper()} {route_path}`"
            for path in (ROOT / "docs/03-backend").glob("*-api.md"):
                text = path.read_text()
                if heading not in text:
                    continue
                block = text.split(heading, 1)[1].split("\n## ", 1)[0]
                request = re.search(r"--data '([^']+)'", block)
                body = (
                    operation.get("requestBody", {})
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                )
                success = next(
                    (r for c, r in operation["responses"].items() if c.startswith("2")), {}
                )
                response_schema = (
                    success.get("content", {}).get("application/json", {}).get("schema", {})
                )
                response = re.search(r"Synthetic response shape.*?```json\n(.*?)\n```", block, re.S)
                try:
                    if request:
                        model = contract_type(body)
                        if model is None:
                            raise ValueError("No request model found")
                        TypeAdapter(model).validate_python(json.loads(request[1]))
                        example_count += 1
                    if response:
                        model = contract_type(response_schema)
                        if model is None:
                            raise ValueError("No response model found")
                        TypeAdapter(model).validate_python(json.loads(response[1]))
                        example_count += 1
                except Exception as exc:
                    failures.append(
                        f"Example validation failed {method.upper()} {route_path}: "
                        f"{type(exc).__name__}"
                    )
    if not example_count:
        failures.append("No API examples validated")
    print(
        f"Contracts: {len(expected)} operations, {len(found)} named schemas, "
        f"{len(list(Base.registry.mappers))} models, "
        f"{len(documented_settings)} Settings fields, {example_count} examples validated"
    )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", action="store_true")
    args = parser.parse_args()
    failures = links()
    if args.contracts:
        failures += contracts()
    for failure in failures:
        print(f"ERROR: {failure}")
    print(f"Result: {len(failures)} failures")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
