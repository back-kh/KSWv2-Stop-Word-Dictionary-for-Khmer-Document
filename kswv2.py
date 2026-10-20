"""Dependency-free loaders and whole-token filtering for the KSWv2 checkout."""

import csv
from pathlib import Path
import unicodedata


DATA_DIR = Path(__file__).resolve().parent / "data"
PROFILES = {
    "core": "kswv2-core.txt",
    "legacy": "kswv2-legacy.txt",
    "expanded": "kswv2-expanded.txt",
    "combined": "kswv2-combined.txt",
}
_BOUNDARY_FORMATTING = "\u200b\ufeff"


def normalize_entry(value):
    """Use NFC and trim edge whitespace, ZWSP and BOM; preserve internal text.

    This is a matching/data-cleaning policy, not Khmer spelling correction.
    """
    if not isinstance(value, str):
        raise TypeError("Dictionary entries and tokens must be strings")
    start, end = 0, len(value)
    while start < end and (
        value[start].isspace() or value[start] in _BOUNDARY_FORMATTING
    ):
        start += 1
    while end > start and (
        value[end - 1].isspace() or value[end - 1] in _BOUNDARY_FORMATTING
    ):
        end -= 1
    return unicodedata.normalize("NFC", value[start:end])


def _read_records(file_path):
    """Return (logical record number, raw value), including empty records."""
    path = Path(file_path)
    if path.suffix.lower() not in {".csv", ".txt"}:
        raise ValueError("Expected a headerless one-column .csv or a .txt file")
    records = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        if path.suffix.lower() == ".csv":
            try:
                for number, row in enumerate(csv.reader(source, strict=True), 1):
                    if len(row) > 1:
                        raise ValueError(
                            f"{path}: record {number}: expected one CSV column"
                        )
                    records.append((number, row[0] if row else ""))
            except csv.Error as exc:
                raise ValueError(f"{path}: malformed CSV: {exc}") from exc
        else:
            records = list(enumerate(source, 1))
    for number, raw in records:
        key = normalize_entry(raw)
        if any(unicodedata.category(char) == "Cc" for char in key):
            raise ValueError(f"{path}: record {number}: internal control character")
    return records


def load_stop_words(file_path=None, *, profile="core"):
    """Load a fresh set from a clean profile or a caller's headerless CSV/TXT.

    Missing files and malformed CSVs raise errors rather than silently disabling
    filtering. The original three CSV files are also supported.
    """
    if file_path is None:
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile {profile!r}; choose {tuple(PROFILES)}")
        file_path = DATA_DIR / "stopwords" / PROFILES[profile]
    return {
        key
        for _, raw in _read_records(file_path)
        if (key := normalize_entry(raw))
    }


def load_vocabulary():
    """Load the separate 81,005-word segmentation lexicon, without normalization.

    Vocabulary membership does not imply that a word is a stopword.
    """
    path = DATA_DIR / "vocabulary" / "khmer-vocabulary-81005.txt"
    return set(path.read_text(encoding="utf-8").splitlines())


def _key_set(entries, name):
    if isinstance(entries, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of strings, not one string")
    return {key for entry in entries if (key := normalize_entry(entry))}


def filter_tokens(tokens, stop_words=None, *, keep=()):
    """Filter complete segmented tokens and preserve the original retained text.

    `keep` overrides stopword membership. No substring deletion or automatic
    phrase merging is performed. Tokenization remains the caller's choice.
    """
    if isinstance(tokens, (str, bytes)):
        raise TypeError("Pass segmented tokens, not an unsegmented text string")
    stop_keys = _key_set(
        load_stop_words() if stop_words is None else stop_words, "stop_words"
    )
    keep_keys = _key_set(keep, "keep")
    result = []
    for token in tokens:
        key = normalize_entry(token)
        if key and (key in keep_keys or key not in stop_keys):
            result.append(token)
    return result
