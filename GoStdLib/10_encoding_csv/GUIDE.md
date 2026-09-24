# encoding/csv — reading and writing comma-separated values

`encoding/csv` reads and writes the CSV format described (loosely) by RFC
4180: comma-separated records, one per line, with a well-defined quoting rule
for fields that contain the delimiter, a quote character, or a newline.
Reach for it any time data crosses a boundary as rows-of-strings — export to
Excel/Sheets, import from another system, a quick tabular log — and you need
that boundary to survive real-world messy fields, not just the happy path.

## When to reach for it vs alternatives already in this repo

- Structured, nested, or typed data → `encoding/json` (see `../XX_encoding_json`
  if present) — CSV has no nesting and every value is a string.
- A one-off human-readable log line → `fmt.Fprintf` (see `../02_fmt`) is
  simpler when you never need to parse the line back into fields.
- Reading the file itself → pair with `os.Open`/`os.Create` (see `../01_os`);
  `csv.Reader`/`csv.Writer` only need an `io.Reader`/`io.Writer`, they don't
  know or care the source is a file.
- Manually joining fields with `strings.Join(fields, ",")` → never, once a
  field can contain a comma or newline — level 9 shows exactly how that
  silently corrupts data while looking correct in every simple test.

## Gotchas

| Gotcha | Detail |
|---|---|
| `Writer` buffers - `Flush()` is not optional | `csv.NewWriter` wraps a `bufio.Writer`; closing the file does not flush it. Small writes can sit in the buffer and vanish entirely if you skip `Flush()` (level 7). |
| `Flush()` swallows its error | The underlying write error from `Flush()` is stored on the `Writer`, not returned. Always check `w.Error()` after `Flush()`. |
| `FieldsPerRecord` defaults to "lock to the first row" | With the zero value, the width of record #1 becomes mandatory for every later record; a short/long row is a real `csv.ErrFieldCount`, not silently accepted (level 4). Set it to `-1` for intentionally ragged data. |
| A bare `"` outside quotes is a hard error by default | Real-world exports often contain one anyway. `Reader.LazyQuotes = true` tolerates it as a literal character instead of failing the whole record (level 5). |
| `Comma` is a rune, not always `,` | The same `Reader`/`Writer` parse TSV, pipe-delimited, or any single-rune-delimited format by setting `Comma` - no separate package needed (level 5). |
| Hand-joining fields "works" until it doesn't | `strings.Join(fields, ",")` passes every test where no field contains the delimiter, then silently reparses as extra columns the moment one does (level 9). `csv.Writer.Write` always quotes correctly. |

## What the 10 levels cover

Levels 1-2 build the everyday API: a full write-then-read round trip through
a real file, then the Reader/Writer fields (`Comment`, `TrimLeadingSpace`,
`FieldsPerRecord`, `UseCRLF`) that cover most real configurations. Level 3
writes the manual `Read()`-until-`io.EOF` streaming loop by hand, the shape
`ReadAll` hides from you. Level 4 triggers a real `csv.ErrFieldCount` and
handles it with `errors.Is`/`errors.As`, then shows the `-1` escape hatch.
Level 5 covers `LazyQuotes` and a custom `Comma` (TSV). Level 6 is a measured,
honestly-reported timing comparison between `ReadAll` and a `Read()` loop on
the same generated data. Level 7 proves the `Flush()` lesson concretely: zero
bytes on disk without it. Level 8 combines `csv` with `os`/`path/filepath` to
process a whole directory of CSV files. Level 9 is the production trap: naive
`strings.Join`-based writing corrupts a field with an embedded comma, silently,
and the fix is switching to `csv.Writer`. Level 10 is a capstone expense
report exercising writing, flushing, quoting-sensitive fields, streaming
reads, and field-count enforcement together.
