"""Rebuild clean stopwords and an auditable duplicate report using only stdlib.

Run from any directory: python scripts/build_resources.py [--check]
"""

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kswv2 import _read_records, normalize_entry  # noqa: E402


SOURCES = {
    "core": "khmer stopwords-corpus-1.csv",
    "legacy": "khmer stopwords-corpus-385.csv",
    "expanded": "Khmer-Stop-Word-1000.csv",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    text = json.dumps(value, ensure_ascii=False, indent=2)
    # Keep Khmer readable while exposing invisible characters in raw variants.
    for codepoint in (0x200B, 0x200C, 0x200D, 0xFEFF):
        text = text.replace(chr(codepoint), "\\u" + f"{codepoint:04x}")
    return (text + "\n").encode("utf-8")


def word_bytes(words):
    return ("\n".join(sorted(words)) + "\n").encode("utf-8")


def build_stopwords():
    outputs = {}
    report = {
        "schema_version": 1,
        "record_numbers": "1-based CSV records, not physical lines; no headers",
        "normalization": (
            "NFC after trimming boundary whitespace (str.isspace), U+200B and "
            "U+FEFF; preserve internal text; no spelling or semantic changes"
        ),
        "ordering": "Unicode code point order, UTF-8, LF, one entry per line",
        "sources": [],
    }
    sets = {}
    provenance = defaultdict(list)
    for profile, filename in SOURCES.items():
        source = ROOT / filename
        records = _read_records(source)
        groups = defaultdict(list)
        changed = []
        empty = []
        internal_formatting = []
        for number, raw in records:
            key = normalize_entry(raw)
            if raw != key:
                changed.append({"record": number, "raw": raw, "clean": key})
            if not key:
                empty.append(number)
                continue
            groups[key].append({"record": number, "raw": raw})
            provenance[key].append({"source": filename, "record": number})
            if any(char.isspace() or unicodedata.category(char) == "Cf" for char in key):
                internal_formatting.append({"record": number, "value": key})
        values = [raw for _, raw in records if normalize_entry(raw)]
        exact_duplicates = len(values) - len(set(values))
        total_duplicates = len(values) - len(groups)
        duplicates = [
            {"entry": key, "occurrences": occurrences}
            for key, occurrences in sorted(groups.items())
            if len(occurrences) > 1
        ]
        output = f"data/stopwords/kswv2-{profile}.txt"
        outputs[output] = word_bytes(groups)
        sets[profile] = set(groups)
        report["sources"].append({
            "profile": profile,
            "path": filename,
            "sha256": sha256(source.read_bytes()),
            "csv_records": len(records),
            "nonempty_records": len(values),
            "raw_unique_entries": len(set(values)),
            "clean_unique_entries": len(groups),
            "exact_duplicate_excess_records": exact_duplicates,
            "additional_formatting_duplicate_excess_records": (
                total_duplicates - exact_duplicates
            ),
            "total_duplicate_excess_records": total_duplicates,
            "changed_records": changed,
            "empty_records": empty,
            "internal_formatting_for_review": internal_formatting,
            "duplicates": duplicates,
            "output": output,
            "output_sha256": sha256(outputs[output]),
        })
    union = set().union(*sets.values())
    output = "data/stopwords/kswv2-combined.txt"
    outputs[output] = word_bytes(union)
    report["combined"] = {
        "entries": len(union),
        "clean_memberships_across_sources": sum(map(len, sets.values())),
        "cross_source_excess_memberships": sum(map(len, sets.values())) - len(union),
        "output": output,
        "output_sha256": sha256(outputs[output]),
    }
    report["pairwise_overlap"] = [
        {"profiles": [a, b], "shared": len(sets[a] & sets[b]),
         "only_first": len(sets[a] - sets[b]), "only_second": len(sets[b] - sets[a])}
        for a, b in itertools.combinations(sets, 2)
    ]
    report["exact_duplicates_note"] = (
        "Counts are excess records, not distinct duplicate groups. The additional "
        "formatting count excludes exact duplicates already counted."
    )
    outputs["reports/stopword-audit.json"] = json_bytes(report)
    outputs["reports/stopword-provenance.json"] = json_bytes(dict(sorted(provenance.items())))
    return outputs, report


def verify_vocabulary(root=ROOT):
    """Check the pinned, separately licensed vocabulary without rewriting it."""
    base = Path(root) / "data" / "vocabulary"
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    data = (base / manifest["output_file"]).read_bytes()
    words = data.decode("utf-8").splitlines()
    if len(words) != manifest["entries"] or data != word_bytes(set(words)):
        raise ValueError("Vocabulary count, uniqueness, ordering or line endings differ")
    if sha256(data) != manifest["output_sha256"]:
        raise ValueError("Vocabulary SHA-256 differs from its provenance manifest")
    if any(not word or any(
        not ("\u1780" <= char <= "\u17ff") or unicodedata.category(char)[0] not in "LM"
        for char in word
    ) for word in words):
        raise ValueError("Vocabulary contains a non-Khmer-letter/mark entry")
    for filename, expected_hash in manifest["notice_sha256"].items():
        if sha256((base / filename).read_bytes()) != expected_hash:
            raise ValueError(f"Vocabulary license/notice changed: {filename}")
    return len(words)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without changing files")
    args = parser.parse_args(argv)
    try:
        vocabulary_count = verify_vocabulary()
        outputs, report = build_stopwords()
        mismatches = []
        for relative, data in outputs.items():
            path = ROOT / relative
            if args.check:
                if not path.exists() or path.read_bytes() != data:
                    mismatches.append(relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        if mismatches:
            print("Resources are stale: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        for source in report["sources"]:
            print(f'{source["profile"]}: {source["csv_records"]} records -> '
                  f'{source["clean_unique_entries"]} unique; '
                  f'{source["total_duplicate_excess_records"]} duplicate excess records')
        print(f'combined: {report["combined"]["entries"]} stopwords')
        print(f"separate vocabulary: {vocabulary_count} entries verified")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
