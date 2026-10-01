# io — Core Tools for Working With Streams

`io` is the module behind every `open()` call in Python. It defines the layered
stream model (raw bytes -> buffering -> text decoding) that files, sockets, and
in-memory buffers all share. You reach for it directly (rather than just calling
`open()` and moving on) whenever you need: an in-memory file-like object
(`io.StringIO` / `io.BytesIO`) to hand to code that expects `.read()`/`.write()`
without touching disk; explicit control over buffering, encoding, or newline
handling; or a custom stream type that plugs into anything expecting file-like
behavior (e.g. `csv.writer`, `json.dump`, `shutil.copyfileobj`).

## When to reach for `io` vs alternatives in this repo

- Need a real file on disk with structured records -> see `PyStdLib/06_csv` or
  `PyStdLib/05_json` — they build on top of `io`, you rarely call raw `io` for
  structured data.
- Need to pass "file-like data" to a function/library without writing to disk in
  a test -> `io.StringIO`/`io.BytesIO` (this module, level 2/8).
- Need atomic, crash-safe file replacement -> see `PyEngineering/06_atomic_file_store`
  (temp file + `os.replace`), which sits one layer above what this module teaches.
- Need to stream a huge file without loading it into memory -> plain `io`
  buffered iteration (level 7 here) is usually enough; for line-oriented
  chunked parsing at scale see `PyEngineering/05_large_file_line_processor`.
- Need a custom transport (network, compression, encryption) that still looks
  like a file to the rest of your code -> subclass `io.RawIOBase` /
  `io.BufferedIOBase` (level 5 here).

## Gotchas

| Gotcha | Detail |
|---|---|
| `'w+'` position after write | Writing leaves the cursor at EOF; reading immediately returns `''` unless you `seek(0)` first. |
| Default encoding is not fixed | Text mode without `encoding=` uses `locale.getpreferredencoding()`, which differs across machines — always pass `encoding=` explicitly for portable code. |
| `buffering=0` only works in binary mode | Unbuffered text streams (`buffering=0` with mode `'r'`/`'w'`) raise `ValueError`; unbuffered is a binary-only concept. |
| Custom `RawIOBase` subclasses aren't buffered | Wrap them in `io.BufferedReader`/`BufferedWriter` if callers expect efficient chunked I/O. |
| `flush()` is not `fsync()` | `flush()` only pushes Python's/libc's buffers to the OS; the OS may still cache the write. Durability across a crash needs `os.fsync(fileobj.fileno())`. |
| Iterating a file object twice | A file iterator is exhausted after one pass; a second `for line in f` yields nothing unless you `seek(0)`. |

## What the 10 levels cover

Level 1 opens a file with each mode character and shows what problem it solves.
Level 2 covers the core read/write/readline API shared by real files and
`StringIO`/`BytesIO`. Level 3 combines `seek()`/`tell()` and `whence` into a
realistic "read the last N bytes" idiom. Level 4 triggers a real
`UnicodeDecodeError` from a bad `encoding=`/`errors=` combination and shows the
recovery options. Level 5 subclasses `io.RawIOBase` to build a minimal custom
stream. Level 6 measures `buffering=0` vs `-1` (default) vs a custom buffer
size with `time.perf_counter()`. Level 7 covers flush/fsync/close lifecycle
guarantees. Level 8 wraps a binary stream in `io.TextIOWrapper` for interop.
Level 9 demonstrates the `'w+'` seek gotcha failing, then fixes it. Level 10 is
a capstone log-processing program using most of the above together.
