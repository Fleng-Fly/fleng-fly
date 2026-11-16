"""Private packaged item bank; never mounted as static content."""

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
BANK_PATH = Path(__file__).resolve().parents[2] / "db/content/placement-v1.json"


@lru_cache
def load_bank() -> dict:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    questions = bank["questions"]
    assert bank["version"] == "placement-1"
    assert bank["review_status"] == "internal_checks_only"
    assert len({q["id"] for q in questions}) == len(questions)
    assert Counter(q["level"] for q in questions) == Counter(dict.fromkeys(LEVELS, 6))
    for q in questions:
        assert q["skill"] in {"grammar", "vocabulary", "reading"}
        assert q["prompt"].strip() and q["explanation"].strip()
        assert len(q["options"]) == 4
        assert len({o["id"] for o in q["options"]}) == 4
        assert len({o["text"].strip().casefold() for o in q["options"]}) == 4
        assert q["correct_option_id"] in {o["id"] for o in q["options"]}
    return bank
