# bytes — working with []byte buffers and slices

`bytes` is the `[]byte` counterpart to the `strings` package: it operates on
raw byte slices instead of immutable strings. Reach for it whenever data is
already a `[]byte` (file contents, network reads, hash input) and you want to
avoid the copy that converting to `string` would cost, or when you need a
growable byte buffer that satisfies `io.Writer`/`io.Reader`.

## When to reach for it vs alternatives already in this repo

- Building up output byte-by-byte or piece-by-piece → `bytes.Buffer`, which
  implements `io.Writer` (works with `fmt.Fprintf`, `io.Copy`, `json.Encoder`)
  and `io.Reader` at the same time.
- Building up a `string` from string pieces, no I/O interfaces needed →
  `strings.Builder` — cheaper, since it has no `Read` side to support and the
  compiler can sometimes avoid a copy on the final `.String()`. Prefer
  `strings.Builder` when the input and output are both text; prefer
  `bytes.Buffer` when you're already holding `[]byte` or need `io.Writer`.
- A read-only, seekable view over an existing `[]byte` → `bytes.NewReader`,
  not `bytes.Buffer` (a `Reader` is cheaper and also implements `io.Seeker`
  and `io.ReaderAt`, which `Buffer` does not).
- Comparing/searching immutable text → `strings` package equivalents
  (`strings.Compare`, `strings.Contains`, ...) if you already have a
  `string`; converting just to use `bytes.*` costs a copy for nothing.
- Whole-file line splitting → `bufio.Scanner`/`bufio.Reader` for streaming;
  `bytes.Split`/`bytes.Fields` are fine once the data is already in memory.

## Gotchas

| Gotcha | Detail |
|---|---|
| `Buffer.Bytes()` aliases internal storage | The slice it returns shares the buffer's backing array. Writing to the buffer again (even after `Reset`) can overwrite that data with nothing telling you. Copy it out (`append([]byte(nil), b...)` or `bytes.Clone`) if you need it to outlive the next write. |
| `[]byte`↔`string` conversion copies | `string(b)` and `[]byte(s)` both copy the underlying bytes (the compiler only skips the copy in a few narrow, provably-safe cases like `m[string(b)]` lookups). Converting in a hot loop is a measurable cost — see level 6. |
| `Buffer` zero value is ready to use | `var buf bytes.Buffer` needs no constructor; `new(bytes.Buffer)` and `bytes.Buffer{}` all work identically. Don't reach for `bytes.NewBuffer(nil)` out of habit. |
| Reading a `Buffer`/`Reader` past the end returns `io.EOF` | Not a special "empty" error type — the same sentinel every other `io.Reader` uses. Check with `errors.Is(err, io.EOF)`. |
| `bytes.Split` on an empty separator splits every <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8 rune | `bytes.Split(b, nil)` (or `[]byte{}`) splits after each rune, which surprises people expecting an error or a no-op. |
| `Reset()` keeps capacity | `buf.Reset()` sets length to 0 but keeps the allocated backing array — reuse it in loops instead of allocating a new `Buffer`, but remember this is exactly what makes the aliasing gotcha above dangerous. |

## What the 10 levels cover

Levels 1-2 build the everyday surface: `bytes.Buffer` (`Write`/`WriteString`/
`String`/`Bytes`/`Reset`) and the free-function toolkit (`Compare`, `Equal`,
`Contains`, `Index`, `Split`, `Join`, `Fields`). Level 3 combines them into a
small line-formatting idiom. Level 4 triggers a real `io.EOF` from
`Buffer.ReadString` and handles it properly. Level 5 shows the
reader/writer duality: `bytes.NewReader` as a seekable `io.Reader` over a
`[]byte`, paired with `io.Copy`. Level 6 is a measured comparison of
`bytes.Equal` against converting both sides to `string` first, showing the
real cost of the implicit copy. Level 7 covers `Buffer` capacity/reuse
lifecycle (`Grow`, `Cap`, `Reset`). Level 8 is interop: `io.Copy` from an
`*os.File` into a `bytes.Buffer`. Level 9 demonstrates the `Bytes()` aliasing
trap failing for real, then fixes it. Level 10 is a capstone that parses a
small `key=value` config blob and re-serializes it, using most of the above
together.
