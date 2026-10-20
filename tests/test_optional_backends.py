"""Small real-backend integration checks; not segmentation accuracy benchmarks."""

import importlib.util
import os
import unittest

from kswv2 import load_stop_words
import Khmer_stop_word_using_KhmerCUT as cut_demo
import Khmer_stop_word_using_KhmerNLTK as nltk_demo


REQUIRE_BACKENDS = os.environ.get("KSWV2_REQUIRE_BACKENDS") == "1"


class OptionalBackendTests(unittest.TestCase):
    @unittest.skipUnless(REQUIRE_BACKENDS or importlib.util.find_spec("khmercut"),
                         "optional khmercut is not installed")
    def test_real_khmercut_segmentation_and_filtering(self):
        self.assertEqual(
            cut_demo.remove_stop_words("នេះគឺជាប្រាសាទអង្គរវត្ត", load_stop_words()),
            "ប្រាសាទ អង្គរវត្ត",
        )
        self.assertEqual(cut_demo.remove_stop_words("", load_stop_words()), "")

    @unittest.skipUnless(REQUIRE_BACKENDS or importlib.util.find_spec("khmernltk"),
                         "optional khmer-nltk is not installed")
    def test_real_khmer_nltk_segmentation_and_filtering(self):
        self.assertEqual(
            nltk_demo.remove_stop_words("នេះគឺជាប្រាសាទអង្គរវត្ត", load_stop_words()),
            "ប្រាសាទ អង្គរវត្ត",
        )
        self.assertEqual(nltk_demo.remove_stop_words("", load_stop_words()), "")


if __name__ == "__main__":
    unittest.main()
