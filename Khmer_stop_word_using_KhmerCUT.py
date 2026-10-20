"""Optional KhmerCUT segmentation followed by complete-token filtering."""

from kswv2 import filter_tokens, load_stop_words


def remove_stop_words(text, stop_words, *, keep=()):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    try:
        from khmercut import tokenize
    except ImportError as exc:
        raise RuntimeError("Install this optional backend: pip install khmercut") from exc
    return " ".join(filter_tokens(tokenize(text), stop_words, keep=keep))


if __name__ == "__main__":
    text = "នេះគឺជាប្រាសាទអង្គរវត្តស្ថិតនៅក្នុងខេត្តសៀមរាបប្រទេសកម្ពុជា"
    print("Original text:", text)
    print("Filtered text:", remove_stop_words(text, load_stop_words()))
