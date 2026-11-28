"""Build a sourced JSONL shard using a reviewed sense and Tatoeba pair manifest."""

import argparse
import bz2
import csv
import gzip
import html
import re
import struct
import zipfile
from pathlib import Path

from app.db.import_vocabulary import SourcedWord

DICTIONARY_URL = "https://danielgregorini.github.io/koreader-dicts/en/en-uk/"
PARTS = {"n.": "noun", "adj.": "adjective", "v.": "verb", "adv.": "adverb"}


def dictionary_entries(archive: Path, words: set[str]) -> dict[str, str]:
    with zipfile.ZipFile(archive) as bundle:
        index = bundle.read("en-uk/en-uk.idx")
        content = gzip.decompress(bundle.read("en-uk/en-uk.dict.dz"))
    result = {}
    offset = 0
    while offset < len(index):
        end = index.index(0, offset)
        word = index[offset:end].decode("utf-8")
        start, length = struct.unpack_from(">II", index, end + 1)
        offset = end + 9
        if word in words:
            if word in result:
                raise ValueError(f"Ambiguous dictionary headword: {word}")
            result[word] = content[start : start + length].decode("utf-8")
    return result


def sentence_records(path: Path, wanted: set[str]) -> dict[str, tuple[str, str]]:
    with bz2.open(path, "rt", encoding="utf-8") as stream:
        return {
            row[0]: (row[2], row[3])
            for row in csv.reader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
            if row[0] in wanted and row[3] and row[3] != "\\N"
        }


def selected_sense(entry: str, sense: int) -> tuple[str, list[str], str]:
    ipa = re.search(r'<div style="color:#666666">(/[^<]+/)</div>', entry)
    blocks = re.findall(r"<div><i>([^<]+)</i>(.*?)</div>", entry)
    senses = [
        (pos, translation)
        for pos, block in blocks
        for translation in re.findall(r"<b>([^<]+)</b>", block)
    ]
    if not ipa or not 1 <= sense <= len(senses):
        raise ValueError("Missing IPA or requested sense")
    part, text = senses[sense - 1]
    translations = [value.strip().replace("\u0301", "") for value in html.unescape(text).split(",")]
    return PARTS[part], translations, html.unescape(ipa.group(1))


def build_release(
    manifest: Path, archive: Path, english: Path, ukrainian: Path, links: Path
) -> list[SourcedWord]:
    with manifest.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    dictionary = dictionary_entries(archive, {row["word"] for row in rows})
    en = sentence_records(english, {row["en_id"] for row in rows})
    uk = sentence_records(ukrainian, {row["uk_id"] for row in rows})
    wanted = {(row["en_id"], row["uk_id"]) for row in rows}
    with bz2.open(links, "rt", encoding="utf-8") as stream:
        found = {(left, right) for left, right in map(str.split, stream) if (left, right) in wanted}
    if found != wanted:
        raise ValueError(f"Unlinked Tatoeba sentence pairs: {sorted(wanted - found)}")

    result = []
    for row in rows:
        word = row["word"]
        pos, translations, ipa = selected_sense(dictionary[word], int(row["sense"]))
        sentence, author_en = en[row["en_id"]]
        translated, author_uk = uk[row["uk_id"]]
        if not re.search(rf"(?<!\w){re.escape(word)}(?!\w)", sentence, re.IGNORECASE):
            raise ValueError(f"Example does not contain the headword: {word}")
        result.append(
            SourcedWord.model_validate(
                {
                    "word": word,
                    "translation": translations[0],
                    "alternative_translations": translations[1:],
                    "pronunciation": ipa,
                    "part_of_speech": pos,
                    "level": row["level"],
                    "category": row["category"],
                    "example": sentence,
                    "example_translation": translated,
                    "course_slug": row["course_slug"],
                    "lesson_slug": row["lesson_slug"],
                    "source_url": DICTIONARY_URL,
                    "license_id": "CC-BY-SA-4.0",
                    "example_sources": [
                        {
                            "url": f"https://tatoeba.org/en/sentences/show/{sentence_id}",
                            "author": author,
                            "license_id": "CC-BY-2.0-FR",
                        }
                        for sentence_id, author in (
                            (row["en_id"], author_en),
                            (row["uk_id"], author_uk),
                        )
                    ],
                }
            )
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "archive", "english", "ukrainian", "links", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    entries = build_release(args.manifest, args.archive, args.english, args.ukrainian, args.links)
    args.output.write_text(
        "".join(entry.model_dump_json() + "\n" for entry in entries), encoding="utf-8"
    )
    print(f"{len(entries)} sourced words")


if __name__ == "__main__":
    main()
