"""
07 — Filesystem Walker
=======================

WHAT
----
Build a small, testable filesystem-walking toolkit on top of `pathlib.Path`:

    walk_files(root, *, pattern=None, exclude_dirs=None) -> Iterator[Path]
    total_size(root, *, pattern=None) -> int
    find_duplicates(root) -> dict[str, list[Path]]   # keyed by content hash

WHY THIS MATTERS
----------------
Every real service eventually needs to enumerate a tree: log rotation, build
tooling, static-asset bundlers, backup/sync agents, "find every file
referencing X" scripts. The naive approach (`os.walk` string-path juggling)
works, but production code increasingly prefers `pathlib.Path` for its
composability and, since 3.12, `Path.walk()` which mirrors `os.walk()`'s
top-down/bottom-up semantics natively on `Path` objects without falling back
to strings.

The harder engineering problem isn't traversal syntax — it's making tree
code *testable*. Filesystem code is notoriously hard to unit test if it's
written against the real filesystem with hardcoded paths. `pytest`'s
`tmp_path` / `tmp_path_factory` fixtures give every test its own throwaway
directory, so this module is deliberately designed to take `root: Path` as a
parameter everywhere rather than reading from a global/CWD — that single
decision is what makes hermetic, parallel-safe tests possible.

`os.walk` VS `Path.walk` (3.12+)
----------------------------------
- `os.walk(top)` yields `(dirpath: str, dirnames: list[str], filenames:
  list[str])` — you must re-join strings with `os.path.join` yourself.
- `Path.walk(top)` (new in 3.12) yields `(dirpath: Path, dirnames:
  list[str], filenames: list[str])` — same shape, but `dirpath` is already a
  `Path`, so `dirpath / name` composes directly. It also supports
  `top_down=False` and `on_error=` exactly like `os.walk`, and (unlike
  `Path.rglob`) lets you *prune* traversal by mutating `dirnames` in place
  during a top-down walk — `Path.rglob`/`glob` give you no such hook, which
  matters when you need to skip `.git`, `node_modules`, `__pycache__`, etc.
  without descending into them at all (mutating dirnames in-place avoids
  wasted stat() calls compared to walking then filtering results).

SPEC
----
    def walk_files(
        root: Path,
        *,
        pattern: str | None = None,
        exclude_dirs: frozenset[str] = frozenset(),
    ) -> Iterator[Path]:
        "Yield every regular file under root (recursively), pruning any
        directory whose *name* is in exclude_dirs before descending into it.
        If pattern is given, only yield files whose name matches it via
        fnmatch-style globbing (e.g. '*.py')."

    def total_size(root: Path, *, pattern: str | None = None) -> int:
        "Sum st_size over walk_files(root, pattern=pattern). Symlinks to
        files are not followed for sizing (use lstat semantics: a symlink's
        own size, not its target's, OR skip symlinks entirely — document
        your choice)."

    def find_duplicates(root: Path) -> dict[str, list[Path]]:
        "Group files under root by content hash (sha256). Return only groups
        with 2+ members. Must not load entire files into memory at once —
        hash in fixed-size chunks."

ACCEPTANCE CRITERIA
--------------------
- `walk_files` never descends into a directory named in `exclude_dirs`
  (verify by asserting call counts / presence, not just final output — a
  correct implementation should never `stat()` files inside a pruned dir).
- `pattern` filtering matches shell-glob semantics for the filename only
  (not the full path).
- `total_size` returns 0 for an empty directory and matches the sum of
  `os.path.getsize` for a hand-built directory tree with mixed depths.
- `find_duplicates` correctly identifies byte-identical files regardless of
  their filename, and does not report unique files.
- All three functions are exercised with `tmp_path` fixtures — no test
  touches any real, permanent path on disk.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


def walk_files(
    root: Path,
    *,
    pattern: str | None = None,
    exclude_dirs: frozenset[str] = frozenset(),
) -> Iterator[Path]:
    """Yield every regular file under `root`, pruning `exclude_dirs`.

    TODO: Use Path.walk() (3.12+). For each (dirpath, dirnames, filenames):
    - prune dirnames in place (dirnames[:] = [...]) to skip exclude_dirs
      *before* Path.walk descends into them
    - for each filename, optionally filter by pattern (Path.match or
      fnmatch.fnmatch on the name only)
    - yield dirpath / filename
    """
    raise NotImplementedError


def total_size(root: Path, *, pattern: str | None = None) -> int:
    """Sum st_size over walk_files(root, pattern=pattern).

    TODO: decide and document symlink handling, then sum sizes.
    """
    raise NotImplementedError


def find_duplicates(root: Path) -> dict[str, list[Path]]:
    """Group files under root by content hash; return only groups with 2+.

    TODO: hash each file in fixed-size chunks (hashlib.sha256, .update() per
    chunk) to avoid loading whole files into memory, group by hex digest,
    filter to groups of size >= 2.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `for dirpath, dirnames, filenames in root.walk():` — mutate `dirnames[:]`
#   (not `dirnames = ...`) to actually affect traversal; rebinding the name
#   doesn't touch the list `Path.walk` is iterating internally.
# - `Path(name).match(pattern)` matches against the *whole* path by default
#   for absolute patterns; for a filename-only glob use `fnmatch.fnmatch(
#   name, pattern)` or `PurePath(name).match(pattern)` with a relative
#   pattern that has no `/`.
# - Chunked hashing: `for chunk in iter(lambda: f.read(65536), b""): hasher.
#   update(chunk)`.
# - `tmp_path_factory.mktemp(name)` gives a fresh directory per call within
#   a test session, useful when a single test needs multiple independent
#   roots.
#
# Pitfalls
# --------
# - Calling `list(root.rglob("*"))` and filtering `exclude_dirs` afterward
#   still *descends into and stats* every file inside the excluded
#   directory first — defeats the point of exclusion for something like a
#   huge `.git` or `node_modules` tree. Pruning must happen during the walk.
# - Following symlinks by default can create infinite loops on a
#   self-referential symlink; `Path.walk` does not follow directory
#   symlinks unless you pass `follow_symlinks=True` explicitly — know your
#   default.
# - Reading whole files into memory for hashing works in tests with tiny
#   fixtures but silently breaks in production on large files.
#
# Stretch goals
# -------------
# - Add `on_error` propagation for permission-denied directories instead of
#   silently skipping them.
# - Make `walk_files` accept multiple patterns (`Iterable[str]`).
# - Add a `--dry-run` style `plan_prune(root, exclude_dirs)` that reports
#   which directories *would* be skipped, for observability before running
#   a real deletion/archival job over the tree.
