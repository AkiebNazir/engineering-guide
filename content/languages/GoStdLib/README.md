# Go Standard Library — Basic to Advanced, Level by Level

This is not a DSA/algorithm curriculum (see `../GoDSA` for that) and it is not the
production-systems curriculum (see `../GoEngineering`, which assumes competence and
teaches whole services). **GoStdLib teaches the standard library itself, one package at a
time**, starting from real basics — this is the one module in the repo where beginner
explanations belong. Each package ramps from "the single most common call" (level 1) to
a small realistic program exercising most of the package's important corners (level 10).

## Layout

```
content/languages/GoStdLib/
  go.mod                          single module — every level is its own subpackage
  NN_libname/
    GUIDE.md                      concept guide: what it's for, gotchas table, level overview
    level_01_<slug>/main.go       ...through...
    level_10_<slug>/main.go       10 independent `package main` programs
```

Ten separate directories instead of ten files in one package, for the same reason
`../GoEngineering` splits explanation/solution: Go compiles per-package, and ten
`func main()`s can't share one. Every level is `go run`-able on its own, self-contained
(temp files via `os.MkdirTemp`, no outside network, no fixed ports: `net/http` levels
listen on a free 127.0.0.1 port the OS picks), proves its lesson with real
runtime checks that `panic` on mismatch (not just print-and-hope), and ends with
`fmt.Println("OK")`.

## The level shape (adapted per library, kept consistent across all 16)

| Level | What it teaches |
|---|---|
| 1 | The single most common use — one function/type, minimal example |
| 2 | The core API surface — what covers 90% of real usage |
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
| 16 | `net/http` | Handlers + `httptest`, Go 1.22 `ServeMux` patterns, client requests with context, telling client errors apart, middleware, connection reuse and `MaxIdleConnsPerHost` measured, server timeouts + graceful shutdown, strict JSON bodies, the `DefaultClient`-has-no-timeout trap |

Deliberately **not** duplicated here because `../GoEngineering` (topics 26-35) already
deep-dives them: `context` internals, `sync` primitives/deadlocks, `reflect`, `unsafe`/cgo,
and custom network dialers (`net`, raw TCP). `net/http` itself is package 16 here; REST API
design and HTTP as a protocol are in `../API`.

## Related design chapters

The packages teach the mechanics; these `../SoftwareDesign` chapters cover the design
decisions around them:

| Package(s) here | Design chapter |
|---|---|
| `errors`, `fmt` (`%w`), `os` (`os.Exit` skipping defers) | [Error Handling and Failure Design in Code](../../interview-core/SoftwareDesign/06_error_handling_and_failure_design.md): sentinel vs typed errors, wrapping, where to handle failure |
| `time` (tickers, timers), `net/http` (timeouts, shutdown) | [Designing Concurrent Code](../../interview-core/SoftwareDesign/07_designing_concurrent_code.md): goroutine lifecycles, cancellation, leaks |
| `encoding/json`, `encoding/csv` | [Data Design and Schema Evolution in Code](../../interview-core/SoftwareDesign/09_data_design_and_schema_evolution.md): evolving the shape of stored and exchanged data |
| `regexp` (RE2), `net/http` (body limits, slowloris) | [Secure Code by Design](../../interview-core/SoftwareDesign/12_secure_code_by_design.md): untrusted input and resource exhaustion |
| `io` (small interfaces), `net/http` (`Handler`, middleware) | [Modularity, Coupling, and Code-Level API Design](../../interview-core/SoftwareDesign/03_modularity_coupling_and_api_design.md): small interfaces and composition |
| the measured levels (level 6 of each package) | [Performance-Aware Design](../../interview-core/SoftwareDesign/11_performance_aware_design.md): measuring before optimizing |

## Workflow

1. Read `NN_libname/GUIDE.md` first — the concepts and gotchas table.
2. Run `level_01` through `level_10` in order: `cd content/languages/GoStdLib && go run ./NN_libname/level_0X_*` (from the repo root).
3. Read the file's header comment, then the code, then re-run it — every file is short
   enough to read top to bottom in a few minutes.

The Python-parallel curriculum lives in `../PyStdLib`.
