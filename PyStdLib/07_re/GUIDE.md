# `re` — Regular Expressions

## What it's for

`re` finds, validates, and rewrites text against a *pattern* instead of literal
characters: "a digit followed by three letters" rather than `"1abc"` exactly. It is
the standard library's answer to matching, extracting groups out of, and
transforming strings that follow a shape rather than a fixed value.

## When to reach for it vs alternatives already in this repo

- **Fixed substring** ("does this contain `'error'`?") → plain `str.find`/`in`, not
  `re`. A regex engine is overkill and slower for a literal match.
- **Structured, well-known formats** (<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, URLs, dates) → use the dedicated parser
  (`json`, `urllib.parse`, `datetime.strptime`) instead of hand-rolling a regex —
  see `API/REST/labs/python/01_crud_stdlib.py` for `json` doing exactly this job.
  Regexes for things like validating emails or URLs are notoriously incomplete.
- **Splitting/joining on a single fixed delimiter** → `str.split`/`str.join` are
  simpler and faster than `re.split` when the delimiter isn't itself a pattern.
- **Reach for `re`** when the shape varies: log lines, loosely structured user
  input, extracting tokens embedded in free text, or bulk find-and-replace with a
  rule instead of a literal.

## Gotchas

| Gotcha | Detail |
|---|---|
| `match`/`search` only anchor at the start (or nowhere) | `re.match` succeeds on a *prefix*; trailing garbage after a valid-looking prefix is silently ignored unless you anchor with `$` or use `fullmatch`. |
| `.group()` on a failed match | `re.search(...)` returns `None` on no match; calling `.group()` on `None` raises `AttributeError`, not a regex-specific error. |
| Greedy quantifiers grab too much | `<.*>` against `<a><b>` matches the whole string, not `<a>`; use `.*?` (non-greedy) or a character class to stop early. |
| `groupby`-style ordering assumptions don't apply here, but *nested quantifiers* do | Patterns like `(a+)+c` can backtrack exponentially on strings that almost-but-don't match — "catastrophic backtracking". |
| `re.split` with capturing groups | The captured separators are *kept* in the result list, which is easy to forget and shows up as unexpected extra list items. |
| Recompiling the same pattern in a hot loop | `re.compile()` once and reuse the object; the module-level `re.search(pattern, ...)` convenience functions cache a small number of compiled patterns internally, but that cache is not something to depend on for a tight loop. |

## What the 10 levels cover

Level 1 starts with the single most common job — finding a pattern in text with
`re.search`. Level 2 covers the core surface: `match` vs `search` vs `fullmatch`,
and pulling data out with `groups()`/named `groupdict()`. Level 3 builds a small
idiom combining `findall`/`finditer`, `sub` with a replacement function, and
`re.split` keeping capturing groups. Level 4 triggers the real exceptions
(`re.error`, `AttributeError` on a failed match) instead of describing them.
Level 5 covers flags (`IGNORECASE`, `MULTILINE`, `DOTALL`, `VERBOSE`). Level 6 is a
measured catastrophic-backtracking demo — a pathological pattern timed against a
fixed one on the same bounded input. Level 7 covers greedy vs non-greedy
quantifiers and lookahead/negative lookahead. Level 8 pairs `re` with
`collections.Counter` for word-frequency interop. Level 9 demonstrates the
prefix-match trap (validation that silently accepts garbage) and its fix. Level 10
is a capstone log parser combining compiled named-group patterns, flags, `sub`,
and error handling.
