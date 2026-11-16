"""Project local official exports into provenance records; never fetch data.

Wiktextract JSONL is streamed. Tatoeba uses sentences_detailed.tsv and direct
links.tsv; both sides require explicit per-sentence licensing metadata. Callers
must review licenses before calling these functions. No third-party text is
inserted into the curriculum, and no dataset is bundled with the application.
"""

import csv
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

from .sources import EvidenceRecord
from .validator import canonical


def wiktextract_records(
    path: Path, words: set[str], *, revision: str, license_name: str, attribution: str
) -> Iterator[EvidenceRecord]:
    if license_name not in {"CC BY-SA 4.0", "CC BY-SA 3.0"}:
        raise ValueError("Unreviewed Wiktionary license")
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            entry = json.loads(line)
            if entry.get("lang_code") != "en" or canonical(entry.get("word", "")) not in words:
                continue
            # Translation sense labels belong to the translations themselves, not an arbitrary
            # first dictionary sense. Keep senses separate so ambiguity remains visible.
            translations = entry.get("translations", [])
            grouped: dict[str, list[str]] = {}
            for translation in translations:
                if translation.get("code") == "uk" and translation.get("word"):
                    grouped.setdefault(translation.get("sense", ""), []).append(translation["word"])
            if not grouped:
                grouped[""] = []
            for index, (sense, ukrainian) in enumerate(grouped.items()):
                yield EvidenceRecord(
                    source="wiktionary",
                    record_id=f"{revision}:{line_no}:{index}",
                    revision=revision,
                    url="https://en.wiktionary.org/wiki/" + quote(entry["word"], safe=""),
                    license=license_name,
                    attribution=attribution,
                    english=entry["word"],
                    ukrainian=ukrainian,
                    pos=entry.get("pos"),
                    sense=sense or None,
                )


def tatoeba_records(
    sentences: Path, links: Path, licenses: Path, examples: set[str], *, revision: str
) -> Iterator[EvidenceRecord]:
    # License sidecar, manually checked against the official release, keyed by sentence ID.
    # Each entry: {license, attribution}. Do not assume every sentence is CC0/default licensed.
    licensing = json.loads(licenses.read_bytes())
    english: dict[str, str] = {}
    with sentences.open(encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(row) != 6:
                raise ValueError("Expected Tatoeba sentences_detailed six-column TSV")
            if row[1] == "eng" and canonical(row[2]) in examples:
                english[row[0]] = row[2]
    pairs: dict[str, set[str]] = {sid: set() for sid in english}
    with links.open(encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(row) != 2:
                raise ValueError("Expected two-column Tatoeba links TSV")
            if row[0] in english:
                pairs[row[0]].add(row[1])
            if row[1] in english:
                pairs[row[1]].add(row[0])
    wanted = {sid for targets in pairs.values() for sid in targets}
    ukrainian: dict[str, str] = {}
    with sentences.open(encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
            if row[0] in wanted and row[1] == "ukr":
                ukrainian[row[0]] = row[2]
    for sid, text in english.items():
        if sid not in licensing:
            raise ValueError(f"Missing reviewed sentence license: {sid}")
        base = licensing[sid]
        grouped: dict[str, list[str]] = {}
        for tid in sorted(pairs[sid] & ukrainian.keys()):
            if tid not in licensing:
                raise ValueError(f"Missing reviewed translation license: {tid}")
            # Separate mixed licenses; never relicense a CC BY translation as CC0.
            group = (
                "CC BY 2.0 FR"
                if "CC BY 2.0 FR" in {base["license"], licensing[tid]["license"]}
                else base["license"]
            )
            if licensing[tid]["license"] not in {"CC BY 2.0 FR", "CC0 1.0"}:
                raise ValueError("Unreviewed translation license")
            grouped.setdefault(group, []).append(tid)
        if not grouped:
            grouped[base["license"]] = []
        for license_name, targets in grouped.items():
            if base["license"] not in {"CC BY 2.0 FR", "CC0 1.0"}:
                raise ValueError("Unreviewed sentence license")
            attribution = (
                base["attribution"]
                + "; "
                + "; ".join(
                    f"{tid}: {licensing[tid]['attribution']} ({licensing[tid]['license']})"
                    for tid in targets
                )
            )
            yield EvidenceRecord(
                source="tatoeba",
                record_id=sid,
                url=f"https://tatoeba.org/en/sentences/show/{sid}",
                revision=revision,
                license=license_name,
                attribution=attribution,
                english=text,
                ukrainian=[ukrainian[tid] for tid in targets],
                translation_ids=targets,
                original_license=base["license"],
                translation_licenses=[licensing[tid]["license"] for tid in targets],
            )


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()
