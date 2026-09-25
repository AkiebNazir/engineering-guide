# strconv — string/number conversions

`strconv` converts between strings and Go's basic types: integers, floats,
booleans, and Go-syntax quoted string literals. It is the direct, allocation-
aware alternative to routing every conversion through `fmt.Sprintf`/
`fmt.Sscanf`.

## When to reach for it vs alternatives already in this repo

- Parsing a decimal int from user/file input → `strconv.Atoi` (level 1), not
  `fmt.Sscanf(s, "%d", &n)`, which is slower and has its own error shape.
- Parsing with a specific base, bit size, or float precision →
  `strconv.ParseInt`/`ParseFloat`/`ParseBool` (level 2, level 4 for errors),
  not a hand-rolled parser.
- Formatting a number into a byte buffer inside a hot loop →
  `strconv.AppendInt`/`AppendFloat` (level 6), not `fmt.Sprintf` per call -
  `fmt.Sprintf` reflects over its arguments and allocates a new string.
- Safely embedding an arbitrary string in generated Go/JSON-like source, or
  logging one with control characters made visible → `strconv.Quote`/`Unquote`
  (level 5), not manual escaping.
- Building a formatted report string → pair with `strings.Builder` (see
  `../05_strings`) and `strconv.Append*`/`Itoa`, not repeated concatenation.

## Gotchas

| Gotcha | Detail |
|---|---|
| Parse errors are `*strconv.NumError`, not a generic `error` | It carries `Func`, `Num` (the offending input), and `Err` (`strconv.ErrSyntax` or `strconv.ErrRange`) - inspect it with `errors.As`, don't string-match the message (level 4). |
| A range error still returns a USABLE value | `ParseInt("99999999999", 10, 8)` returns `err = ErrRange` AND `v = 127` (the clamped max for that bit size) - not zero. Ignoring the error silently gives a plausible-looking wrong number (level 9). |
| `Atoi` is exactly `ParseInt(s, 10, 0)` | `Atoi` is a convenience wrapper - it's not a different algorithm, just base 10 with the platform int's bit size. |
| `FormatInt`/`AppendInt` never add a base prefix | `FormatInt(255, 16)` gives `"ff"`, not `"0xff"` - if you want the prefix, add it yourself or parse with `ParseInt(s, 0, ...)` which DOES understand `0x`/`0o`/`0b` prefixes on the way in. |
| `Quote` output is Go-syntax, not JSON | It's close to JSON string syntax but not guaranteed identical (e.g. non-ASCII handling); don't use it as a JSON encoder. |

## What the 10 levels cover

Level 1 is `Atoi`/`Itoa`, the single most common conversion. Level 2 is the
core <abbr title="Application Programming Interface">API</abbr> surface: `ParseInt`/`ParseFloat`/`ParseBool` and their `Format*`
counterparts. Level 3 combines `FormatInt`/`ParseInt` with different bases
into a small prefixed-number idiom (`0x`, `0o`, `0b`). Level 4 triggers a real
`*strconv.NumError` and inspects its fields. Level 5 round-trips a string with
special characters through `Quote`/`Unquote`. Level 6 measures `AppendInt`
into a growing `[]byte` against `fmt.Sprintf` in a hot loop. Level 7 is a
second intermediate pattern: reusing one `[]byte` buffer across iterations
with `Append*` instead of allocating a new one each time. Level 8 interops
with `strings.Builder` to build a formatted report. Level 9 demonstrates the
range-error-still-returns-a-value trap and fixes it by checking the error.
Level 10 is a capstone config-line parser exercising most of the above
together.
