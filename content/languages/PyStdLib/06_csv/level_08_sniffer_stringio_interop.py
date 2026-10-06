"""
LEVEL 08 (advanced) - interop: csv + io.StringIO, and csv.Sniffer for dialect detection
==========================================================================================
You will learn
  * csv.reader/writer work over any file-like object, including io.StringIO
  * csv.Sniffer().sniff(sample) inspects real text and guesses delimiter/quoting
  * using the sniffed dialect to then parse the rest of the data correctly

Run: python level_08_sniffer_stringio_interop.py
"""
import csv
import io


def main() -> None:
    # A CSV-shaped string that arrived over the network, not from disk --
    # csv.reader is happy to parse it straight out of a StringIO.
    comma_text = "id,name,dept\n1,Ada,Eng\n2,Grace,Ops\n"
    rows = list(csv.reader(io.StringIO(comma_text)))
    assert rows == [["id", "name", "dept"], ["1", "Ada", "Eng"], ["2", "Grace", "Ops"]]

    # Semicolon-delimited data, common in locales where comma is a decimal separator.
    semicolon_text = "id;name;dept\n1;Ada;Eng\n2;Grace;Ops\n"

    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(semicolon_text)
    assert dialect.delimiter == ";"

    parsed = list(csv.reader(io.StringIO(semicolon_text), dialect=dialect))
    assert parsed == [["id", "name", "dept"], ["1", "Ada", "Eng"], ["2", "Grace", "Ops"]]

    # sniff() can also tell you whether the sample looks like it has a header row.
    assert sniffer.has_header(semicolon_text) is True
    headerless = "1;Ada;Eng\n2;Grace;Ops\n3;Rear;Dev\n"
    assert sniffer.has_header(headerless) is False

    # Sniffer needs a real, representative sample -- too little text can guess wrong.
    # Restricting the delimiter candidates makes detection reliable even on a short sample.
    tab_text = "id\tname\n1\tAda\n"
    tab_dialect = sniffer.sniff(tab_text, delimiters=",;\t|")
    assert tab_dialect.delimiter == "\t"

    # Round-trip through StringIO both ways: write with csv.writer, sniff+read back.
    buf = io.StringIO()
    csv.writer(buf, delimiter="|").writerows([["a", "b"], ["1", "2"]])
    buf.seek(0)
    sample = buf.getvalue()
    detected = sniffer.sniff(sample, delimiters="|,;\t")
    buf.seek(0)
    assert list(csv.reader(buf, dialect=detected)) == [["a", "b"], ["1", "2"]]

    print("OK")


if __name__ == "__main__":
    main()
