# regexp — RE2-based regular expressions

`regexp` compiles a pattern into a `*regexp.Regexp` and runs it against
strings/bytes to match, find, or replace. Go's engine is RE2: guaranteed
linear-time in the length of the input, no catastrophic backtracking - at
the cost of not supporting a few PCRE features (backreferences, lookaround).

## When to reach for it vs alternatives already in this repo

- A fixed substring or prefix/suffix check → `strings.Contains` /
  `strings.HasPrefix` / `strings.HasSuffix`. Don't compile a regex for
  `strings.Contains(s, "foo")` - it's slower and less readable.
- Splitting on a single fixed separator → `strings.Split`, not
  `regexp.Split`. Reach for regexp only when the separator is a *pattern*
  (variable whitespace, multiple delimiters).
- A cheap pre-check before an expensive regex → combine both: a
  `strings.Contains` guard before running a real match avoids compiling
  work on inputs that can't possibly match (level 8).
- Structured extraction from free-form text (log lines, IDs embedded in a
  larger string) → `regexp` with named groups is usually clearer than
  manual index/slice arithmetic.
- A pattern that "needs" a backreference or lookaround (matching a repeated
  word, validating "contains X but doesn't start with X") → RE2 cannot do
  it directly; capture broadly and post-filter in Go code (level 9).

## Gotchas

| Gotcha | Detail |
|---|---|
| `MustCompile` panics; `Compile` returns an error | Use `MustCompile` only for patterns fixed in your source code (fail fast at startup). Use `Compile` for any pattern that comes from config, a flag, or user input. |
| Recompiling inside a loop is real, measurable waste | `regexp.MustCompile` parses and builds a state machine every call. Compile once at package scope (or once before a loop) and reuse the `*Regexp` - level 6 has the numbers. |
| No backreferences, no lookaround | RE2 trades these PCRE features for guaranteed linear-time matching. `(\w+)\s+\1` and `(?=...)`/`(?<=...)` fail to compile. Capture broadly and check in Go instead. |
| `Find*` returns `nil`/`""` on no match, not an error | `FindString` returns `""` for "no match" AND for "matched an empty string" - use `FindStringIndex` (returns `nil` on no match) if you must tell them apart. |
| Named groups: unmatched optional groups are `""` in `SubexpNames()` order | `FindStringSubmatch` always returns one slice entry per group, even when that group didn't participate in the match. |
| A `*Regexp` is safe for concurrent use once built | The one-time compile is the expensive, non-thread-safe-to-repeat part; the built value itself can be shared and called from anywhere afterward. |

## What the 10 levels cover

Levels 1-2 cover the everyday surface: `MustCompile` + `MatchString` for a
yes/no check, then `Compile`'s error return, `FindString`, and
`FindAllString`. Level 3 combines named capture groups with
`SubexpNames()` to read matches back by name instead of by index. Level 4
triggers a real `Compile` error from a malformed pattern and handles it,
contrasted with why `MustCompile` at startup is the right call for a
fixed pattern. Level 5 covers `ReplaceAllString` and
`ReplaceAllStringFunc`. Level 6 measures compiling once vs. recompiling
every loop iteration. Level 7 is a design concern: caching compiled
patterns when the pattern itself is dynamic (not known until runtime).
Level 8 is `regexp` + `strings` interop: a cheap `strings.Contains`
pre-filter before an expensive match. Level 9 is RE2's core limitation -
no backreferences/lookaround - shown failing to compile, then fixed with a
capture-and-post-filter idiom. Level 10 is a capstone log-line parser
combining named groups, replacement, and pre-filtering.
