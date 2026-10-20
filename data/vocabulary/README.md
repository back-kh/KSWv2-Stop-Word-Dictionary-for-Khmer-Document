# General vocabulary: 81,005 entries

[`khmer-vocabulary-81005.txt`](khmer-vocabulary-81005.txt) is the same
segmentation vocabulary used by KhmerEasyTools at commit
[`705d1825deb94f969f4aa303b63a67f7cfd7f9a4`](https://github.com/back-kh/khmereasytools/tree/705d1825deb94f969f4aa303b63a67f7cfd7f9a4).
It is **not a stopword list** and must not be passed to stopword filtering.
Ordinary words such as `ប្រាសាទ`, `សាលារៀន` and `កម្ពុជា` belong in vocabulary.

The file is a sorted, exact set union of:

- 80,999 filtered ICU dictionary entries (Unicode License V3).
- 213 original KhmerEasyTools entries (MIT); six are additional to ICU.

This reuse adds no new corpus and makes no new authorship or segmentation
accuracy claim. Words, compounds and phrases may all occur; membership is
not a guarantee of spelling correctness. The union is not normalized.

[`manifest.json`](manifest.json) records both component hashes, the pinned
KhmerEasyTools revision, upstream ICU revision and filtering policy, and
the hash of this **union** file. The nested ICU `output_sha256` belongs to
the 80,999-entry component, not the union.

To reproduce it from a local checkout containing those exact components:

```bash
python scripts/import_vocabulary.py --ket-checkout ../khmereasytools --check
# Omit --check to rebuild the union after verifying both input hashes.
```

The main resource audit verifies the union and license checksums without
needing another checkout or an internet connection:

```bash
python scripts/build_resources.py --check
```

Licenses and original attribution are retained in
[`UNICODE-LICENSE.txt`](UNICODE-LICENSE.txt),
[`UPSTREAM-DICTIONARY-NOTICE.txt`](UPSTREAM-DICTIONARY-NOTICE.txt), and
[`LEGACY-MIT-LICENSE.txt`](LEGACY-MIT-LICENSE.txt). The original notice's
`khmerdict.txt` and `legacy_words.txt` refer to upstream component files;
the manifest maps them to this merged resource. The repository's root MIT
license does not replace these data notices.
