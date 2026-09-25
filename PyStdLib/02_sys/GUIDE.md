# `sys` — the interpreter's own control panel

`sys` exposes the running Python interpreter itself: the arguments it was started
with, its standard streams, where it looks for modules, what it has already imported,
and knobs like the recursion limit. It's not a library you use to *do* things to the
outside world (that's `os`) — it's how your code introspects and controls the process
Python itself is running in.

## When to reach for `sys` vs alternatives already in this repo

- **Parsing real command-line arguments (flags, subcommands, `--help`):** `sys.argv`
  is the raw list; for anything beyond a couple of positional args, reach for
  `argparse` instead of hand-parsing `sys.argv`. This module only covers the raw list.
- **Printing progress / writing to a log:** `sys.stdout`/`sys.stderr` are plain file
  objects — level 3 here covers buffering and `flush()`, but for structured
  application logging use the `logging` module, not raw `sys.stdout.write`.
- **Exiting with a status code:** `sys.exit(code)` is the normal, cooperative way —
  it raises `SystemExit`, which unwinds the stack and flushes output. See
  `PyStdLib/01_os/level_09_exit_and_shell_traps.py` for how `os._exit()` differs
  (immediate, no flush, no cleanup) — that comparison lives there, not here.
- **Deep import-system customization (custom finders/loaders, import hooks):**
  `sys.path`/`sys.modules` (level 4 here) are the surface you'd hook into, but
  building an actual import hook is out of scope for this module — see the
  `importlib` docs if you need that.

## Gotchas

| Gotcha | Detail |
|---|---|
| `sys.exit()` doesn't exit — it raises | `sys.exit(code)` raises `SystemExit(code)`. If something up the call stack has a bare `except:` or `except Exception:` (which does NOT catch `SystemExit`, but a bare `except:` DOES), your "exit" can be silently swallowed and the program keeps running. |
| Piped stdout is buffered; a terminal isn't | When stdout is a TTY, Python line-buffers it (each `\n` flushes). When it's redirected to a file or pipe, it's block-buffered — a `print()` without a trailing flush can sit in memory and never reach the reader until the buffer fills or the process exits normally. `os._exit()` skips even that final flush. |
| `sys.path[0]` is not always the script's directory | When you run `python -m pkg.mod`, `sys.path[0]` is the current working directory, not the package directory — this changes which local modules an accidental same-name import resolves to. |
| `sys.modules` is a cache, not a suggestion | Once a module name is in `sys.modules`, every future `import thatname` returns the SAME cached object without re-running the module body — even if the file on disk changed. Deleting the key and re-importing is how test tools force a reload. |
| `getsizeof()` is shallow | `sys.getsizeof(obj)` reports only the object's own memory, not what it points to — `sys.getsizeof([1, 2, 3])` does not include the ints' own sizes, so it badly undercounts nested containers. |
| String interning is an optimization, not a promise | `sys.intern()` (and CPython's automatic interning of short identifier-like strings) makes equal strings share one object, so `is` can look like it works for string equality — but this is a CPython implementation detail, never a substitute for `==`. |

## What the 10 levels cover

Level 1 is `sys.argv`, the single most common use. Level 2 covers `sys.exit`, the
standard streams, and `sys.platform`/`version_info`. Level 3 combines them into a
buffering-aware <abbr title="Command-Line Interface. A text-based user interface used to view and manage computer files.">CLI</abbr>-style idiom. Level 4 triggers `SystemExit` and inspects
`sys.exc_info()` inside a real `except` block. Level 5 is the import machinery:
`sys.path` resolution order and the `sys.modules` cache. Level 6 measures
`sys.intern()` against ordinary string equality/identity. Level 7 is the recursion
limit: a real `RecursionError` triggered on purpose, then raised and lowered safely.
Level 8 pairs `sys.getsizeof` with `gc.get_referents` to compute a real deep size and
show how badly the shallow number undercounts nested containers. Level 9 is a
correctness trap around catching `SystemExit` with an overly broad `except`. Level 10
is a small capstone <abbr title="Command-Line Interface. A text-based user interface used to view and manage computer files.">CLI</abbr> that parses `argv`, writes buffered progress to `stdout`,
reports errors to `stderr`, and exits with a real status code.
