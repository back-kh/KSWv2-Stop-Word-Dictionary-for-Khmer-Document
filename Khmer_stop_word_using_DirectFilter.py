"""Filter already segmented, whitespace-delimited text with no dependencies.

Behavior change: never delete matching substrings inside unsegmented words.
For continuous Khmer text, choose a segmenter first (see README).
"""

from kswv2 import filter_tokens, load_stop_words


def remove_stop_words(text, stop_words, *, keep=()):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return " ".join(filter_tokens(text.split(), stop_words, keep=keep))


if __name__ == "__main__":
    text = "នេះ គឺជា ប្រាសាទ អង្គរវត្ត ស្ថិត នៅក្នុង ខេត្ត សៀមរាប ប្រទេស កម្ពុជា"
    print("Segmented input:", text)
    print("Filtered text:", remove_stop_words(text, load_stop_words()))
