# Dictionary audit

Run `python scripts/build_resources.py --check` from the repository to reproduce
all counts and check the committed files. It needs no third-party packages.

| Profile | Input records | Raw unique | Exact duplicate excess records | Additional formatting duplicate excess records | Clean unique |
| --- | ---: | ---: | ---: | ---: | ---: |
| Core | 379 | 375 | 4 | 2 | 373 |
| Legacy | 385 | 383 | 2 | 2 | 381 |
| Expanded | 1,040 | 1,028 | 12 | 44 | 984 |

The combined union has **1,195** entries. There are 1,738 clean memberships
summed across the three profiles, with 543 excess memberships across files.
This differs from counting within-file duplicate records. A word occurring
three times contributes two excess records, not one. Formatting duplicate counts
exclude exact duplicates already counted.

- [`stopword-audit.json`](stopword-audit.json): per-source hashes, input/output
  counts, every changed record, every duplicate group with raw variants, and
  pairwise overlaps. ZWSP, ZWNJ, ZWJ and BOM characters are shown as JSON escapes
  while Khmer text stays readable. There are no
  retained internal formatting characters in the current clean source entries.
- [`stopword-provenance.json`](stopword-provenance.json): each combined entry
  maps to every original file and logical CSV record number, including duplicates.
  Some quoted records span physical lines; record numbers are not line numbers.

Only edge whitespace, U+200B and U+FEFF are trimmed, followed by NFC. Internal
text is preserved. Original CSVs are not rewritten. No spelling variants are
merged and no word is removed for a guessed linguistic reason.

The general vocabulary is checked separately: **81,005 unique entries**, with
no duplicate lines. The two source components have 80,999 and 213 entries and
share 207 entries; their union adds six legacy words to the ICU component.
Its [manifest](../data/vocabulary/manifest.json) records source and output hashes
and licensing. It must not be interpreted as a stopword list.

The English workbook and old segmentation experiments are outside this Khmer
stopword audit. This report is about data hygiene and reproducibility, not an
accuracy benchmark or expert certification of which words should be filtered.
