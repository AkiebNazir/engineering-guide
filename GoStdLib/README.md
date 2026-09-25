# Go Standard Library — Basic to Advanced, Level by Level

This is not a DSA/algorithm curriculum (see `../GoDSA` for that) and it is not the
production-systems curriculum (see `../GoEngineering`, which assumes competence and
teaches whole services). **GoStdLib teaches the standard library itself, one package at a
time**, starting from real basics — this is the one module in the repo where beginner
explanations belong. Each package ramps from "the single most common call" (level 1) to
a small realistic program exercising most of the package's important corners (level 10).

## Layout

```
GoStdLib/
  go.mod                          single module — every level is its own subpackage
  NN_libname/
    GUIDE.md                      concept guide: what it's for, gotchas table, level overview
    level_01_<slug>/main.go       ...through...
    level_10_<slug>/main.go       10 independent `package main` programs
```

Ten separate directories instead of ten files in one package, for the same reason
`../GoEngineering` splits explanation/solution: Go compiles per-package, and ten
`func main()`s can't share one. Every level is `go run`-able on its own, self-contained
(temp files via `os.MkdirTemp`, no network, no fixed ports), proves its lesson with real
runtime checks that `panic` on mismatch (not just print-and-hope), and ends with
`fmt.Println("OK")`.

## The level shape (adapted per library, kept consistent across all 15)

| Level | What it teaches |
|---|---|
| 1 | The single most common use — one function/type, minimal example |
| 2 | The core <abbr title="Application Programming Interface">API</abbr> surface — what covers 90% of real usage |
| 3 | Combining basics into a small realistic idiom |
| 4 | Error handling — the real error values/types, triggered for real |
| 5 | An intermediate pattern specific to the package |
| 6 | A **measured** comparison — two approaches, actually timed with `time.Since`, numbers from that run |
| 7 | A resource-management / lifecycle concern |
| 8 | Interop with another stdlib package |
| 9 | A production gotcha or correctness trap — shown failing, then fixed |
| 10 | A capstone — a small realistic program tying the level together |

Level 6 (and any other measured level) reports the number it actually got on that run —
several packages below turned up genuine, sometimes counter-intuitive results this way
(see each `GUIDE.md`'s gotchas table).

## Curriculum

| # | Package | Levels 1-10 cover |
|---|---|---|
| 01 | `os` | ReadFile/WriteFile/OpenFile, Getenv/env, Stat + `fs.ErrNotExist`, Mkdir/RemoveAll, `os.Exit` skipping defers, `os.Pipe`, permissions/umask |
| 02 | `fmt` | Printf verb table, Sprintf/Fprintf, Scan family, `%w` error wrapping, `Stringer`, custom `Formatter` |
| 03 | `io` | Reader/Writer/Closer, `io.Copy`/`ReadAll`, `io.Pipe`, MultiWriter/TeeReader/LimitReader, the `io.EOF` idiom |
| 04 | `bufio` | `Scanner` + the 64KB token limit, custom `SplitFunc`, buffered vs unbuffered throughput, the missing-`Flush` trap |
| 05 | `strings` | `Builder` vs `+=`, Split/Join/Fields, Trim family, `strings.Reader`, `NewReplacer` |
| 06 | `strconv` | Atoi/Itoa, ParseInt/ParseFloat with `*NumError`, FormatInt bases, Quote/Unquote, `AppendInt` |
| 07 | `bytes` | `bytes.Buffer`, Compare/Contains/Split/Join, `bytes.NewReader`, the `[]byte`↔`string` conversion cost |
| 08 | `path/filepath` | Join/Clean/Abs/Base/Dir/Ext, `WalkDir`+`fs.SkipDir`, Glob/Rel/Match, `filepath` vs `path` |
| 09 | `encoding/json` | Marshal/Unmarshal + struct tags, custom (Un)MarshalJSON, streaming `Decoder`, the `any`-decodes-to-float64 trap |
| 10 | `encoding/csv` | Reader/Writer, `FieldsPerRecord`, `LazyQuotes`, streaming, the missing-`Flush` trap |
| 11 | `time` | Duration arithmetic, the reference-date layout, timers/tickers and the Stop()-leak, monotonic vs wall clock |
| 12 | `sort` | `sort.Slice`/`SliceStable`, `sort.Interface`, `sort.Search`, the stability trap |
| 13 | `errors` | `errors.New` vs `%w`, `Is`/`As` through wrap chains, custom error types, `errors.Join` |
| 14 | `regexp` | Compile vs MustCompile, named groups, ReplaceAll, compile-once-reuse, the RE2-vs-PCRE limitation |
| 15 | `slices` (Go 1.21+) | Sort/SortFunc, Contains/Index, Clone (the aliasing bug without it), Compact, Insert/Delete, BinarySearch |

Deliberately **not** duplicated here because `../GoEngineering` (topics 26-35) already
deep-dives them: `context` internals, `sync` primitives/deadlocks, `reflect`, `unsafe`/cgo,
and custom network dialers.

## Workflow

1. Read `NN_libname/GUIDE.md` first — the concepts and gotchas table.
2. Run `level_01` through `level_10` in order: `go run ./GoStdLib/NN_libname/level_0X_*`.
3. Read the file's header comment, then the code, then re-run it — every file is short
   enough to read top to bottom in a few minutes.

The Python-parallel curriculum lives in `../PyStdLib`.
