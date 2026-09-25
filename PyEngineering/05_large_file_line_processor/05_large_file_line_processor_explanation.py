"""
05 · Large File Line Processor
===============================

WHAT WE'RE BUILDING
--------------------
A robust processor for multi-gigabyte log or CSV files that never holds the whole file
in memory. It reads line by line, aggregates metrics, and handles malformed lines
gracefully.

WHY THIS MATTERS
----------------
"Out of Memory" (OOM) is the most common crash for data ingestion jobs. You must learn
to yield data as a generator rather than returning a massive list.
"""

def process_large_file(filepath: str):
    valid_count = 0
    error_count = 0
    with open(filepath, 'r') as f:
        for line in f:
            try:
                # simulate processing
                if line.strip():
                    valid_count += 1
            except Exception:
                error_count += 1
    return valid_count, error_count
