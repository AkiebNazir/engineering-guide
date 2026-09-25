# strings — string manipulation

`strings` operates on Go's immutable `string` type: searching, splitting,
joining, trimming, replacing, comparing. It is the first place to look before
reaching for `regexp` (heavier, slower, only needed for real patterns) or
manual byte-index loops (error-prone with <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8).

## When to reach for it vs alternatives already in this repo

- Building a string piece by piece in a loop → `strings.Builder` (level 6),
  not repeated `+=` concatenation, which reallocates and copies every time.
- Reading a string through an `io.Reader`-shaped <abbr title="Application Programming Interface">API</abbr> (e.g. to hand to
  `bufio.NewReader`, see `../04_bufio`) → `strings.NewReader` (level 4), not
  converting to `[]byte` and writing a custom reader.
- Many different substring replacements in one pass → `strings.NewReplacer`
  (level 5), not several chained `strings.ReplaceAll` calls (each is a full
  extra pass over the string).
- A genuine pattern (wildcards, alternation, backreferences) → `regexp`, out
  of scope here; `strings` only does literal/exact matching.
- Formatting values into a string → pair with `strconv` (see `../06_strconv`)
  for numbers, not `fmt.Sprintf` in a hot loop.

## Gotchas

| Gotcha | Detail |
|---|---|
| `TrimLeft`/`TrimRight` take a **cutset**, not a prefix | `strings.TrimLeft(s, "xy")` strips ANY leading run of `'x'` or `'y'` characters, not the literal substring `"xy"`. For an exact prefix/suffix, use `TrimPrefix`/`TrimSuffix` (level 9). |
| `+=` concatenation in a loop is O(n²) | Each `+=` allocates a new string and copies everything so far; `strings.Builder` grows a buffer and copies each byte at most a small constant number of times (level 6). |
| `Replace(s, old, new, n)`'s `n` is a count, not a boolean | `n < 0` means "replace all" (same as `ReplaceAll`); `n == 0` means replace nothing at all - easy to typo as "replace once". |
| `EqualFold` is not the same as `strings.ToLower(a) == strings.ToLower(b)` | `EqualFold` does Unicode case-folding correctly for cases simple lower-casing gets wrong, and never allocates. |
| `strings.Reader` reads return `io.EOF` like any `io.Reader` | Forgetting to check for `io.EOF` when driving a `strings.Reader` manually looks like "it just stops" instead of a clear signal. |

## What the 10 levels cover

Levels 1-2 build the everyday <abbr title="Application Programming Interface">API</abbr>: substring checks (`Contains`/`HasPrefix`/
`HasSuffix`), then `Split`/`SplitN`/`Fields`, `Replace`/`ReplaceAll`, and the
`Trim*` family. Level 3 combines them into a small record-cleaning idiom.
Level 4 uses `strings.Reader` as a real `io.Reader` and handles `io.EOF` for
real. Level 5 measures `strings.NewReplacer` against chained `ReplaceAll`
calls. Level 6 measures `strings.Builder` against `+=` concatenation at scale.
Level 7 is a second intermediate pattern: `Compare` and `EqualFold` for
case-insensitive sorting and matching. Level 8 interops with `strconv` to
parse and reformat a delimited numeric string. Level 9 demonstrates the
`TrimLeft`/cutset trap and fixes it with `TrimPrefix`. Level 10 is a capstone
log-line normalizer exercising most of the above together.
