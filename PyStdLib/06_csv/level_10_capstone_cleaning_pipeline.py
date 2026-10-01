"""
LEVEL 10 (capstone) - a small CSV data-cleaning pipeline, levels 1-9 together
================================================================================
You will learn
  * sniffing an unknown incoming dialect, reading it streaming with DictReader,
    validating/cleaning each row, and writing a normalized QUOTE_NONNUMERIC
    output file -- all correctly, with newline='' throughout
  * a realistic "ingest messy export, produce clean report" shape

Run: python level_10_capstone_cleaning_pipeline.py
"""
import csv
import os
import shutil
import tempfile


def write_messy_export(path: str) -> None:
    """A semicolon-delimited export with embedded commas/newlines/quotes."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write('id;name;note;amount\n')
        f.write('1;Ada;"ok, shipped";10.5\n')
        f.write('2;Grace;"multi\nline note";7\n')
        f.write('3;;"missing name";3\n')          # bad row: empty required field
        f.write('4;Rear;"has a \\"quote\\" mark";5\n'.replace("\\\"", '""'))


def clean_and_convert(src_path: str, dst_path: str) -> tuple[int, int]:
    """Stream src (unknown dialect), skip invalid rows, write a clean QUOTE_NONNUMERIC csv.

    Returns (rows_written, rows_rejected).
    """
    with open(src_path, newline="", encoding="utf-8") as f:
        sample = f.read(2048)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        reader = csv.DictReader(f, dialect=dialect)

        written = rejected = 0
        with open(dst_path, "w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(["id", "name", "note", "amount"])
            for row in reader:                      # streaming: one row at a time
                if not row.get("name"):
                    rejected += 1
                    continue
                writer.writerow([
                    int(row["id"]),
                    row["name"],
                    row["note"].replace("\n", " "),   # normalize embedded newlines
                    float(row["amount"]),
                ])
                written += 1
    return written, rejected


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "export.csv")
    dst = os.path.join(tmpdir, "clean.csv")
    try:
        write_messy_export(src)

        written, rejected = clean_and_convert(src, dst)
        assert written == 3      # rows 1, 2, 4
        assert rejected == 1     # row 3, missing name

        with open(dst, newline="", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            clean_rows = list(csv.reader(f, quoting=csv.QUOTE_NONNUMERIC))

        assert clean_rows[0] == ["id", "name", "note", "amount"]
        assert clean_rows[1] == [1.0, "Ada", "ok, shipped", 10.5]
        assert clean_rows[2] == [2.0, "Grace", "multi line note", 7.0]   # newline normalized
        assert clean_rows[3][1] == "Rear"
        assert '"' in content   # QUOTE_NONNUMERIC quoted every string field
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
