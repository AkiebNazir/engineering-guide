"""
LEVEL 04 (advanced) - encoding/errors=, and a real UnicodeDecodeError
======================================================================
You will learn
  * text mode always encodes/decodes through a codec -- binary mode never does
  * a mismatched encoding produces a genuine UnicodeDecodeError, not a garbled string
  * the errors= handlers that let you recover: 'strict' (default), 'replace', 'ignore'

Run: python level_04_encoding_errors.py
"""
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "greeting.txt")
    try:
        text = "café ☃"   # 'é' and a snowman -- both outside plain ASCII
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        # Reading back with the SAME encoding round-trips perfectly.
        with open(path, encoding="utf-8") as f:
            assert f.read() == text

        # Reading UTF-8 bytes as if they were Latin-1 is *not* an error -- Latin-1
        # maps every byte to a code point, so it silently produces mojibake.
        with open(path, encoding="latin-1") as f:
            mojibake = f.read()
        assert mojibake != text   # wrong, but no exception -- the dangerous case

        # A codec that genuinely cannot map the bytes raises UnicodeDecodeError for real.
        raw_bytes = text.encode("utf-8")
        assert b"\xc3\xa9" in raw_bytes   # utf-8 encoding of 'é'
        try:
            raw_bytes.decode("ascii")
            raise AssertionError("expected UnicodeDecodeError")
        except UnicodeDecodeError as e:
            assert e.encoding == "ascii"
            assert e.start >= 0            # byte offset where decoding failed

        # The same failure happens through open(..., encoding="ascii") on a real file.
        try:
            with open(path, encoding="ascii") as f:
                f.read()
            raise AssertionError("expected UnicodeDecodeError")
        except UnicodeDecodeError:
            pass

        # errors= lets you choose what happens instead of raising.
        with open(path, encoding="ascii", errors="replace") as f:
            replaced = f.read()
        assert "�" in replaced        # unmappable bytes become U+FFFD

        with open(path, encoding="ascii", errors="ignore") as f:
            ignored = f.read()
        assert ignored == "caf "           # unmappable bytes silently dropped
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
