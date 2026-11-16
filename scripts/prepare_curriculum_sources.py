"""Convert reviewed LOCAL official exports into an evidence JSONL (no network).

The JSONL remains a private audit cache. Never publish a combined dataset without
review of each record's attribution and share-alike obligations.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.curriculum import CONTENT, load_curriculum
from app.services.curriculum_validation.datasets import (
    file_sha,
    tatoeba_records,
    wiktextract_records,
)
from app.services.curriculum_validation.sources import SourceRegistry
from app.services.curriculum_validation.validator import canonical


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=CONTENT, help="Draft to select relevant records"
    )
    parser.add_argument("--license-reviewed", action="store_true", required=True)
    parser.add_argument(
        "--revision", required=True, help="Official release/dump identifier"
    )
    parser.add_argument("--output", type=Path, required=True, help="New evidence JSONL")
    parser.add_argument("--wiktextract", type=Path)
    parser.add_argument(
        "--wiktionary-license", choices=["CC BY-SA 4.0", "CC BY-SA 3.0"]
    )
    parser.add_argument(
        "--attribution", help="Reviewed Wiktionary attribution incl. history link"
    )
    parser.add_argument("--tatoeba-sentences", type=Path)
    parser.add_argument("--tatoeba-links", type=Path)
    parser.add_argument(
        "--tatoeba-licenses", type=Path, help="Reviewed per-sentence license JSON"
    )
    args = parser.parse_args()
    if bool(args.wiktextract) == bool(args.tatoeba_sentences):
        parser.error("Select one source per cache")
    if args.wiktextract and not (args.wiktionary_license and args.attribution):
        parser.error("Wiktextract requires explicit license and attribution")
    if args.tatoeba_sentences and not (args.tatoeba_links and args.tatoeba_licenses):
        parser.error("Tatoeba requires links and per-sentence reviewed licensing")
    try:
        content = load_curriculum(args.input)
        lessons = [l for c in content.courses for l in c.lessons]
        manifest = args.output.with_suffix(args.output.suffix + ".manifest.json")
        if args.output.exists() or manifest.exists():
            raise ValueError("Refusing to overwrite evidence or manifest")
        inputs = (
            [args.wiktextract]
            if args.wiktextract
            else [args.tatoeba_sentences, args.tatoeba_links, args.tatoeba_licenses]
        )
        input_hashes = {p.name: file_sha(p) for p in inputs}
        if args.wiktextract:
            records = list(
                wiktextract_records(
                    args.wiktextract,
                    {canonical(w.word) for l in lessons for w in l.vocabulary},
                    revision=args.revision,
                    license_name=args.wiktionary_license,
                    attribution=args.attribution,
                )
            )
        else:
            records = list(
                tatoeba_records(
                    args.tatoeba_sentences,
                    args.tatoeba_links,
                    args.tatoeba_licenses,
                    {canonical(e) for l in lessons for e in l.examples},
                    revision=args.revision,
                )
            )
        if not records:
            raise ValueError("No matching records; no cache written")
        encoded = "\n".join(r.model_dump_json() for r in records) + "\n"
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
        registry = SourceRegistry(args.output)
        with manifest.open("x", encoding="utf-8") as handle:
            json.dump(
                {
                    "revision": args.revision,
                    "license_reviewed": True,
                    "input_sha256": input_hashes,
                    "evidence": registry.metadata(),
                },
                handle,
                indent=2,
            )
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            f"Dataset preparation failed: {type(exc).__name__}: {exc}", file=sys.stderr
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
