import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import kswv2
from scripts import build_resources, import_vocabulary
import Khmer_stop_word_using_DirectFilter as direct
import Khmer_stop_word_using_KhmerCUT as cut_demo
import Khmer_stop_word_using_KhmerNLTK as nltk_demo


ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def load_temp(self, content, suffix=".csv"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ("words" + suffix)
            path.write_bytes(content)
            return kswv2.load_stop_words(path)

    def test_bom_blanks_duplicates_boundary_formatting_and_multiline_csv(self):
        source = '\ufeffក្នុង\n\n" ក្នុង\u200b "\n"\u200bវា"\n"ចេញពី\n"\n""\n'
        self.assertEqual(self.load_temp(source.encode()), {"ក្នុង", "វា", "ចេញពី"})

    def test_nfc_matching_without_compatibility_or_internal_rewriting(self):
        self.assertEqual(kswv2.normalize_entry(" \u200b\ufeffe\u0301\u200b "), "é")
        self.assertEqual(kswv2.normalize_entry("ក\u200bខ"), "ក\u200bខ")
        self.assertEqual(kswv2.normalize_entry("ក\u200dខ"), "ក\u200dខ")
        self.assertEqual(kswv2.normalize_entry("ក ខ"), "ក ខ")
        self.assertEqual(kswv2.normalize_entry("Ａ"), "Ａ")

    def test_empty_and_txt_crlf(self):
        self.assertEqual(self.load_temp(b""), set())
        self.assertEqual(self.load_temp("ក្នុង\r\nក្នុង \r\n".encode(), ".txt"), {"ក្នុង"})

    def test_multicolumn_unclosed_quote_and_internal_control_rejected(self):
        for source in [b"a,b\n", b'"unclosed', b'"a\nb"\n', b'"a\tb"\n']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.load_temp(source)

    def test_invalid_utf8_missing_path_unknown_profile_and_suffix(self):
        with self.assertRaises(UnicodeDecodeError):
            self.load_temp(b"\xff")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                kswv2.load_stop_words(Path(directory) / "missing.csv")
        with self.assertRaises(ValueError):
            kswv2.load_stop_words(profile="missing")
        with self.assertRaises(ValueError):
            self.load_temp(b"word", ".json")

    def test_profiles_are_independent_fresh_sets(self):
        expected = {"core": 373, "legacy": 381, "expanded": 984, "combined": 1195}
        for profile, count in expected.items():
            loaded = kswv2.load_stop_words(profile=profile)
            self.assertEqual(len(loaded), count)
            loaded.clear()
            self.assertEqual(len(kswv2.load_stop_words(profile=profile)), count)


class FilteringTests(unittest.TestCase):
    def test_substrings_inside_content_words_are_never_removed(self):
        self.assertEqual(
            kswv2.filter_tokens(["ការ", "ការងារ", "សាលារៀន", "កម្ពុជា"], {"ការ", "សាលា"}),
            ["ការងារ", "សាលារៀន", "កម្ពុជា"],
        )

    def test_normalized_lookup_retains_original_tokens_and_handles_generators(self):
        tokens = (token for token in [" \u200bវា ", "\u200be\u0301 ", "ក\u200bខ", "កខ"])
        stops = (word for word in ["វា", "កខ"])
        self.assertEqual(kswv2.filter_tokens(tokens, stops), ["\u200be\u0301 ", "ក\u200bខ"])
        self.assertEqual(kswv2.filter_tokens(["e\u0301"], {"é"}), [])

    def test_keep_override_protects_negation_and_domain_terms(self):
        tokens = ["ខ្ញុំ", "មិន", "ទៅ", "ទេ", "កម្ពុជា"]
        stops = {"ខ្ញុំ", "មិន", "ទេ", "កម្ពុជា"}
        self.assertEqual(
            kswv2.filter_tokens(tokens, stops, keep=(w for w in ["មិន", "ទេ", "កម្ពុជា"])),
            ["មិន", "ទៅ", "ទេ", "កម្ពុជា"],
        )
        self.assertEqual(stops, {"ខ្ញុំ", "មិន", "ទេ", "កម្ពុជា"})

    def test_phrases_are_not_merged_across_tokens(self):
        self.assertEqual(kswv2.filter_tokens(["នៅ", "ក្នុង"], {"នៅក្នុង"}), ["នៅ", "ក្នុង"])
        self.assertEqual(kswv2.filter_tokens(["នៅក្នុង"], {"នៅក្នុង"}), [])

    def test_no_default_filtering_for_explicit_empty_set(self):
        self.assertEqual(kswv2.filter_tokens(["ក្នុង"], set()), ["ក្នុង"])
        self.assertEqual(kswv2.filter_tokens(["ក្នុង"]), [])
        self.assertEqual(kswv2.filter_tokens(["", " \u200b ", "🙂", "OCR", "១២៣"], set()),
                         ["🙂", "OCR", "១២៣"])

    def test_bad_arguments_are_explicit(self):
        for tokens, stops, keep in [("ក្នុង", [], []), ([1], [], []),
                                    (["ក្នុង"], "ក្នុង", []), (["ក្នុង"], [], "ក្នុង")]:
            with self.subTest(tokens=tokens), self.assertRaises(TypeError):
                kswv2.filter_tokens(tokens, stops, keep=keep)

    def test_vocabulary_is_never_used_as_default_stopwords(self):
        self.assertIn("សាលារៀន", kswv2.load_vocabulary())
        self.assertEqual(kswv2.filter_tokens(["សាលារៀន"]), ["សាលារៀន"])


class DemoTests(unittest.TestCase):
    def test_direct_demo_is_safe_on_continuous_text(self):
        self.assertEqual(direct.remove_stop_words("ការងារ ការ", {"ការ"}), "ការងារ")
        self.assertEqual(direct.remove_stop_words("នេះគឺជាប្រាសាទ", {"នេះ", "គឺជា"}),
                         "នេះគឺជាប្រាសាទ")

    def test_importing_optional_demos_does_not_import_backends(self):
        code = (
            "import sys; import Khmer_stop_word_using_KhmerCUT; "
            "import Khmer_stop_word_using_KhmerNLTK; "
            "assert 'khmercut' not in sys.modules; assert 'khmernltk' not in sys.modules"
        )
        subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)

    def test_missing_optional_backend_is_actionable(self):
        for demo, module, install in [(cut_demo, "khmercut", "khmercut"),
                                      (nltk_demo, "khmernltk", "khmer-nltk")]:
            with self.subTest(module=module), mock.patch.dict(sys.modules, {module: None}):
                with self.assertRaisesRegex(RuntimeError, "pip install " + install):
                    demo.remove_stop_words("ខ្មែរ", set())

    def test_direct_demo_works_outside_checkout_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "Khmer_stop_word_using_DirectFilter.py")],
                cwd=directory, capture_output=True, check=True,
            )
            self.assertIn("អង្គរវត្ត", result.stdout.decode("utf-8"))


