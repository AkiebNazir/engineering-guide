# `logging` — the standard library's logging framework

## What it's for

`logging` gives every Python program (and every third-party library it imports) a shared,
structured way to emit diagnostic messages: severity levels, multiple destinations
(console, files, network), per-destination filtering, and consistent formatting — all
configured independently of the code that actually calls `log.info(...)`. The call sites
never change; only the configuration around them does.

## When to reach for it vs alternatives already in this repo

| Situation | Use |
|---|---|
| A one-off script you run yourself, output read once, thrown away | `print()` is fine |
| Anything that runs unattended, ships to someone else, or needs different verbosity in dev vs prod | `logging` |
| A library/package other code will import (see `PyEngineering`) | `logging.getLogger(__name__)` + `NullHandler` — never `print()`, never call `basicConfig()` |
| Structured JSON logs shipped to a log aggregator | `logging` with a custom `Formatter` (or `logging.config.dictConfig`), not hand-rolled `json.dumps` + `print` |
| Capturing subprocess output for a report | `subprocess` (see `12_subprocess`) — that's not what `logging` is for |

`print()` cannot be turned off selectively, cannot be routed to two places at two
verbosities at once, and carries no level/timestamp/logger-name metadata. `logging` does
all three without touching the call sites — that's the whole reason it exists.

## Gotchas

| Gotcha | Detail |
|---|---|
| "No handlers could be found" / stderr spam | A logger with no handler anywhere in its ancestor chain falls back to `logging.lastResort`, which prints WARNING+ straight to stderr. Libraries must attach a `NullHandler` to opt out. |
| `extra=` key collisions | `extra={"message": ...}` or `extra={"asctime": ...}` raises `KeyError` at log time — those names are already `LogRecord` attributes. Pick names that don't collide. |
| Handlers pile up silently | Calling `getLogger(name)` twice returns the *same* logger object; calling `addHandler` in a function that runs more than once (e.g. in a test loop) duplicates every log line per extra handler. |
| `basicConfig()` is a no-op after the first call | Once the root logger already has a handler, a second `basicConfig()` call does nothing unless `force=True` is passed. |
| `%s` args aren't actually lazy | `logger.debug("%s", expensive())` still calls `expensive()` every time — Python evaluates call arguments before the call happens, regardless of level. Only `logger.isEnabledFor(level)` as an explicit guard skips the work. |
| Propagation duplicates output | A child logger with its own handler *and* propagation still fires ancestor handlers too, so the same line can appear twice unless propagation is deliberately disabled. |

## What the 10 levels cover

Levels 1–3 build the basic mental model: `basicConfig()` for a quick script, why `print()`
stops being enough the moment you need levels or multiple destinations, and the
`getLogger(__name__)` hierarchy with propagation up to the root logger. Level 4 triggers
and catches the real errors logging code runs into. Level 5 assembles a `Logger` +
`Handler` + `Formatter` by hand (no `basicConfig`), including structured fields via
`extra=`. Level 6 measures the real cost difference between lazy and eager message
formatting. Level 7 manages the lifecycle of multiple handlers at different levels on one
logger. Level 8 adds a `RotatingFileHandler` and inspects the rotated files on disk via
`pathlib`. Level 9 demonstrates the classic library-logger gotcha (unwanted stderr output)
and fixes it with `NullHandler` and `propagate = False`. Level 10 is a small capstone
program using most of the above together.
