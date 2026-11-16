"""Reproducible draft audit; never opens a database or modifies grading/XP."""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.db.curriculum import Curriculum, ExerciseSpec, LessonSpec, WordSpec, content_sha
from app.db.models import Exercise
from app.modules.exercises.grading import grade_objective

from .sources import SourceRegistry


def canonical(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


class Issue(BaseModel):
    issue_id: str
    course_id: str | None
    lesson_id: str | None
    item_id: str | None
    category: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    confidence: Literal["high", "medium", "low"]
    source: dict
    evidence: str
    suggested_fix: str
    review_status: Literal["needs_review", "confirmed"] = "needs_review"


class Report(BaseModel):
    schema_version: int = 1
    raw_sha256: str
    publication_sha256: str | None = None
    structural_validation: dict = Field(default_factory=dict)
    linguistic_validation: dict = Field(default_factory=dict)
    sources: dict = Field(default_factory=dict)
    ai_review: dict = Field(default_factory=lambda: {"status": "not_run", "requests": 0})
    courses: list[dict] = Field(default_factory=list)
    vocabulary: list[dict] = Field(default_factory=list)
    sentences: list[dict] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    proposed_fixes: list[dict] = Field(default_factory=list)
    severity_counts: dict = Field(default_factory=dict)


def validate(
    path: Path, *, level: str | None = None, sources: SourceRegistry | None = None
) -> Report:
    registry = sources or SourceRegistry()
    raw = path.read_bytes()
    data = json.loads(raw)
    report = Report(raw_sha256=hashlib.sha256(raw).hexdigest(), sources=registry.metadata())

    def issue(
        course,
        lesson,
        item,
        category,
        evidence,
        *,
        severity="medium",
        source_type="deterministic",
        confidence="high",
        fix="Review in context.",
        records=None,
    ):
        identity = json.dumps([course, lesson, item, category, evidence], ensure_ascii=False)
        report.issues.append(
            Issue(
                issue_id=hashlib.sha256(identity.encode()).hexdigest()[:20],
                course_id=course,
                lesson_id=lesson,
                item_id=item,
                category=category,
                severity=severity,
                confidence=confidence,
                source={
                    "type": source_type,
                    "name": category,
                    **({"records": records} if records else {}),
                },
                evidence=evidence,
                suggested_fix=fix,
                review_status="confirmed" if source_type == "deterministic" else "needs_review",
            )
        )

    # Reuse the importer contract, but continue raw inspection after failures.
    try:
        content = Curriculum.model_validate(data)
        report.publication_sha256 = content_sha(content)
        contract_valid = True
    except ValidationError as exc:
        contract_valid = False
        for error in exc.errors(include_input=False, include_url=False):
            loc = list(error["loc"])
            ci = loc[1] if len(loc) > 1 and loc[0] == "courses" else None
            course = data["courses"][ci]["slug"] if isinstance(ci, int) else None
            lesson = None
            if "lessons" in loc:
                li = loc[loc.index("lessons") + 1]
                if isinstance(ci, int) and isinstance(li, int):
                    lesson = data["courses"][ci]["lessons"][li]["slug"]
            issue(
                course,
                lesson,
                "/".join(map(str, loc)),
                "import_contract",
                error["msg"],
                severity="high",
            )

    if registry.status != "available":
        issue(
            None,
            None,
            None,
            "source_unavailable",
            "No usable local licensed evidence dataset. " + (registry.error or "Not configured."),
            severity="info",
            fix="Supply reviewed local dataset with record provenance.",
        )
    counts: Counter = Counter(
        {
            key: 0
            for key in (
                "courses",
                "lessons",
                "lessons_structurally_valid",
                "words",
                "words_structurally_valid",
                "words_without_examples",
                "exercises",
                "exercises_structurally_valid",
            )
        }
    )
    seen_words: dict[str, str] = {}
    for course in data.get("courses", []):
        if level and course["level"] != level:
            continue
        cid = course["slug"]
        before = len(report.issues)
        course_counts_before = counts.copy()
        counts["courses"] += 1
        for lesson in course["lessons"]:
            lid = lesson["slug"]
            counts["lessons"] += 1
            try:
                LessonSpec.model_validate(lesson)
                counts["lessons_structurally_valid"] += 1
            except ValidationError:
                pass
            for fragment in (lesson["theory"], *lesson["examples"]):
                for pattern in (
                    r"\b(?:he|she|it) (?:are|am)\b",
                    r"\b(?:we|they) is\b",
                    r"\bdoesn.t (?:goes|works|likes)\b",
                ):
                    match = re.search(pattern, fragment, re.IGNORECASE)
                    if match:
                        issue(
                            cid,
                            lid,
                            lid,
                            "grammar_pattern",
                            f"Suspicious agreement in teaching text: {match.group()!r}; "
                            "may be an explicitly demonstrated error.",
                            source_type="heuristic",
                            confidence="medium",
                        )
            if course["level"] in {"A0", "A1"} and any(
                term in canonical(lesson["grammar"])
                for term in ("third conditional", "past perfect", "inversion", "mixed conditional")
            ):
                issue(
                    cid,
                    lid,
                    lid,
                    "cefr_construction",
                    "Advanced grammar label in introductory course; local sequencing advisory.",
                    source_type="heuristic",
                    confidence="medium",
                )
            issue(
                cid,
                lid,
                lid,
                "grammar_review",
                "Explanation/example consistency and goal alignment require teacher review: "
                + lesson["grammar"],
                source_type="heuristic",
                confidence="low",
                severity="info",
            )
            # Length is an advisory signal, never a CEFR classification.
            limit = {"A0": 10, "A1": 14, "A2": 20, "B1": 28, "B2": 36}[course["level"]]
            longest = max(
                (len(s.split()) for s in re.split(r"[.!?]", lesson["reading"])), default=0
            )
            if longest > limit:
                issue(
                    cid,
                    lid,
                    lid,
                    "cefr_length",
                    f"Longest reading sentence: {longest} "
                    f"words; local advisory threshold {limit} for {course['level']}.",
                    source_type="heuristic",
                    confidence="low",
                )
            issue(
                cid,
                lid,
                lid,
                "competency_coverage",
                "Multiple choice cannot demonstrate independent speaking/writing; "
                "verify goals, prerequisites and productive skills with a teacher. "
                + (
                    "A0 uses Fleng introductory specification, not official CEFR."
                    if course["level"] == "A0"
                    else "Framework: https://www.coe.int/en/web/common-european-framework-reference-languages"
                ),
                source_type="heuristic",
                confidence="medium",
                severity="info",
            )
            for si, sentence in enumerate(lesson["examples"]):
                matches = registry.matches(sentence, "tatoeba")
                report.sentences.append(
                    dict(
                        course_id=cid,
                        lesson_id=lid,
                        index=si,
                        status="probable"
                        if matches
                        else "source_unavailable"
                        if registry.status != "available"
                        else "needs_review",
                        evidence=[registry.provenance(r) for r in matches],
                    )
                )
            local_words: set[str] = set()
            for wi, word in enumerate(lesson["vocabulary"]):
                counts["words"] += 1
                wid = f"{lid}/vocabulary/{wi}"
                word_valid = True
                try:
                    WordSpec.model_validate(word)
                except ValidationError:
                    word_valid = False
                key = canonical(word["word"])
                status = "needs_review" if registry.status == "available" else "source_unavailable"
                if key in local_words:
                    word_valid = False
                    issue(cid, lid, wid, "duplicate_word", f"Repeated word: {key}", severity="high")
                local_words.add(key)
                if key in seen_words:
                    issue(
                        cid,
                        lid,
                        wid,
                        "cross_lesson_word",
                        f"{key} also in {seen_words[key]}; may be intentional spiral practice.",
                        source_type="heuristic",
                        confidence="low",
                        severity="info",
                    )
                seen_words[key] = lid
                if not word["word"] or not all(
                    ch.isalpha() and "LATIN" in unicodedata.name(ch, "") or ch in " '-’"
                    for ch in word["word"]
                ):
                    issue(cid, lid, wid, "spelling", "Unexpected characters in English headword.")
                if not re.search(r"[а-яіїєґА-ЯІЇЄҐ]", word["translation"]):
                    status = "invalid"
                    word_valid = False
                    issue(
                        cid,
                        lid,
                        wid,
                        "translation_script",
                        "Missing Ukrainian translation.",
                        severity="high",
                    )
                matches = registry.matches(word["word"], "wiktionary")
                if matches:
                    status = "probable" if status != "invalid" else status
                    translations = {canonical(t) for r in matches for t in r.ukrainian}
                    if translations and canonical(word["translation"]) not in translations:
                        issue(
                            cid,
                            lid,
                            wid,
                            "translation_mismatch",
                            "Draft translation not among recorded source senses; synonyms and "
                            "context must be reviewed. Records: "
                            + ", ".join(r.record_id for r in matches),
                            source_type="licensed_dataset",
                            records=[registry.provenance(r) for r in matches],
                            confidence="medium",
                        )
                        status = "needs_review" if status != "invalid" else status
                    if len({r.sense for r in matches}) > 1:
                        issue(
                            cid,
                            lid,
                            wid,
                            "translation_ambiguity",
                            "Multiple dictionary senses; draft has no POS or sense field.",
                            source_type="licensed_dataset",
                            records=[registry.provenance(r) for r in matches],
                            confidence="medium",
                        )
                        status = "needs_review"
                if not word["example"]:
                    counts["words_without_examples"] += 1
                if word_valid:
                    counts["words_structurally_valid"] += 1
                report.vocabulary.append(
                    dict(
                        course_id=cid,
                        lesson_id=lid,
                        item_id=wid,
                        word=word["word"],
                        translation=word["translation"],
                        status=status,
                        evidence=[registry.provenance(r) for r in matches],
                    )
                )
            prompts: set[str] = set()
            for spec in lesson["exercises"]:
                counts["exercises"] += 1
                eid = spec["slug"]
                errors_before = len(report.issues)
                exercise_valid = True
                try:
                    ExerciseSpec.model_validate(spec)
                except ValidationError:
                    exercise_valid = False
                prompt = canonical(spec["prompt"])
                if not prompt:
                    issue(cid, lid, eid, "empty_prompt", "Question is empty.", severity="high")
                if prompt in prompts:
                    issue(cid, lid, eid, "duplicate_prompt", "Repeated normalized question.")
                prompts.add(prompt)
                options = spec.get("options", [])
                texts = [canonical(o["text"]) for o in options]
                ids = [o["id"] for o in options]
                if not texts or "" in texts or len(set(texts)) != len(texts):
                    issue(
                        cid,
                        lid,
                        eid,
                        "ambiguous_options",
                        "Empty or equivalent normalized options.",
                        severity="high",
                    )
                if len(set(ids)) != len(ids) or spec.get("correct_option_id") not in ids:
                    issue(cid, lid, eid, "answer_reference", "Invalid answer ID.", severity="high")
                exercise = Exercise(**{k: v for k, v in spec.items() if k != "phase"})
                if spec["type"] == "single_choice":
                    for answer in ids + ["", "__invalid_answer__"]:
                        expected = answer == spec.get("correct_option_id") and answer in ids
                        if grade_objective(exercise, answer) != expected:
                            issue(
                                cid,
                                lid,
                                eid,
                                "grader_contract",
                                "Unexpected grade for " + repr(answer),
                                severity="critical",
                            )
                else:
                    issue(
                        cid,
                        lid,
                        eid,
                        "unsupported_draft_type",
                        "Draft importer currently supports single_choice only.",
                        severity="high",
                    )
                if exercise_valid and errors_before == len(report.issues):
                    counts["exercises_structurally_valid"] += 1
                # Known broad ambiguity: unrestricted modal completion has multiple valid meanings.
                modal_options = {"can", "could", "may", "might", "must", "should", "will", "would"}
                if (
                    sum(t in modal_options for t in texts) > 1
                    and "___" in prompt
                    and not any(
                        cue in prompt
                        for cue in (
                            "obligation",
                            "possib",
                            "advice",
                            "certain",
                            "polite",
                            "formal",
                            "ability",
                            "deduction",
                            "probab",
                            "likely",
                            "backshift",
                            "use would",
                            "if i were",
                        )
                    )
                ):
                    issue(
                        cid,
                        lid,
                        eid,
                        "possible_multiple_answers",
                        f"Question: {spec['prompt']!r}; options: {texts!r}. "
                        "Several modal options; check whether context fixes the meaning.",
                        fix="Teacher: check conditional meaning and intended modality; "
                        "add an explicit instruction if alternatives remain valid.",
                        source_type="heuristic",
                        confidence="low",
                    )
        report.courses.append(
            dict(
                course_id=cid,
                level=course["level"],
                issues=len(report.issues) - before,
                structural_validation={
                    k: counts[k] - course_counts_before[k] for k in counts if k != "courses"
                },
                recommendation="human_review_required",
            )
        )

    # Only NFC/edge whitespace: no rewriting text, translations, keys or option IDs.
    def walk(value, pointer=()):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, (*pointer, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, (*pointer, index))
        elif isinstance(value, str) and pointer[-1] in {
            "word",
            "translation",
            "example",
            "prompt",
            "text",
            "theory",
            "reading",
        }:
            fixed = unicodedata.normalize("NFC", value).strip()
            if fixed != value:
                ci = pointer[1] if pointer[0] == "courses" else None
                course = data["courses"][ci] if isinstance(ci, int) else None
                if level and course and course["level"] != level:
                    return
                lesson = None
                if "lessons" in pointer and course:
                    lesson = course["lessons"][pointer[pointer.index("lessons") + 1]]
                issue(
                    course["slug"] if course else None,
                    lesson["slug"] if lesson else None,
                    "/".join(map(str, pointer)),
                    "unicode_whitespace",
                    f"NFC/edge whitespace differs: {value!r} -> {fixed!r}.",
                    severity="low",
                    fix="Apply deterministic normalization to a new draft snapshot.",
                )
                report.proposed_fixes.append(
                    dict(
                        path=list(pointer), old=value, new=fixed, type="deterministic_normalization"
                    )
                )

    walk(data)
    for course_summary in report.courses:
        course_summary["issues"] = sum(
            i.course_id == course_summary["course_id"] for i in report.issues
        )
        course_words = [
            w for w in report.vocabulary if w["course_id"] == course_summary["course_id"]
        ]
        course_summary["linguistic_validation"] = dict(
            vocabulary_statuses=dict(Counter(w["status"] for w in course_words)),
            dictionary_attested=sum(bool(w["evidence"]) for w in course_words),
            externally_verified=0,
            human_review_words=len(course_words),
        )
    report.structural_validation = dict(counts, importer_contract_valid=contract_valid)
    report.linguistic_validation = dict(
        vocabulary_statuses=dict(Counter(v["status"] for v in report.vocabulary)),
        externally_verified=0,  # No sense-level human approval in this format.
        dictionary_attested=sum(bool(v["evidence"]) for v in report.vocabulary),
        human_review_words=len(report.vocabulary),
        human_review_lessons=counts["lessons"],
        structural_pass_words=counts["words_structurally_valid"],
        warning_items=len({i.item_id for i in report.issues if i.severity != "info"}),
        not_run=[
            "Exhaustive grammar/semantic equivalence",
            "Word-frequency CEFR model",
            "POS/sense matching (no fields in draft)",
            "AI review (opt-in)",
        ],
    )
    report.severity_counts = dict(Counter(i.severity for i in report.issues))
    return report
