# time — instants, durations, and formatting

`time` is Go's package for everything involving points in time and spans
between them: `time.Now()`, arithmetic with `time.Duration`, formatting and
parsing timestamps, and timers/tickers for "do this later" or "do this
repeatedly". Reach for it any time you touch a timestamp, measure how long
something took, need a deadline, or need to wait without busy-looping.

## When to reach for it vs alternatives already in this repo

- Cancelling work when a deadline passes across goroutines/API boundaries →
  `context.WithTimeout` (out of scope here - already deep-dived in
  GoEngineering topic 32) uses `time.Duration` underneath, but the
  cancellation *tree* is a `context` concern, not a `time` one.
- Coordinating goroutines waiting on each other → `sync` primitives (out of
  scope here - GoEngineering topic 31); `time` only provides "wait until a
  clock condition is true", not general goroutine coordination.
- Formatting a duration for a human log line → `Duration.String()` (e.g.
  `"1h2m3s"`) needs nothing from `fmt` beyond `%v`/`%s`.
- Formatting a specific calendar timestamp → `time.Time.Format` with the
  reference-date layout (level 5) - never hand-build date strings with
  `fmt.Sprintf("%d-%d-%d", ...)`, that skips zero-padding and time zones.

## Gotchas

| Gotcha | Detail |
|---|---|
| Layouts are an example, not `%Y-%m-%d` verbs | Go formats by matching against the literal reference instant `Mon Jan 2 15:04:05 MST 2006` (component values 1-7 in order). Any other string is not a magic format code - it is literal text (level 5). |
| An unstopped `Ticker`/`Timer` leaks | `time.NewTicker` fires forever until `Stop()`; a goroutine that only reads `ticker.C` has no way to exit on its own. Always pair a ticker with a stop signal AND call `Stop()` (level 7). |
| `time.Now()` carries a monotonic reading you can't see in `Format()` | `String()`/`%v` show it as `m=+...`; `Format()` never does. `Sub()`/`Since()` use it when present, which is what makes elapsed-time math immune to wall-clock adjustments (level 9). |
| The monotonic reading disappears silently | `Round`, `Truncate`, `AddDate`, and any Format→Parse (or marshal/unmarshal) round trip strip it with no error. A `time.Time` that still *looks* fine now computes `Sub()` on wall-clock time alone (level 9). |
| `time.Parse` fails on ANY shape mismatch, including extra trailing text | A value with more content than the layout describes is a real `*time.ParseError`, not a partial parse (level 4). |
| Comparing `time.Time` with `==` is usually wrong | Two equal instants can differ in monotonic reading or `Location` pointer and still fail `==`. Use `Equal`, `Before`, or `After` (level 2). |

## What the 10 levels cover

Levels 1-2 build the everyday API: `time.Now()`, `Duration` arithmetic,
`Add`/`Sub`, `Before`/`After`/`Equal`, `time.Date`, and `Since`/`Until`/
`Truncate`/`Round`. Level 3 combines the "stopwatch" timing idiom with
`time.After` inside a `select` as a timeout. Level 4 triggers a real
`*time.ParseError` and inspects it. Level 5 explains and proves the
reference-date layout with Format/Parse round trips. Level 6 is a measured,
honestly-reported comparison of `Format` against a buffer-reusing
`AppendFormat`. Level 7 is the required timer/ticker resource-leak
demonstration, using `runtime.NumGoroutine()` to show leaked goroutines
concretely, then a fix that reclaims them. Level 8 combines `time.Time` with
`os.Stat`'s `ModTime()` to compare file freshness. Level 9 is the production
trap: the monotonic clock reading silently disappears across a
Format/Parse round trip, changing how `Sub()` computes elapsed time even
though nothing about the value looks different. Level 10 is a capstone job
scheduler combining timing, per-job timeouts, and reference-layout log lines.
