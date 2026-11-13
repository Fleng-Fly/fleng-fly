"""Offline audit regressions. All external evidence is synthetic fixture data."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import Settings
from app.db.curriculum import CONTENT, load_curriculum
from app.modules.ai.provider import Completion
from app.services.curriculum_validation.ai_review import review
from app.services.curriculum_validation.fixes import apply_safe_fixes
from app.services.curriculum_validation.reports import markdown
from app.services.curriculum_validation.sources import SourceRegistry
from app.services.curriculum_validation.validator import Report, validate

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def draft(tmp_path):
    path = tmp_path / "draft.json"
    path.write_bytes(CONTENT.read_bytes())
    return path


def mutate(path, callback):
    data = json.loads(path.read_bytes())
    callback(data["courses"][0]["lessons"][0])
    path.write_text(json.dumps(data, ensure_ascii=False))


def evidence(tmp_path, **changes):
    record = dict(
        source="wiktionary",
        record_id="synthetic-read-1",
        url="https://en.wiktionary.org/wiki/read",
        license="CC BY-SA 4.0",
        attribution="Synthetic fixture, not imported dictionary data",
        revision="fixture-v1",
        english="read",
        ukrainian=["читати"],
        pos="verb",
        sense="interpret writing",
    )
    record.update(changes)
    path = tmp_path / "evidence.jsonl"
    path.write_text(json.dumps(record, ensure_ascii=False) + "\n")
    return SourceRegistry(path)


def test_all_inventory_and_read_only(draft):
    before = draft.read_bytes()
    result = validate(draft)
    assert result.structural_validation == dict(
        courses=5,
        lessons=50,
        lessons_structurally_valid=50,
        words=500,
        words_structurally_valid=500,
        words_without_examples=500,
        exercises=400,
        exercises_structurally_valid=400,
        importer_contract_valid=True,
    )
    assert len(result.vocabulary) == 500
    assert len(result.sentences) == 150
    assert result.linguistic_validation["externally_verified"] == 0
    assert result.ai_review["status"] == "not_run"
    assert not any(i.severity in {"critical", "high"} for i in result.issues)
    assert draft.read_bytes() == before
    assert len(load_curriculum(draft).courses) == 5
    assert validate(draft).model_dump() == result.model_dump()


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "B1", "B2"])
def test_level_filter(draft, level):
    result = validate(draft, level=level)
    assert result.structural_validation["words"] == 100
    assert result.structural_validation["exercises"] == 80
    assert result.courses[0]["level"] == level


@pytest.mark.parametrize("field", ["prompt", "correct_option_id"])
def test_empty_question_or_answer(draft, field):
    mutate(draft, lambda lesson: lesson["exercises"][0].update({field: ""}))
    result = validate(draft)
    assert not result.structural_validation["importer_contract_valid"]
    assert any(i.severity == "high" for i in result.issues)


def test_unicode_equivalent_options(draft):
    def change(lesson):
        lesson["exercises"][0]["options"][0]["text"] = "café"
        lesson["exercises"][0]["options"][1]["text"] = " CAFE\u0301 "

    mutate(draft, change)
    result = validate(draft)
    assert any(i.category == "ambiguous_options" for i in result.issues)


def test_modal_ambiguity(draft):
    def change(lesson):
        lesson["exercises"][0].update(
            prompt="I ___ go home.",
            options=[
                {"id": "1", "text": "can"},
                {"id": "2", "text": "might"},
                {"id": "3", "text": "should"},
            ],
        )

    mutate(draft, change)
    result = validate(draft)
    assert any(
        i.category == "possible_multiple_answers" and i.confidence == "low" for i in result.issues
    )


def test_duplicate_words(draft):
    mutate(draft, lambda lesson: lesson["vocabulary"][1].update(word="READ"))
    assert any(i.category == "duplicate_word" for i in validate(draft).issues)


def test_nonexistent_word_not_proven_by_missing_entry(draft, tmp_path):
    mutate(draft, lambda lesson: lesson["vocabulary"][0].update(word="zzqnonword"))
    result = validate(draft, sources=evidence(tmp_path))
    assert result.vocabulary[0]["status"] == "needs_review"
    assert not result.vocabulary[0]["evidence"]


def test_translation_mismatch_is_review_not_proof(draft, tmp_path):
    mutate(draft, lambda lesson: lesson["vocabulary"][0].update(translation="банан"))
    result = validate(draft, sources=evidence(tmp_path))
    assert result.vocabulary[0]["status"] == "needs_review"
    assert any(
        i.category == "translation_mismatch" and i.source["type"] == "licensed_dataset"
        for i in result.issues
    )


def test_attestation_not_verification(draft, tmp_path):
    result = validate(draft, sources=evidence(tmp_path))
    assert result.vocabulary[0]["status"] == "probable"
    assert result.linguistic_validation["dictionary_attested"] == 1
    assert result.linguistic_validation["externally_verified"] == 0
    assert result.vocabulary[0]["evidence"][0]["revision"] == "fixture-v1"


def test_tatoeba_linked_sentence(draft, tmp_path):
    registry = evidence(
        tmp_path,
        source="tatoeba",
        license="CC0 1.0",
        url="https://tatoeba.org/en/sentences/show/123",
        record_id="123",
        english="Look at the text. Read it.",
        ukrainian=["Подивись на текст. Прочитай його."],
        translation_ids=["456"],
    )
    result = validate(draft, sources=registry)
    assert result.sentences[0]["status"] == "probable"
    assert result.sentences[0]["evidence"][0]["translation_ids"] == ["456"]


@pytest.mark.parametrize("kind", ["missing", "corrupt", "empty", "license", "missing_link"])
def test_unavailable_and_corrupt_sources(draft, tmp_path, kind):
    path = tmp_path / "bad.jsonl"
    if kind == "corrupt":
        path.write_text('{"english":')
    if kind == "empty":
        path.write_text("")
    registry = SourceRegistry(path)
    if kind == "license":
        registry = evidence(tmp_path, license="unreviewed")
    if kind == "missing_link":
        registry = evidence(tmp_path, source="tatoeba", license="CC0 1.0")
    assert registry.status == "source_unavailable"
    assert registry.records == []
    result = validate(draft, sources=registry)
    assert result.vocabulary[0]["status"] == "source_unavailable"
    assert any(i.category == "source_unavailable" for i in result.issues)


def test_safe_copy_and_sha(draft, tmp_path):
    mutate(draft, lambda lesson: lesson["vocabulary"][0].update(word=" read "))
    raw = draft.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    result = validate(draft)
    assert len(result.proposed_fixes) == 1
    output = tmp_path / "new-draft.json"
    with pytest.raises(ValueError, match="SHA"):
        apply_safe_fixes(draft, output, "wrong")
    assert not output.exists()
    result = apply_safe_fixes(draft, output, sha)
    assert result["applied"] == 1
    assert draft.read_bytes() == raw
    assert output.with_suffix(".json.diff").exists()
    assert load_curriculum(output).courses[0].lessons[0].vocabulary[0].word == "read"
    with pytest.raises(ValueError, match="overwrite"):
        apply_safe_fixes(draft, output, sha)
    with pytest.raises(ValueError, match="separate"):
        apply_safe_fixes(draft, draft, sha)


def test_reports_roundtrip(draft):
    result = validate(draft)
    assert Report.model_validate_json(result.model_dump_json()) == result
    text = markdown(result)
    assert "Structural validation" in text and "Linguistic validation" in text
    assert result.raw_sha256 in text
    assert "source_unavailable" in text


def test_cli_dry_run_and_output_protection(draft, tmp_path):
    raw = draft.read_bytes()
    command = [
        sys.executable,
        str(ROOT / "scripts/validate_curriculum.py"),
        "--input",
        str(draft),
        "--level",
        "A0",
    ]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["structural_validation"]["words"] == 100
    run = subprocess.run(command + ["--output", str(draft)], capture_output=True, text=True)
    assert run.returncode == 2
    assert draft.read_bytes() == raw
    mutate(draft, lambda lesson: lesson["exercises"][0].update(prompt=""))
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 1


class MockProvider:
    def __init__(self, content='{"findings": []}', fail=False):
        self.calls = 0
        self.content = content
        self.fail = fail

    async def complete(self, messages, schema=None):
        self.calls += 1
        assert "SECRET_SENTINEL" not in json.dumps(messages)
        if self.fail:
            raise TimeoutError()
        return Completion(
            self.content, "fixture", dict(cost=0.001, prompt_tokens=100, completion_tokens=20)
        )

    async def stream(self, messages):
        yield Completion("", "fixture")


async def test_ai_limits_usage_and_no_autofix(draft):
    data = json.loads(draft.read_bytes())
    result = validate(draft)
    provider = MockProvider(
        '{"findings":[{"evidence":"Potential issue","suggested_fix":"Review manually"}]}'
    )
    settings = Settings(openrouter_api_key="SECRET_SENTINEL")
    await review(
        result,
        data,
        settings,
        budget=1,
        price_ceiling=0.000001,
        max_requests=2,
        max_tokens=100,
        provider=provider,
    )
    assert provider.calls == 2
    assert result.ai_review["reported_cost_usd"] == 0.002
    assert result.ai_review["status"] == "limit_reached"
    assert all(i.source["type"] == "ai_assisted" for i in result.issues[-2:])
    assert result.proposed_fixes == []
    assert result.courses[0]["issues"] == sum(
        i.course_id == result.courses[0]["course_id"] for i in result.issues
    )


async def test_ai_budget_exhausted_before_call(draft):
    provider = MockProvider()
    result = validate(draft)
    await review(
        result,
        json.loads(draft.read_bytes()),
        Settings(),
        budget=0.00001,
        price_ceiling=0.001,
        provider=provider,
    )
    assert provider.calls == 0
    assert result.ai_review["status"] == "limit_reached"


async def test_ai_retry_bounded_and_bad_json(draft):
    for provider in (MockProvider(fail=True), MockProvider("invalid JSON")):
        result = validate(draft)
        await review(
            result,
            json.loads(draft.read_bytes()),
            Settings(),
            budget=1,
            price_ceiling=0.000001,
            max_requests=2,
            retries=1,
            provider=provider,
        )
        assert provider.calls == 2
        assert not result.ai_review["usage_complete"]
        assert result.ai_review["reserved_usd"] > 0


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(budget=0),
        dict(max_requests=100),
        dict(retries=5),
        dict(max_tokens=10000),
        dict(timeout=100),
    ],
)
async def test_invalid_ai_limits(draft, kwargs):
    options = dict(budget=1, price_ceiling=0.000001)
    options.update(kwargs)
    with pytest.raises(ValueError, match="limits"):
        await review(validate(draft), json.loads(draft.read_bytes()), Settings(), **options)


async def test_disabled_ai_not_run(draft):
    result = validate(draft)
    await review(
        result,
        json.loads(draft.read_bytes()),
        Settings(ai_enabled=False),
        budget=1,
        price_ceiling=0.000001,
    )
    assert result.ai_review["status"] == "not_run"
    assert result.ai_review["requests"] == 0


def test_wiktextract_projection_preserves_senses(tmp_path):
    from app.services.curriculum_validation.datasets import wiktextract_records

    path = tmp_path / "wiktextract.jsonl"
    entry = dict(
        word="book",
        lang_code="en",
        pos="noun",
        translations=[
            dict(code="uk", word="книга", sense="written work"),
            dict(code="uk", word="книжка", sense="bound pages"),
            dict(code="de", word="Buch", sense="written work"),
        ],
    )
    path.write_text(json.dumps(entry))
    rows = list(
        wiktextract_records(
            path,
            {"book"},
            revision="fixture",
            license_name="CC BY-SA 4.0",
            attribution="Synthetic fixture",
        )
    )
    assert len(rows) == 2
    assert rows[0].ukrainian == ["книга"]
    assert rows[0].pos == "noun"
    assert rows[0].sense == "written work"
    assert rows[0].record_id != rows[1].record_id
    assert (
        list(
            wiktextract_records(
                path,
                {"absent"},
                revision="fixture",
                license_name="CC BY-SA 4.0",
                attribution="Synthetic fixture",
            )
        )
        == []
    )


def test_tatoeba_projection_direct_links_and_individual_licenses(tmp_path):
    from app.services.curriculum_validation.datasets import tatoeba_records

    sentences = tmp_path / "sentences.tsv"
    links = tmp_path / "links.tsv"
    licenses = tmp_path / "licenses.json"
    sentences.write_text(
        "1\teng\tRead it.\tAlice\t2020\t2020\n"
        "2\tukr\tПрочитай це.\tBob\t2020\t2020\n"
        "3\tukr\tНе пов'язано.\tCharlie\t2020\t2020\n"
    )
    links.write_text("1\t2\n2\t1\n")
    licenses.write_text(
        json.dumps(
            {
                "1": dict(license="CC0 1.0", attribution="Alice"),
                "2": dict(license="CC BY 2.0 FR", attribution="Bob"),
            }
        )
    )
    rows = list(tatoeba_records(sentences, links, licenses, {"read it."}, revision="fixture"))
    assert len(rows) == 1
    assert rows[0].translation_ids == ["2"]
    assert rows[0].ukrainian == ["Прочитай це."]
    assert rows[0].original_license == "CC0 1.0"
    assert rows[0].translation_licenses == ["CC BY 2.0 FR"]
    assert "Bob" in rows[0].attribution
    licenses.write_text("{}")
    with pytest.raises(ValueError, match="license"):
        list(tatoeba_records(sentences, links, licenses, {"read it."}, revision="fixture"))


def test_source_preparation_cli_license_gate_and_corrupt_export(tmp_path):
    command = [sys.executable, str(ROOT / "scripts/prepare_curriculum_sources.py")]
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 2
    raw = tmp_path / "raw.jsonl"
    raw.write_text("not json")
    output = tmp_path / "cache.jsonl"
    result = subprocess.run(
        command
        + [
            "--license-reviewed",
            "--revision",
            "fixture",
            "--wiktextract",
            str(raw),
            "--wiktionary-license",
            "CC BY-SA 4.0",
            "--attribution",
            "Synthetic fixture",
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert not output.exists()


def test_grammar_and_cefr_are_advisory(draft):
    mutate(
        draft,
        lambda lesson: lesson.update(
            theory=lesson["theory"] + " She are a teacher.", grammar="Third conditional"
        ),
    )
    result = validate(draft)
    for category in ("grammar_pattern", "cefr_construction"):
        finding = next(i for i in result.issues if i.category == category)
        assert finding.source["type"] == "heuristic"
        assert finding.review_status == "needs_review"


def test_missing_translation_is_invalid(draft):
    mutate(draft, lambda lesson: lesson["vocabulary"][0].update(translation=""))
    result = validate(draft)
    assert result.vocabulary[0]["status"] == "invalid"
    assert any(i.category == "translation_script" for i in result.issues)


def test_safe_fixes_refuse_blocking_defects(draft, tmp_path):
    mutate(draft, lambda lesson: lesson["exercises"][0].update(correct_option_id="unknown"))
    sha = hashlib.sha256(draft.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Blocking"):
        apply_safe_fixes(draft, tmp_path / "fixed.json", sha)


def test_ai_timeout_bound(draft):
    import asyncio

    class SlowProvider(MockProvider):
        async def complete(self, messages, schema=None):
            self.calls += 1
            await asyncio.sleep(1)
            return Completion('{"findings": []}', "fixture")

    provider = SlowProvider()
    result = validate(draft)
    asyncio.run(
        review(
            result,
            json.loads(draft.read_bytes()),
            Settings(),
            budget=1,
            price_ceiling=0.000001,
            max_requests=1,
            timeout=0.001,
            provider=provider,
        )
    )
    assert provider.calls == 1
    assert result.ai_review["usage_complete"] is False
