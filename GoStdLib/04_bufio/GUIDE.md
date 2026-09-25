# bufio — buffered I/O

`bufio` wraps an `io.Reader` or `io.Writer` with an in-memory buffer so the
program makes far fewer, larger syscalls instead of one syscall per small
read/write. Reach for it any time you're doing many small reads or writes
against something backed by a real syscall (a file, a socket, stdin) — the
underlying `io.Reader`/`io.Writer` never buffers on its own.

## When to reach for it vs alternatives already in this repo

- Reading a file line by line → `bufio.NewScanner` (level 1), not
  `os.ReadFile` + manual splitting when the file may be large or streamed.
- One-shot "give me the whole file" → plain `os.ReadFile` is simpler and
  already buffers internally; don't add a `bufio.Reader` on top of it.
- Reading up to a delimiter, or peeking ahead without consuming →
  `bufio.Reader.ReadString`/`ReadBytes`/`Peek` (level 2) — a raw `io.Reader`
  has no peek and no delimiter-aware read.
- Writing many small pieces to a file/socket → `bufio.Writer` (levels 6-7),
  always paired with `Flush()` before the underlying writer is closed.
- Custom framing (records separated by something other than `\n`) →
  a `bufio.SplitFunc` (level 5), not manual byte-scanning loops.

## Gotchas

| Gotcha | Detail |
|---|---|
| Scanner's default token buffer is 64KB | A single line/token longer than ~64KB makes `Scan()` return `false` and `Err()` return `bufio.ErrTooLong`. Fix with `Scanner.Buffer(buf, max)` before scanning (level 4). |
| `Writer.Flush()` is not automatic | Bytes written to a `bufio.Writer` sit in memory until `Flush()` runs or the buffer fills. Forgetting it (e.g. before closing the underlying file) silently drops the tail of the output (level 7). |
| `Scanner.Bytes()` is reused every call | The `[]byte` returned aliases the scanner's internal buffer; it is overwritten on the next `Scan()`. Keeping it past the next iteration without copying corrupts already-stored data (level 9). |
| A `SplitFunc` must handle `atEOF` | A custom split function that doesn't return the final, delimiter-less token when `atEOF` is true silently drops the last record. |
| Wrapping an already-buffered reader adds nothing but latency | Double-buffering (e.g. `bufio.NewReader` around an `*os.File` already read via `os.ReadFile`) just copies bytes twice for no benefit. |

## What the 10 levels cover

Levels 1-2 build the everyday <abbr title="Application Programming Interface">API</abbr>: `Scanner` reading lines (the single most
common use), then `Reader`'s `ReadString`/`ReadBytes`/`Peek`. Level 3 combines
`Scanner` and `Writer` into a small realistic line-filtering idiom. Level 4
triggers a real `bufio.ErrTooLong` and fixes it with `Scanner.Buffer`. Level 5
writes a custom `SplitFunc` for a non-newline delimiter. Level 6 measures
buffered vs unbuffered writes over many small chunks with real timings. Level
7 proves that a forgotten `Flush()` silently loses buffered output, then fixes
it. Level 8 interops `bufio.Reader` with a `strings.Reader` source and
`strconv` parsing. Level 9 demonstrates the `Scanner.Bytes()` aliasing trap and
fixes it by copying. Level 10 is a capstone log-line processor that reads
long/short lines with a resized buffer, avoids the aliasing trap, and writes a
flushed summary.
