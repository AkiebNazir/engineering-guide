"""
07 — Filesystem Walker — Reference Solution
==============================================

See `07_filesystem_walker_explanation.py` for the full spec and rationale.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from fnmatch import fnmatch
from pathlib import Path

_CHUNK_SIZE = 65536


def walk_files(
    root: Path,
    *,
    pattern: str | None = None,
    exclude_dirs: frozenset[str] = frozenset(),
) -> Iterator[Path]:
    """Yield every regular file under `root`, pruning `exclude_dirs`.

    `Path.walk()` (3.12+) yields (dirpath, dirnames, filenames) top-down by
    default. Mutating `dirnames` *in place* before the loop body finishes is
    what actually prunes traversal — Path.walk reads the same list object on
    its next step, so removing names from it stops descent into those
    subdirectories entirely (no wasted stat() calls inside excluded trees).
    """
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            if pattern is not None and not fnmatch(name, pattern):
                continue
            yield dirpath / name


def total_size(root: Path, *, pattern: str | None = None) -> int:
    """Sum st_size over walk_files(root, pattern=pattern).

    Symlinks are skipped entirely (not followed, not counted) — this avoids
    double-counting a target file reachable both directly and via a link,
    and avoids surprising size numbers when a symlink target lives outside
    root. A production variant might instead choose to always report the
    symlink's own (typically tiny) inode size via lstat; document whichever
    choice you make.
    """
    total = 0
    for path in walk_files(root, pattern=pattern):
        if path.is_symlink():
            continue
        total += path.stat().st_size
    return total


def find_duplicates(root: Path) -> dict[str, list[Path]]:
    """Group files under root by content hash; return only groups with 2+.

    Hashing in fixed-size chunks keeps memory use O(chunk_size) regardless
    of file size, unlike `path.read_bytes()` which loads the whole file.
    """
    by_hash: dict[str, list[Path]] = {}
    for path in walk_files(root):
        if path.is_symlink():
            continue
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
                hasher.update(chunk)
        by_hash.setdefault(hasher.hexdigest(), []).append(path)

    return {digest: paths for digest, paths in by_hash.items() if len(paths) >= 2}


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Prune directories during the walk (mutate dirnames in place), never
#   after collecting a full listing — the whole point of exclusion is to
#   avoid the cost of descending, not just to hide results.
# - Take `root: Path` as an explicit parameter everywhere instead of reading
#   CWD or a module-global — this is what makes `tmp_path`-based testing
#   possible without monkeypatching the filesystem.
# - Chunked I/O for hashing/checksumming — O(1) memory regardless of file
#   size, the same principle as problem 05's line processor.
# - Be explicit and intentional about symlink handling; "whatever the stdlib
#   defaults to" is not a documented design decision.
#
# Alternative approaches
# -----------------------
# - `os.walk` + `os.path.join` works identically but loses the ergonomic
#   `Path` composition and forces string plumbing throughout.
# - `Path.rglob("*")` is simpler for "give me everything" but offers no
#   pruning hook — you'd filter *after* a full recursive stat pass, which
#   is wasted work (and wasted permission errors) inside excluded trees.
# - For very large trees, `find_duplicates` could first group by
#   `st_size` (cheap) and only hash within same-size groups, avoiding full
#   hashing of files that can't possibly match — a real-world optimization
#   left as a stretch goal.
