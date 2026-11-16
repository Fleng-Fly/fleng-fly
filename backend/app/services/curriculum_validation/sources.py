"""Offline evidence adapters. No downloading, scraping or implicit network calls."""

import hashlib
import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source: Literal["wiktionary", "tatoeba"]
    record_id: str = Field(min_length=1)
    url: str = Field(pattern=r"^https://")
    license: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    english: str = Field(min_length=1)
    ukrainian: list[str] = Field(default_factory=list)
    pos: str | None = None
    sense: str | None = None
    # Required for linked Tatoeba translations (not inferred from co-occurrence).
    translation_ids: list[str] = Field(default_factory=list)
    original_license: str | None = None
    translation_licenses: list[str] = Field(default_factory=list)


class SourceRegistry:
    """Reviewed local JSONL evidence, kept separate from distributable content.

    Rows are a documented projection of Wiktextract or linked Tatoeba exports.
    Missing dictionary entries are NOT proof that a word does not exist.
    """

    def __init__(self, path: Path | list[Path] | None = None):
        self.records: list[EvidenceRecord] = []
        self.status = "source_unavailable"
        self.error: str | None = None
        self.sha256: str | None = None
        self.files: list[dict] = []
        if not path:
            return
        try:
            paths = [path] if isinstance(path, Path) else path
            records: list[EvidenceRecord] = []
            for dataset in paths:
                data = dataset.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                self.files.append(dict(name=dataset.name, sha256=digest))
                records.extend(
                    EvidenceRecord.model_validate_json(s) for s in data.splitlines() if s
                )
            self.sha256 = (
                self.files[0]["sha256"]
                if len(self.files) == 1
                else hashlib.sha256(json.dumps(self.files, sort_keys=True).encode()).hexdigest()
            )
            if not records:
                raise ValueError("Empty dataset")
            for r in records:
                allowed = (
                    {"CC BY 2.0 FR", "CC0 1.0"}
                    if r.source == "tatoeba"
                    else {"CC BY-SA 4.0", "CC BY-SA 3.0"}
                )
                expected_host = "tatoeba.org" if r.source == "tatoeba" else "en.wiktionary.org"
                if urlparse(r.url).hostname != expected_host:
                    raise ValueError("Unexpected provenance host")
                if r.original_license is not None and r.original_license not in allowed:
                    raise ValueError("Original license requires review")
                if any(license_name not in allowed for license_name in r.translation_licenses):
                    raise ValueError("Translation license requires review")
                if r.translation_licenses and len(r.translation_licenses) != len(r.translation_ids):
                    raise ValueError("Translation license provenance mismatch")
                if any(not t.strip() for t in r.ukrainian):
                    raise ValueError("Empty translation in evidence")
                if r.license == "CC0 1.0" and "CC BY 2.0 FR" in [
                    r.original_license,
                    *r.translation_licenses,
                ]:
                    raise ValueError("Cannot relicense attributed records as CC0")
                if r.license not in allowed:
                    raise ValueError("License requires separate review")
                if r.source == "tatoeba" and len(r.ukrainian) != len(r.translation_ids):
                    raise ValueError("Translation provenance missing")
            self.records = records  # Atomic: malformed datasets provide no evidence.
            self.status = "available"
        except (OSError, ValueError) as exc:
            self.error = type(exc).__name__ + ": invalid or unreadable evidence dataset"

    def metadata(self) -> dict:
        return dict(
            status=self.status,
            sha256=self.sha256,
            files=self.files,
            records=len(self.records),
            error=self.error,
            reference_sources={
                "cefr": {
                    "type": "official_framework",
                    "status": "reference_only",
                    "url": "https://www.coe.int/en/web/common-european-framework-reference-languages",
                },
                "cambridge": {
                    "type": "official_framework",
                    "status": "reference_only",
                    "url": "https://www.cambridgeenglish.org/exams-and-tests/qualifications/preparation/",
                },
            },
        )

    def matches(self, text: str, source: str) -> list[EvidenceRecord]:
        from .validator import canonical

        return [
            r
            for r in self.records
            if r.source == source and canonical(r.english) == canonical(text)
        ]

    def provenance(self, record: EvidenceRecord) -> dict:
        return json.loads(record.model_dump_json(exclude={"english", "ukrainian"}))