class ReproducibilityTests(unittest.TestCase):
    def test_committed_resources_exactly_reproduce(self):
        outputs, _ = build_resources.build_stopwords()
        for relative, expected in outputs.items():
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), expected)

    def test_duplicate_accounting_and_record_level_provenance(self):
        _, report = build_resources.build_stopwords()
        expected = {"core": (379, 4, 2, 373), "legacy": (385, 2, 2, 381),
                    "expanded": (1040, 12, 44, 984)}
        for source in report["sources"]:
            self.assertEqual((source["csv_records"], source["exact_duplicate_excess_records"],
                              source["additional_formatting_duplicate_excess_records"],
                              source["clean_unique_entries"]), expected[source["profile"]])
        provenance = json.loads((ROOT / "reports/stopword-provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(len(provenance), 1195)
        self.assertEqual(sum(map(len, provenance.values())), 1804)
        self.assertIn({"source": "khmer stopwords-corpus-1.csv", "record": 4}, provenance["ប្រាំ"])

    def test_vocabulary_checksums_and_independence(self):
        self.assertEqual(build_resources.verify_vocabulary(), 81005)
        self.assertEqual(len(kswv2.load_vocabulary()), 81005)
        self.assertNotEqual(kswv2.load_vocabulary(), kswv2.load_stop_words(profile="combined"))

    def test_vocabulary_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "data/vocabulary"
            base.mkdir(parents=True)
            manifest = json.loads((ROOT / "data/vocabulary/manifest.json").read_text(encoding="utf-8"))
            (base / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (base / manifest["output_file"]).write_text("ក\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "count"):
                build_resources.verify_vocabulary(directory)

    def test_invalid_vocabulary_source_fails_before_overwriting_output(self):
        with tempfile.TemporaryDirectory() as directory:
            before = (ROOT / "data/vocabulary/khmer-vocabulary-81005.txt").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(import_vocabulary.main(["--ket-checkout", directory]), 1)
            self.assertEqual((ROOT / "data/vocabulary/khmer-vocabulary-81005.txt").read_bytes(), before)

    def test_resource_check_cli_detects_stale_output_without_writing(self):
        outputs, _ = build_resources.build_stopwords()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative, data in outputs.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            damaged = root / "data/stopwords/kswv2-core.txt"
            damaged.write_bytes(b"stale\n")
            with mock.patch.object(build_resources, "ROOT", root), \
                    mock.patch.object(build_resources, "verify_vocabulary", return_value=81005), \
                    mock.patch.object(build_resources, "build_stopwords", return_value=(outputs, {})), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(build_resources.main(["--check"]), 1)
            self.assertEqual(damaged.read_bytes(), b"stale\n")


if __name__ == "__main__":
    unittest.main()
