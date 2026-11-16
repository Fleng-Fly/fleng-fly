# Curriculum sources and licenses

Review date: 2026-11-11. This records a technical review of published source
information, not clearance of any particular third-party record for distribution.
No live educational dataset was downloaded or bundled during this implementation.
All automated external-source tests use synthetic records. Local evidence caches
must remain separate from the authored draft and from public release artifacts.

| Source | Purpose and official URL | License / attribution | Restrictions and next review |
| --- | --- | --- | --- |
| Council of Europe CEFR | [Framework](https://www.coe.int/en/web/common-european-framework-reference-languages), competencies and curriculum goals | No general reuse license is assumed for descriptors. This implementation stores links and original short observations only. | Reference only; review the specific publication's reproduction terms before quoting descriptors. No large extracts or official level certification. A0 is Fleng's internal introductory label. |
| Cambridge English | [Preparation](https://www.cambridgeenglish.org/exams-and-tests/qualifications/preparation/), methodological reference and qualification levels | No open license is assumed. Link attribution only; no Cambridge content imported. | No scraper, textbooks, exam extraction, copied vocabulary lists or English Vocabulary Profile database. Review any intended reuse separately. No affiliation or endorsement. |
| Tatoeba | [Downloads](https://tatoeba.org/en/downloads), exact/normalized English sentence attestation and directly linked Ukrainian translations | [Terms §6](https://tatoeba.org/en/terms_of_use): text defaults to CC BY 2.0 FR, with per-sentence licensing including CC0. Preserve each sentence ID, author, license, release and translation link. | Downloads page timed out during this audit; terms were available. Check each record, including translation authors and licenses; do not infer CC0 from its origin. Audio is excluded. No blanket correctness claim. Separate record-level license review is required before importing or redistributing evidence. |
| Wiktionary / Wiktextract | [Wiktionary copyrights](https://en.wiktionary.org/wiki/Wiktionary:Copyrights), [official Wikimedia dumps](https://dumps.wikimedia.org/enwiktionary/), [Wiktextract](https://github.com/tatuylonen/wiktextract), [Kaikki raw exports](https://kaikki.org/dictionary/rawdata.html); existence, POS, senses and candidate translations | Current Wiktionary original text is described as CC BY-SA 4.0 / GFDL; snapshot terms control. Adapter also supports explicitly reviewed historical CC BY-SA 3.0 snapshots. Preserve entry/history attribution, release identifier and file hash. Extractor software license is distinct from data license. | Source entries can contain separately licensed quotations/media. This adapter excludes quotations/media and extracts headwords, POS and translation sense labels only. Review snapshot terms, attribution and share-alike obligations before redistribution or adaptation. Never assume a headword match proves a translation. |

The source checks above establish what must be reviewed, not permission to
relicense a combined dataset. In particular, do not merge source-derived CC BY-SA
text into publicly distributed curriculum or reports without a separate review.
Generated audit reports include provenance rather than copied source definitions
or translated sentences. They still contain authored Fleng draft text and must
not be treated as a publication package.

## Evidence cache contract

The validator consumes one or more local UTF-8 JSONL files, one EvidenceRecord per
line. Run `--dataset wiktionary.jsonl --dataset tatoeba.jsonl` to use both without
building a public combined dataset. Each row requires:

- `source`: `wiktionary` or `tatoeba`.
- `record_id`, `url` on the corresponding official host, `revision`.
- `license`, `attribution`, `english`, `ukrainian` (list, possibly empty).
- Optional `pos` and `sense` for dictionary evidence.
- `translation_ids` for Tatoeba: exactly one ID per Ukrainian translation.
- `original_license` and `translation_licenses` preserve separate licenses when
  the adapter groups linked Tatoeba records. A CC BY record cannot be labeled CC0.

The registry validates metadata, accepted license labels and record shape. It
cannot authenticate an operator's license declaration or establish linguistic
truth. Unknown licenses, missing links, malformed records and unreadable files
make the cache `source_unavailable`, with no partial evidence accepted. Empty
caches are unavailable. A miss in a partial dictionary is `needs_review`, never
proof that a word does not exist.

## Preparing official local exports

No network is used by either command. Acquire exports through their official
channels and inspect the actual release terms first. Keep caches outside Git.
Examples use `/tmp`; choose persistent private storage for a real review.

```bash
backend/.venv/bin/python scripts/prepare_curriculum_sources.py \
  --wiktextract /path/to/reviewed-wiktextract.jsonl \
  --revision REVIEWED_DUMP_DATE --wiktionary-license 'CC BY-SA 4.0' \
  --attribution 'Wiktionary contributors; entry history links; reviewed snapshot' \
  --license-reviewed --output /tmp/fleng-wiktionary.jsonl
```

The Wiktextract adapter streams English headwords and groups Ukrainian
translations by their own sense labels. It never pairs a translation with an
arbitrary first sense. This is not a full morphology engine: inflection and
word-sense alignment remain review tasks. It supports the English-edition
Wiktextract JSONL schema, not arbitrary multilingual extraction formats.

Tatoeba uses the official detailed sentence format: tab-separated
`id, language, text, username, date_added, date_modified`, with no CSV quoting,
and the official two-column direct-links export. Decompress releases locally
first. Supply a JSON sidecar keyed by sentence ID, with reviewed `license` and
`attribution` values for both English and Ukrainian records. This sidecar must be
based on the release's metadata, not a guessed license for all sentences.

```bash
backend/.venv/bin/python scripts/prepare_curriculum_sources.py \
  --tatoeba-sentences /path/to/sentences_detailed.tsv \
  --tatoeba-links /path/to/links.tsv \
  --tatoeba-licenses /path/to/reviewed-sentence-licenses.json \
  --revision REVIEWED_RELEASE --license-reviewed \
  --output /tmp/fleng-tatoeba.jsonl
```

Only direct English–Ukrainian links are retained. Unlinked and transitively linked
sentences are excluded. Both adapters emit a companion `.manifest.json` with
SHA-256 hashes of their inputs and output metadata. Missing record licensing
aborts preparation. Review the cache before validation; preparation is not
publication or a declaration that source sentences are correct.
