# io — core I/O primitives

`io` defines the interfaces (`Reader`, `Writer`, `Closer`, and their
combinations) that make files, network connections, in-memory buffers, and
compressors all interchangeable, plus a handful of functions that operate on
any of them: `Copy`, `ReadAll`, `Pipe`, `MultiWriter`, `TeeReader`,
`LimitReader`. Almost everything else in the standard library that does I/O
(`os`, `net`, `bufio`, `compress/*`, `crypto/*`) is built on these few
interfaces.

## When to reach for it vs alternatives already in this repo

- Copying bytes from one stream to another → `io.Copy`, not a manual
  read/write loop, unless you need to observe or transform each chunk.
- Reading a whole stream into memory → `io.ReadAll` for a stream of unknown
  size at read time; prefer `os.ReadFile` (`../01_os`) when you specifically
  have a file path, since it can pre-size the buffer with `Stat`.
- Writing formatted text to a stream → pair with `fmt.Fprintf` (`../02_fmt`);
  `io` itself only moves and shapes bytes, it doesn't format them.
- Capping how much a caller can read (untrusted input, request bodies) →
  `io.LimitReader`, not a manual byte counter.
- Duplicating a stream to two destinations (e.g. logging while forwarding) →
  `io.MultiWriter`/`io.TeeReader`, not two independent read loops.
- Line-oriented or buffered reading → `bufio.Scanner`/`bufio.Reader` layered
  on top of an `io.Reader` (out of scope here; this module's `io` levels stay
  at the raw `Read`/`Write` level).

## Gotchas

| Gotcha | Detail |
|---|---|
| `Read` can return `n > 0` AND `err == io.EOF` in the SAME call | The contract explicitly allows this: process the `n` bytes first, THEN check the error. Checking the error before using `n` silently drops the last chunk. |
| `io.EOF` is a plain sentinel `error` value, not a panic | It means "no more data," a normal, expected condition — treat it as control flow via `errors.Is(err, io.EOF)`, never as a crash. |
| A zero-byte, nil-error `Read` is technically legal but rare | Callers should treat it as "try again," per the `io.Reader` doc comment — don't assume every `Read` call makes progress. |
| `io.Copy` returns `(0, nil)` at true EOF, not an error | `io.EOF` from the source is not surfaced by `Copy`/`ReadAll` — it's consumed internally and reported as a clean nil error. |
| `io.Pipe` is fully synchronous | A `Write` blocks until a matching `Read` consumes it (there is no internal buffer) — writing on the same goroutine that later reads deadlocks; always use a separate goroutine for one side. |
| `MultiWriter`/`TeeReader` stop at the first error | If one of several destinations in a `MultiWriter` errors, the whole write fails immediately — the other destinations may have already received a partial write. |

## What the 10 levels cover

Levels 1-2 establish the interfaces themselves (`Reader`, `Writer`, `Closer`,
`ReadWriter`) and the single most common function, `io.Copy`. Level 3 adds
`io.ReadAll` and `io.LimitReader`. Level 4 triggers and handles the real
`io.EOF` idiom, including the `n>0`-with-`EOF` case from a custom `Read`.
Level 5 covers `MultiWriter` and `TeeReader`. Level 6 measures `io.Copy`
against different buffer sizes with real timings. Level 7 covers `io.Pipe`
connecting a writer goroutine to a reader synchronously, plus its
close/lifecycle rules. Level 8 shows `os` + `io` interop end to end. Level 9
demonstrates a partial-read correctness trap (assuming one `Read` fills the
whole buffer) and its fix. Level 10 is a capstone that writes a minimal
custom `Reader` from scratch and drives it through `io.Copy`,
`io.LimitReader`, and a `MultiWriter` together.
