"""
LEVEL 08 (advanced) - Interop: re + collections.Counter for word frequency
=============================================================================
You will learn
  * re.findall() is a natural tokenizer: pull out "word-shaped" chunks
  * feeding that token list straight into collections.Counter for frequency counts
  * combining the two removes any hand-rolled counting loop

Run: python level_08_interop_counter.py
"""
import re
from collections import Counter

TEXT = """
The quick brown fox jumps over the lazy dog.
The dog barks, but the fox is already gone.
"""

if __name__ == "__main__":
    # \b\w+\b tokenizes on word boundaries; lower() makes the count case-insensitive
    words = re.findall(r"\b\w+\b", TEXT.lower())
    assert words[:5] == ["the", "quick", "brown", "fox", "jumps"]

    counts = Counter(words)
    assert counts["the"] == 4      # "The"/"the" appears 4 times total
    assert counts["fox"] == 2
    assert counts["dog"] == 2

    top3 = counts.most_common(3)
    assert top3[0] == ("the", 4)   # most_common sorts by count, descending

    # re + Counter together answer "what are the 3 most common words?" in two lines,
    # with no manual dict bookkeeping.
    assert sum(counts.values()) == len(words)   # every token was counted exactly once

    print(f"total words: {len(words)}, unique words: {len(counts)}")
    print(f"top 3: {top3}")

    print("OK")
