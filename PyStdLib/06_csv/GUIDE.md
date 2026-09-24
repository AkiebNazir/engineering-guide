# csv — Reading and Writing CSV Files Correctly

`csv` parses and writes the deceptively-hard comma-separated-value format: fields
with embedded commas, quotes, and even newlines, quoting rules that differ between
"Excel CSV" and "Unix CSV", and encoding concerns layered on top. Hand-rolling
`line.split(",")` looks fine until the first field contains a comma or a quoted
newline, then it silently corrupts data. `csv` gets this right.

## When to reach for `csv` vs alternatives in this repo

- Need nested/structured data (objects inside objects, arrays of mixed types)
  -> `PyStdLib/05_json` — CSV is strictly flat, rows of scalar fields.
- Need real spreadsheet features (formulas, multiple sheets, formatting)
  -> outside stdlib entirely; this module only reads/writes plain delimited text.
  the file-conventions/curriculum docs in this repo don't cover a spreadsheet
  library, since none is stdlib.
- Need to stream a file too big for memory -> this module's reader/writer are
  already iterator-based (see level 7 here); for line-oriented processing at
  larger scale see `PyEngineering/05_large_file_line_processor`.
- Need the data as Python objects (not raw rows) with header-based access
  -> `csv.DictReader`/`DictWriter` (level 2 here) rather than hand-mapping
  `reader()` rows to field names yourself.

## Gotchas

| Gotcha | Detail |
|---|---|
| Missing `newline=''` on `open()` | Without it, universal-newline translation can silently rewrite `\r`/`\r\n` bytes embedded inside quoted fields before `csv` ever sees them — the Python docs call this out explicitly. |
| `DictWriter` with an unlisted field | Writing a row dict containing a key not in `fieldnames` raises `ValueError` by default (`extrasaction='raise'`). |
| `QUOTE_NONNUMERIC` on read | With this quoting mode, the *reader* converts every unquoted field to `float` — a schema assumption that breaks on non-numeric data. |
| Dialect guessing isn't magic | `csv.Sniffer().sniff()` needs a reasonably large, representative sample — a tiny or unusual sample can guess the wrong delimiter. |
| Excel vs Unix dialect | `excel` (the default) writes `\r\n` line endings and quotes minimally; `unix_dialect` writes `\n` and quotes every field (`QUOTE_ALL`). |
| `list(reader)` on a huge file | Defeats the whole point of streaming — the reader itself is a lazy iterator; only materialize it into a list when you actually need random access. |

## What the 10 levels cover

Level 1 is the basic `reader`/`writer` round trip over a real file. Level 2
covers `DictReader`/`DictWriter` with `fieldnames`. Level 3 combines both into
a realistic idiom: fields with embedded commas, quotes, and newlines,
round-tripping correctly. Level 4 triggers real exceptions (`csv.Error`,
`ValueError` from `DictWriter`) and handles them. Level 5 covers dialects
(`excel` vs `unix`) and the four quoting modes with custom `delimiter=`/
`quotechar=`. Level 6 measures `csv.reader` vs `csv.DictReader` overhead with
`time.perf_counter()`. Level 7 streams a large file row-by-row without
loading it fully into memory. Level 8 pairs `csv` with `io.StringIO` and
`csv.Sniffer` to detect a dialect from an in-memory sample. Level 9
demonstrates the `newline=''` gotcha actually corrupting data, then the fix.
Level 10 is a capstone: a small CSV-based data-cleaning pipeline.
