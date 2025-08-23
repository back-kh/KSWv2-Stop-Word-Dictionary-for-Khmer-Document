
import csv
import re

# --- Optional Dependency Handling ---
try:
    from khmernltk import pos_tag as khmernltk_pos_tag
    KHMERNLTK_AVAILABLE = True
except ImportError:
    KHMERNLTK_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False



# --- Custom Segmentation Logic (Replaces external libraries) ---
def longest_match_segmenter(text, dictionary):
    """
    A simple dictionary-based word segmenter using the longest match principle.
    """
    words = []
    current_pos = 0
    # Clean up the text by removing zero-width spaces that can appear
    clean_text = text.replace('\u200b', '').replace('.', ' . ').replace('។', ' ។ ')
    text_len = len(clean_text)

    while current_pos < text_len:
        longest_word = ''
        for i in range(text_len, current_pos, -1):
            substring = clean_text[current_pos:i]
            if substring in dictionary:
                if len(substring) > len(longest_word):
                    longest_word = substring
        
        if not longest_word:
            # If no word is found, handle potential mix of Khmer and non-Khmer chars
            match = re.match(r'([\u1780-\u17FF]+|\s+|[a-zA-Z0-9]+|.)', clean_text[current_pos:])
            if match:
                longest_word = match.group(0)
            else:
                longest_word = clean_text[current_pos]

        if longest_word.strip():
            words.append(longest_word.strip())
        current_pos += len(longest_word)
    return words

def syllable_segmenter(text):
    """
    A basic rule-based syllable segmenter for Khmer.
    This is a simplified implementation.
    """
    syllable_pattern = r'([\u1780-\u17A2][\u17B6-\u17D3]*)'
    return [s for s in re.split(syllable_pattern, text) if s]


def load_stop_words_from_file(file_path):
    stop_words = set()
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    stop_words.add(row[0].strip())
    except FileNotFoundError:
        print(f"Error: Stop words file not found at {file_path}")
    return stop_words