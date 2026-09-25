# fmt — formatted I/O

`fmt` formats values into strings and writes them to any destination that
implements `io.Writer`. It's the package behind `Println` debugging, building
error messages, and every human-readable log line in a Go program.

## When to reach for it vs alternatives already in this repo

- Ad-hoc debugging output → `fmt.Println`/`Printf` to stdout.
- Building a string from parts → `fmt.Sprintf` for a few values; `strings.Builder`
  when concatenating in a loop (level 6 measures the difference for real).
- Writing formatted output to a file/socket/buffer → `fmt.Fprintf` with that
  destination's `io.Writer` (see `../03_io` for the interface itself).
- Wrapping an error with context → `fmt.Errorf("...: %w", err)`, then
  `errors.Is`/`errors.As` to inspect it — not manual string concatenation.
- A custom human-readable representation for your type → implement `String()
  string` (the `Stringer` interface) so `%v`/`Println` pick it up automatically;
  reach for the lower-level `fmt.Formatter` interface only when you need to
  react to the verb itself (`%x` vs `%d` vs `%v`) or to flags/width.
- Structured machine-readable output → `encoding/json`, not `fmt.Sprintf` with
  hand-built <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> strings (out of scope here).

## Gotchas

| Gotcha | Detail |
|---|---|
| Mismatched verb/argument does not panic | `fmt.Sprintf("%d", "hi")` returns the string `%!d(string=hi)` instead of erroring — it silently pollutes output unless you're looking for `%!` in logs. `go vet` catches many of these at compile time; the runtime call itself never complains. |
| A custom `Format` method must handle every verb it cares about | If a type implements `fmt.Formatter` and its `Format` method's switch has no case (and no default) for a given verb, NOTHING is written for that call — not an error, just silent empty output. |
| `%v` on a pointer vs a value | `%v` on a `*T` whose `T` has a value-receiver `String()` still calls it (Go dereferences automatically for interface satisfaction here in practice via method sets), but a POINTER-receiver `String()` is NOT in the method set of a plain value — passing `T{}` (not `&T{}`) to `Printf("%v", ...)` skips `String()` entirely. |
| `%+v` vs `%#v` | `%+v` adds field names to a struct's default form; `%#v` prints a Go-syntax representation (including the type name) — easy to reach for the wrong one when debugging. |
| `Errorf`'s `%w` only wraps one error per call (pre-Go 1.20) | Go 1.20+ allows multiple `%w` verbs in one `Errorf`, producing a multi-error unwrapped by `errors.Is`/`As` doing a tree walk — easy to assume only one `%w` is ever allowed. |
| `Scanf` matches literal whitespace loosely but literal text exactly | Non-space characters in the format string must match the input byte-for-byte, or `Scanf` stops and returns an error with a partial result. |

## What the 10 levels cover

Levels 1-3 build the everyday surface: `Println`/`Printf`, the verb table
(`%v %+v %#v %T %q %x %p`), and using `Sprintf` plus width/precision
(`%6.2f`) to build formatted strings. Level 4 triggers a real wrapped error
with `%w` and unwraps it with `errors.Is`/`As`. Level 5 reads non-interactive
input with `Scan`/`Scanf`/`Scanln` from a `strings.Reader`. Level 6 measures
`Sprintf`-in-a-loop against `strings.Builder` with real timings. Level 7
implements `Stringer` so `%v` and `Println` call it automatically. Level 8
writes with `Fprintf` to arbitrary `io.Writer` destinations, not just stdout.
Level 9 implements `fmt.Formatter` for custom verb handling and demonstrates,
for real, the silent-empty-output trap of an unhandled verb before fixing it.
Level 10 is a capstone report printer combining Stringer, Fprintf, error
wrapping, and the verb table into one small program.
