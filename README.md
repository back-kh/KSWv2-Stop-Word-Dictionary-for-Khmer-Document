# KSWv2: Khmer Stop Word Dictionary

Khmer stopword resources for keyword filtering and search preprocessing, with
reproducible cleanup, lightweight Python helpers, and a separate general vocabulary.

[![Dictionary validation](https://github.com/back-kh/KSWv2-Stop-Word-Dictionary-for-Khmer-Document/actions/workflows/validate.yml/badge.svg)](https://github.com/back-kh/KSWv2-Stop-Word-Dictionary-for-Khmer-Document/actions/workflows/validate.yml)

**The 81,005-word file is segmentation vocabulary, not 81,005 stopwords.**
It reuses the existing KhmerEasyTools lexicon with its original attribution.
The KSWv2 stopword union contains **1,195 distinct entries** after formatting cleanup.
No new training corpus or model is required.

## Choose a file

| Resource | Original CSV records | Clean unique entries | Download |
| --- | ---: | ---: | --- |
| Core (`khmer stopwords-corpus-1.csv`) | 379 | **373** | [kswv2-core.txt](data/stopwords/kswv2-core.txt) |
| Legacy (`khmer stopwords-corpus-385.csv`) | 385 | **381** | [kswv2-legacy.txt](data/stopwords/kswv2-legacy.txt) |
| Expanded (`Khmer-Stop-Word-1000.csv`) | 1,040 | **984** | [kswv2-expanded.txt](data/stopwords/kswv2-expanded.txt) |
| Combined union of all three | 1,804 across inputs | **1,195** | [kswv2-combined.txt](data/stopwords/kswv2-combined.txt) |
| General segmentation vocabulary | Separate resource | **81,005** | [khmer-vocabulary-81005.txt](data/vocabulary/khmer-vocabulary-81005.txt) |

Each clean file is UTF-8 with one entry per line, sorted by Unicode code point.
The original CSV files and the English workbook remain available unchanged.
The core profile is the default because it follows the latest small CSV; it is
not a linguistically certified safe list. Expanded and combined profiles are
more aggressive, and include content-bearing words and phrases.

## Daily use: no extra dependencies

Python 3.9 or newer is needed for the helpers. From a checkout:

```bash
git clone https://github.com/back-kh/KSWv2-Stop-Word-Dictionary-for-Khmer-Document.git
cd KSWv2-Stop-Word-Dictionary-for-Khmer-Document
python Khmer_stop_word_using_DirectFilter.py
```

This is a data repository with a local helper module; it is not a separate
PyPI package. Copy a clean TXT file into an existing project, or use `kswv2.py`
with its `data/` directory. Run the examples below from the checkout.

```python
from kswv2 import filter_tokens, load_stop_words, load_vocabulary

stop_words = load_stop_words()  # default: core, 373 unique entries
# Also supported: profile="legacy", "expanded", or "combined".
# Or use your own headerless one-column CSV or TXT:
# stop_words = load_stop_words("my-stopwords.csv")

tokens = ["នេះ", "គឺជា", "ប្រាសាទ", "អង្គរវត្ត", "នៅក្នុង", "កម្ពុជា"]
print(filter_tokens(tokens, stop_words))
# ['ប្រាសាទ', 'អង្គរវត្ត', 'កម្ពុជា']

# Keep negation or domain terms important to your task:
print(filter_tokens(["មិន", "ទៅ", "ទេ"], stop_words, keep={"មិន", "ទៅ", "ទេ"}))
# ['មិន', 'ទៅ', 'ទេ']

vocabulary = load_vocabulary()  # separate 81,005-word set; never used as stopwords
```

Filtering operates on **whole tokens**. A stopword `ការ` will not delete part of
`ការងារ`. Matching uses the same normalization as the cleaned stopword files;
retained tokens preserve their original text. Empty tokens are skipped. `keep`
overrides stopword membership. Multiword entries match only if the tokenizer
returns the entire entry as one token; the helper does not merge adjacent tokens.

**Continuous Khmer text must be segmented first.** The direct demo now splits
only at whitespace. This intentionally replaces its old substring deletion,
which could damage words. It does not infer Khmer word boundaries. For example,
passing `នេះគឺជាប្រាសាទ` to the direct demo will leave that continuous token intact.

## Use with KhmerEasyTools

[KhmerEasyTools](https://github.com/back-kh/khmereasytools) supplies segmentation
and other Khmer utilities. Pass a KSWv2 list explicitly:

```bash
pip install khmereasytools
```

```python
import khmereasytools as ket
from kswv2 import load_stop_words

stop_words = load_stop_words(profile="core") - {"មិន", "ទេ"}
text = "នេះគឺជាប្រាសាទអង្គរវត្តស្ថិតនៅក្នុងខេត្តសៀមរាបប្រទេសកម្ពុជា"
filtered = ket.khfilter(text, stop_words=stop_words)
print(filtered)
```

KSWv2 does not change KhmerEasyTools' built-in stopword defaults. `khfilter`
removes matching tokens; it does not by itself rank keywords or prove improved
retrieval quality. Segmentation behavior can vary by installed toolkit version.

## Optional segmentation demos

Install only the backend you want; neither is needed for loading files or
filtering existing tokens:

```bash
pip install khmercut
python Khmer_stop_word_using_KhmerCUT.py

pip install khmer-nltk
python Khmer_stop_word_using_KhmerNLTK.py
```

`requirements.txt` installs both demo backends if desired. They load lazily;
missing backends give an installation message. Demo files use the clean core
profile and work independently of the current working directory. Their
`load_stop_words(path)` functions still accept the original CSV paths.
The older segmentation experiments in `tools/` are not the daily-use API.

## What was cleaned and checked

The expanded CSV had **12 excess records from exact duplicates**, plus **44
additional excess records** that became duplicates after formatting cleanup.
The small core CSV had 4 exact and 2 additional formatting duplicate records;
the legacy CSV had 2 of each. Repeated entries such as `កាន់`, `នេះជា`,
`ក៏ដោយ` and `យ៉ាងណា` are recorded with their source record numbers.

Cleanup trims **boundary** whitespace, zero-width space (`U+200B`), and BOM
(`U+FEFF`), then applies NFC. It preserves internal spaces, joiners, and
zero-width spaces. It does not apply NFKC, rewrite Khmer spellings, or merge
lexical variants. Malformed multi-column CSVs and internal control characters
are rejected rather than silently truncated. CSV inputs have no header.

The audit counts logical CSV records, including quoted records that span more
than one physical line. See the [audit guide](reports/README.md),
[full duplicate and formatting report](reports/stopword-audit.json), and
[entry-to-source provenance](reports/stopword-provenance.json).
The separate [vocabulary manifest](data/vocabulary/manifest.json) pins upstream
revisions, component checksums, licenses, and the merged file checksum.

Rebuild or verify everything offline with the Python standard library:

```bash
python scripts/build_resources.py
python scripts/build_resources.py --check
python -m unittest discover -s tests -v
```

`--check` fails if a generated stopword file or audit report is stale, or if the
vocabulary or its recorded notices have changed. CI runs validation and tests
on Windows, macOS and Linux with Python 3.9 and 3.13.
Separate Python 3.11 jobs install the pinned optional test backends and run
the real KhmerCUT and Khmer-NLTK integration checks without skipping them.

## Use stopwords carefully

Stopword choice depends on the task. Negation, pronouns, numbers, and common
verbs can matter for search, sentiment, translation and question answering.
A larger list is not automatically better. For RAG, keep the original passage
for display and generation; filter a separate retrieval representation only
when an evaluation shows a benefit. Review negation-bearing phrases as well as
single words; a `keep={"មិន"}` override protects that exact token, not every
phrase beginning with it.

These changes establish deduplication, provenance and filtering behavior.
They do **not** establish improved keyword F1, retrieval ranking, semantic
correctness, or segmentation accuracy. That requires reviewed task data and a
comparison against no filtering and smaller lists. Contributions should include
source attribution, a reason for each proposed word, and reproducible checks.

## Licenses

KSW stopword resources and code retain the [MIT license](LICENSE).
The reused vocabulary has its own [Unicode and MIT notices](data/vocabulary/README.md).
Keep these notices when redistributing the vocabulary; it is not newly authored
KSW stopword data. No research POS model or noncommercial training corpus is added.

## Acknowledgements

- The collection team included students and researchers from **ITC (Cambodia)**.
- Funding support: **ITC (CAMBODIA) and ARES-CCD (BELGIUM)**.
- Project lead: **Nimol Thuon**.
- The additional general vocabulary is reused from KhmerEasyTools and the
  Unicode ICU dictionary, with their original notices retained.

## Citation

```bibtex
@article{thuon2024ksw,
  title={KSW: Khmer Stop Word based Dictionary for Keyword Extraction},
  author={Thuon, Nimol and Zhang, Wangrui and Thuon, Sada},
  journal={arXiv preprint arXiv:2405.17390},
  year={2024}
}
```
