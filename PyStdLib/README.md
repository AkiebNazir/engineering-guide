# Python Standard Library — Basic to Advanced, Level by Level

This is not a DSA/algorithm curriculum (see `../PyDSA` for that) and it is not the
production-systems curriculum (see `../PyEngineering`, which assumes competence and
teaches whole services). **PyStdLib teaches the standard library itself, one package at a
time**, starting from real basics — this is the one module in the repo where beginner
explanations belong. Each package ramps from "the single most common call" (level 1) to
a small realistic program exercising most of the package's important corners (level 10).

100% standard library. No pip installs anywhere in this module — that's deliberate: the
point is mastering what ships with Python itself.

## Layout

```
PyStdLib/
  NN_libname/
    GUIDE.md              concept guide: what it's for, gotchas table, level overview
    level_01_<slug>.py     ...through...
    level_10_<slug>.py     10 standalone, independently runnable files
```

Every level file is self-contained — no imports between level files, no network access,
no fixed ports, own temp files under `tempfile.mkdtemp()` when it needs the filesystem.
Every file proves its lesson with real `assert` statements at runtime (this repo's
standing quality bar — see `../CONTEXT.md` §5) and ends with `print("OK")`.

## The level shape (adapted per library, kept consistent across all 15)

| Level | What it teaches |
|---|---|
| 1 | The single most common use — one function/class, minimal example |
| 2 | The core <abbr title="Application Programming Interface">API</abbr> surface — what covers 90% of real usage |
| 3 | Combining basics into a small realistic idiom |
| 4 | Error handling — the real exception types, triggered for real |
| 5 | An intermediate pattern specific to the library |
| 6 | A **measured** comparison — two approaches, actually timed, numbers from that run |
| 7 | A resource-management / lifecycle concern |
| 8 | Interop with another stdlib package |
| 9 | A production gotcha or correctness trap — shown failing, then fixed |
| 10 | A capstone — a small realistic program tying the level together |

Level 6 (and any other measured level) reports the number it actually got on that run,
even when it contradicts intuition — several libraries below turned up genuine surprises
this way (see each `GUIDE.md`'s gotchas table).

## Curriculum

| # | Package | Levels 1-10 cover |
|---|---|---|
| 01 | `os` | environ, cwd/listdir/scandir, stat, mkdir/remove/rename, `os.walk`, low-level fd read/write, chmod, `os.system` vs `subprocess`, exit codes |
| 02 | `sys` | argv, exit/`SystemExit`, stdio streams, `sys.path`/`sys.modules`, `getsizeof`, recursion limit, `exc_info`, `intern` |
| 03 | `pathlib` | `Path` construction, `/` joining, glob/rglob, read/write helpers, mkdir/unlink, vs `os.path` side by side |
| 04 | `io` | open() modes, `StringIO`/`BytesIO`, encoding/errors handling, seek/tell, subclassing a custom stream |
| 05 | `json` | dumps/loads, `default=`/`object_hook`, `JSONDecodeError`, atomic config writes, duplicate-key and NaN gotchas |
| 06 | `csv` | reader/writer, `DictReader`/`DictWriter`, dialects/quoting, `Sniffer`, streaming, the `newline=''` trap |
| 07 | `re` | match/search/fullmatch, named groups, findall/finditer, flags, greedy vs lazy, catastrophic backtracking |
| 08 | `collections` | `deque`, `Counter`, `defaultdict`, `namedtuple`, `OrderedDict` vs dict, `ChainMap` |
| 09 | `itertools` | chain, islice, groupby (sorted-input gotcha), product/permutations/combinations, accumulate, tee |
| 10 | `functools` | reduce, partial, `lru_cache`/`cache`, `wraps`, `singledispatch`, `total_ordering` |
| 11 | `datetime` | construction/arithmetic, strftime/strptime, naive vs aware, `zoneinfo`/DST, monotonic vs wall clock |
| 12 | `subprocess` | `run()`/`Popen`, `CalledProcessError`, streaming, timeouts, the `shell=True` injection trap |
| 13 | `logging` | why not `print()`, Logger/Handler/Formatter, hierarchy/propagation, `RotatingFileHandler`, structured `extra=` |
| 14 | `argparse` | positional/optional args, types/choices/nargs, subcommands, mutually exclusive groups, custom actions |
| 15 | `contextlib` | `@contextmanager`, `ExitStack`, `suppress`, `closing`, `redirect_stdout`, vs a hand-written class |

Deliberately **not** duplicated here because `../PyEngineering` already deep-dives them:
`asyncio`/threading (27, 33, 34), `typing`/`dataclasses` (32, 35), full `sqlite3` database
work (09-11), and pytest-based testing patterns (20-21). Networking is covered
hands-on in `../API`.

## Workflow

1. Read `NN_libname/GUIDE.md` first — the concepts and gotchas table.
2. Run `level_01` through `level_10` in order: `.venv/bin/python PyStdLib/NN_libname/level_0X_*.py`.
3. Read the file's docstring header, then the code, then re-run it — every file is short
   enough to read top to bottom in a few minutes.

The Go-parallel curriculum lives in `../GoStdLib`.
