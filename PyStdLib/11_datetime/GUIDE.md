# datetime

`datetime` (plus `zoneinfo` and the relevant parts of `time`) is the stdlib's toolkit
for representing points in time, calendar dates, and durations, and for converting
between them and text. It gets calendar arithmetic right (leap years, month lengths,
varying-length months) so you never hand-roll date math.

## When to reach for it

- Any calendar date, wall-clock time, or "how long between these two moments" value →
  `datetime.date` / `datetime.time` / `datetime.datetime` / `datetime.timedelta`.
- Parsing/formatting dates in human or log formats → `strptime`/`strftime`, or
  `datetime.fromisoformat`/`.isoformat()` for ISO 8601 round trips.
- Real-world timezones (with daylight saving rules, historical changes) →
  `zoneinfo.ZoneInfo`, not a hand-written UTC-offset constant. `datetime.timezone.utc`
  is fine for pure-UTC work, but any *named* zone ("Europe/Lisbon") needs `zoneinfo`.
- Measuring elapsed time in running code (benchmarks, timeouts) → `time.monotonic()`,
  never `time.time()` or `datetime.now()`, because wall-clock time can jump backwards
  (NTP sync, manual clock changes) while monotonic time cannot.
- Scheduling, cron-like recurring jobs, or business-day calendars → this repo doesn't
  have a scheduler module; `datetime` gives you the arithmetic primitives, but a real
  recurring-job system needs a persistence layer, which is out of scope here.

`datetime` is not a timer/profiler for code performance — for that, see `time.perf_counter()`
(covered here for elapsed-duration correctness) or `PyEngineering/22_profiling_optimization`
for real profiling tools (`cProfile`, `tracemalloc`).

## Gotchas

| Gotcha | Detail |
|---|---|
| Naive vs aware datetimes don't compare | Comparing a naive `datetime` (no `tzinfo`) to an aware one raises `TypeError: can't compare offset-naive and offset-aware datetimes`. |
| `datetime.utcnow()` is deprecated and still naive | It returns UTC values but with no `tzinfo` attached — easy to accidentally treat as local time. Prefer `datetime.now(timezone.utc)`. |
| Fixed UTC offsets don't capture DST | `timezone(timedelta(hours=1))` never changes; only `zoneinfo.ZoneInfo("Europe/Lisbon")` knows that the offset shifts across DST transitions. |
| Some local times don't exist or exist twice | During a "spring forward" transition, a wall-clock hour is skipped; during "fall back", one hour occurs twice — `zoneinfo` can construct that ambiguous datetime without raising by default, and you must handle it deliberately with `fold`. |
| `time.time()` can jump | NTP corrections or manual clock changes make wall-clock-based elapsed-time measurements wrong (even go negative); `time.monotonic()` cannot go backwards. |
| Month/year arithmetic isn't `timedelta` | `timedelta` only knows days/seconds/microseconds; adding "1 month" requires manual day-count math or a third-party library — `datetime` has no `relativedelta`. |

## What the 10 levels cover

Levels 1-3 build the core objects (`date`, `time`, `datetime`, `timedelta`), their
arithmetic, and `strftime`/`strptime` round trips. Level 4 triggers the real
`TypeError` from comparing naive and aware datetimes. Level 5 introduces
`zoneinfo.ZoneInfo` for genuine IANA timezones. Level 6 *measures*
`time.monotonic()` vs `time.time()` for a short sleep, with real numbers from this
run. Level 7 covers `timedelta.total_seconds()` and safe duration accumulation.
Level 8 combines `zoneinfo` with a real DST-transition edge case (a wall-clock time
that occurs twice, disambiguated with `fold`). Level 9 is a production correctness
trap: naive datetimes silently drifting when mixed with aware ones across a service
boundary, shown breaking and then fixed. Level 10 is a capstone: a small event-log
processor doing timezone-aware parsing, duration calculation, and monotonic timing
together.
