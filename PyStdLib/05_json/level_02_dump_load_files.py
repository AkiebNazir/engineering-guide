"""
LEVEL 02 (core) - json.dump()/json.load() with real files, indent=, sort_keys=
=================================================================================
You will learn
  * dump()/load() work directly against an open file handle -- no manual read()/write()
  * indent= produces human-readable, multi-line JSON
  * sort_keys= gives deterministic key order, useful for diffs and tests
  * ensure_ascii=False keeps unicode characters literal instead of \\uXXXX-escaped

Run: python level_02_dump_load_files.py
"""
import json
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "config.json")
    try:
        config = {"retries": 3, "host": "localhost", "timeout": 5.0}

        # dump() writes straight to a file object -- no intermediate string needed.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f)

        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == config

        # indent= pretty-prints with that many spaces per nesting level.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, sort_keys=True)
        with open(path, encoding="utf-8") as f:
            pretty = f.read()
        assert pretty == (
            "{\n"
            '  "host": "localhost",\n'
            '  "retries": 3,\n'
            '  "timeout": 5.0\n'
            "}"
        )
        # sort_keys= made the order alphabetical regardless of insertion order.
        assert pretty.index('"host"') < pretty.index('"retries"') < pretty.index('"timeout"')

        # ensure_ascii (default True) escapes non-ASCII to \\uXXXX.
        unicode_data = {"city": "Zürich"}
        escaped = json.dumps(unicode_data)
        assert "\\u00fc" in escaped and "ü" not in escaped

        # ensure_ascii=False keeps the literal characters -- smaller, more readable.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unicode_data, f, ensure_ascii=False)
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        assert "ü" in raw
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == unicode_data   # round-trips fine either way
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
