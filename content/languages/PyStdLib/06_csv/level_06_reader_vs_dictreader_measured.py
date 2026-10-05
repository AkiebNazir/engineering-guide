"""
LEVEL 06 (advanced) - measured: csv.reader vs csv.DictReader overhead
========================================================================
You will learn
  * DictReader builds a dict per row (using the header as keys) -- reader gives
    plain lists
  * measuring the real per-row cost of that convenience with time.perf_counter(),
    instead of assuming it's negligible

Run: python level_06_reader_vs_dictreader_measured.py
"""
import csv
import io
import time

ROW_COUNT = 50_000


def build_csv_text() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "score"])
    for i in range(ROW_COUNT):
        writer.writerow([i, f"item-{i}", i * 1.5])
    return buf.getvalue()


def time_reader(text: str) -> float:
    start = time.perf_counter()
    rows = list(csv.reader(io.StringIO(text)))
    elapsed = time.perf_counter() - start
    assert len(rows) == ROW_COUNT + 1   # +1 for the header row
    return elapsed


def time_dictreader(text: str) -> float:
    start = time.perf_counter()
    rows = list(csv.DictReader(io.StringIO(text)))
    elapsed = time.perf_counter() - start
    assert len(rows) == ROW_COUNT
    return elapsed


def main() -> None:
    text = build_csv_text()

    reader_time = time_reader(text)
    dictreader_time = time_dictreader(text)

    print(f"csv.reader,     {ROW_COUNT} rows: {reader_time:.4f}s")
    print(f"csv.DictReader, {ROW_COUNT} rows: {dictreader_time:.4f}s")
    if reader_time > 0:
        print(f"DictReader took {dictreader_time / reader_time:.2f}x the time of reader on this run")

    assert reader_time > 0 and dictreader_time > 0
    # This is the real, measured claim: DictReader's per-row dict construction
    # costs real time over plain lists. Report the actual ratio, not an assumption.
    assert dictreader_time > reader_time, (
        f"unexpected: DictReader ({dictreader_time:.4f}s) was not slower than "
        f"reader ({reader_time:.4f}s) on this run"
    )

    print("OK")


if __name__ == "__main__":
    main()
