"""
LEVEL 04 (advanced) - real csv exceptions: ValueError from DictWriter, csv.Error
===================================================================================
You will learn
  * DictWriter raises ValueError when a row has a key not in fieldnames (default
    extrasaction='raise') -- catching this early prevents silently dropped columns
  * extrasaction='ignore' is the opt-in way to allow (and discard) extra keys
  * csv.Error is raised for structurally invalid dialect configuration

Run: python level_04_error_handling.py
"""
import csv
import io


def main() -> None:
    fieldnames = ["id", "name"]

    # A row with an unexpected extra key -- easy to introduce by accident when
    # the data source's shape drifts from what the writer was configured for.
    bad_row = {"id": "1", "name": "Ada", "extra_field": "oops"}

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)   # extrasaction='raise' is the default
    writer.writeheader()
    try:
        writer.writerow(bad_row)
        raise AssertionError("expected ValueError for an unlisted field")
    except ValueError as e:
        assert "extra_field" in str(e) or "fields not in fieldnames" in str(e)

    # extrasaction='ignore' opts into silently dropping unlisted keys instead.
    buf2 = io.StringIO()
    tolerant_writer = csv.DictWriter(buf2, fieldnames=fieldnames, extrasaction="ignore")
    tolerant_writer.writeheader()
    tolerant_writer.writerow(bad_row)   # no exception -- 'extra_field' is dropped
    buf2.seek(0)
    rows = list(csv.DictReader(buf2))
    assert rows == [{"id": "1", "name": "Ada"}]

    # A row MISSING a fieldnames key raises no error -- missing keys just become
    # restval (default ''), which is a different (and equally real) trap.
    buf3 = io.StringIO()
    writer3 = csv.DictWriter(buf3, fieldnames=fieldnames, restval="N/A")
    writer3.writeheader()
    writer3.writerow({"id": "2"})   # 'name' missing entirely
    buf3.seek(0)
    rows3 = list(csv.DictReader(buf3))
    assert rows3 == [{"id": "2", "name": "N/A"}]

    # csv.Error: a genuinely broken dialect configuration.
    try:
        csv.writer(io.StringIO(), delimiter="too-long")
        raise AssertionError("expected TypeError/csv.Error for a bad delimiter")
    except (csv.Error, TypeError) as e:
        assert "delimiter" in str(e).lower() or "1-character" in str(e)

    print("OK")


if __name__ == "__main__":
    main()
