"""Offline curriculum QA. Exit 0: no blocking defects; 1: defects; 2: input/config error.

Warnings and unavailable linguistic evidence do not imply publication approval.
Use the backend virtualenv Python. No database is opened, including in fix mode.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.curriculum import CONTENT
from app.services.curriculum_validation.fixes import apply_safe_fixes
from app.services.curriculum_validation.reports import markdown
from app.services.curriculum_validation.sources import SourceRegistry
from app.services.curriculum_validation.validator import validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="All courses (default)")
    selection.add_argument("--level", choices=["A0", "A1", "A2", "B1", "B2"])
    parser.add_argument("--input", type=Path, default=CONTENT)
    parser.add_argument(
        "--dataset",
        type=Path,
        action="append",
        help="Reviewed provenance JSONL; see source docs",
    )
    parser.add_argument(
        "--check-sources", action="store_true", help="Show local dataset status only"
    )
    parser.add_argument("--report", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path, help="Write report to a new file")
    parser.add_argument(
        "--suggest-fixes",
        action="store_true",
        help="Include safe proposals (no writes)",
    )
    parser.add_argument("--apply-safe-fixes", type=Path, metavar="NEW_DRAFT")
    parser.add_argument(
        "--expected-sha", help="Raw file SHA-256 required for fix application"
    )
    parser.add_argument(
        "--ai-review", action="store_true", help="Explicitly allow bounded paid review"
    )
    parser.add_argument("--ai-budget-usd", type=float, default=0)
    parser.add_argument(
        "--ai-price-ceiling",
        type=float,
        default=0,
        help="Operator-confirmed maximum USD per token (input/output)",
    )
    parser.add_argument("--ai-max-requests", type=int, default=2)
    parser.add_argument("--ai-max-tokens", type=int, default=600)
    parser.add_argument("--ai-retries", type=int, default=0)
    parser.add_argument("--ai-timeout", type=float, default=20)
    args = parser.parse_args()
    if args.apply_safe_fixes and (
        not args.expected_sha or args.ai_review or args.level
    ):
        parser.error(
            "Fix mode requires --expected-sha and excludes --level/--ai-review"
        )
    try:
        registry = SourceRegistry(args.dataset)
        if args.check_sources:
            print(json.dumps(registry.metadata()))
            return 0 if registry.status == "available" else 1
        if args.output and (
            args.output.resolve() == args.input.resolve() or args.output.exists()
        ):
            raise ValueError("Report output must be a new file, separate from source")
        if (
            args.output
            and args.apply_safe_fixes
            and args.output.resolve()
            in {
                args.apply_safe_fixes.resolve(),
                args.apply_safe_fixes.with_suffix(
                    args.apply_safe_fixes.suffix + ".diff"
                ).resolve(),
            }
        ):
            raise ValueError("Report and draft output paths must differ")
        report = validate(args.input, level=args.level, sources=registry)
        if args.ai_review:
            from app.core.config import get_settings
            from app.services.curriculum_validation.ai_review import review

            asyncio.run(
                review(
                    report,
                    json.loads(args.input.read_text()),
                    get_settings(),
                    budget=args.ai_budget_usd,
                    price_ceiling=args.ai_price_ceiling,
                    max_requests=args.ai_max_requests,
                    max_tokens=args.ai_max_tokens,
                    retries=args.ai_retries,
                    timeout=args.ai_timeout,
                )
            )
        if args.apply_safe_fixes:
            applied = apply_safe_fixes(
                args.input, args.apply_safe_fixes, args.expected_sha
            )
            print(json.dumps(applied), file=sys.stderr)
        if not args.suggest_fixes:
            report.proposed_fixes = []
        result = (
            report.model_dump_json(indent=2)
            if args.report == "json"
            else markdown(report)
        )
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(result + ("\n" if args.report == "json" else ""))
        else:
            print(result)
        return int(any(i.severity in {"critical", "high"} for i in report.issues))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Validation failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
