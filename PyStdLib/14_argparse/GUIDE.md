# `argparse` — command-line argument parsing

## What it's for

`argparse` turns a list of strings (`sys.argv[1:]`) into a validated, typed namespace of
values, and generates `--help` / usage text and error messages for free. It is the
standard library's answer to "parse the command line" — positional args, optional flags,
type coercion, subcommands, and mutually exclusive options are all built in.

## When to reach for it vs alternatives already in this repo

| Situation | Use |
|---|---|
| A script with a handful of flags, run by a human from a terminal | `argparse` |
| Config that comes from environment variables or a TOML file | plain `os.environ` / `tomllib` (see `PyEngineering/08_config_loader`), not `argparse` |
| A REST-style HTTP <abbr title="Application Programming Interface">API</abbr>'s request parameters | `urllib.parse` / the web framework's own parsing (see `API/`), not `argparse` |
| A git-style tool with subcommands (`tool add`, `tool remove`) | `argparse` with `add_subparsers()` |
| Extremely simple one-flag scripts where importing argparse feels heavy | manual `sys.argv` slicing is acceptable, but you lose `--help`, type errors, and usage text for free |

## Gotchas

| Gotcha | Detail |
|---|---|
| Errors call `sys.exit()` | A bad argument doesn't raise a catchable Python exception by default — `parser.error()` prints usage + message to stderr and raises `SystemExit(2)`. Tests must catch `SystemExit`, not `ValueError`. |
| `type=` exceptions must be `ValueError` or `TypeError` (or `ArgumentTypeError`) | Any other exception raised by a `type=` callable propagates as an ugly, unhandled traceback instead of a clean argparse error. |
| Mutable defaults for `nargs` | `default=[]` shared across parser instances is a lesser risk than the mutable-default-arg trap, but `nargs='*'`/`'+'` results are always fresh lists per parse — the trap is elsewhere: forgetting `nargs` means only *one* value is ever accepted even if the user passes several. |
| `store_true`/`store_false` need `default=` awareness | Omitting neither is fine (defaults to `False`/`True`), but combining `action='store_true'` with an explicit conflicting `default=` silently changes what "not passing the flag" means. |
| A lambda as `type=` gives a useless error message | `type=lambda s: s.upper()` that fails produces `invalid <lambda> value: '...'` — a custom function or `Action` subclass gives a message users can actually act on. |
| Subparsers are required by default only if you say so | `add_subparsers(required=True)` (Python 3.7+) — otherwise omitting the subcommand silently leaves `args.command` as `None` instead of erroring. |

## What the 10 levels cover

Levels 1–3 build up the basic surface: positional and optional arguments, then `type=` /
`default=` / `choices=` together, then `nargs` (`'+'`, `'*'`, `'?'`) in a realistic
multi-value example. Level 4 triggers argparse's real errors (`SystemExit`, bad `type=`
coercion) and catches them properly. Level 5 builds a git-style CLI with
`add_subparsers()`. Level 6 measures argparse's parsing overhead against a hand-rolled
parser with real timings. Level 7 organizes a larger CLI's `--help` with
`argument_group()` and enforces exclusivity with `mutually_exclusive_group()`. Level 8
captures the auto-generated `--help` text programmatically via `io`/`contextlib`. Level 9
shows the real gotcha of a bad `type=` error message and fixes it with a custom `Action`
subclass. Level 10 is a small capstone CLI combining subcommands, groups, and a custom
action.
