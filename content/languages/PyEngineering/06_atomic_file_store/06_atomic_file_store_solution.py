"""
06 — Atomic File Store — Reference Solution
=============================================

See `06_atomic_file_store_explanation.py` for the full spec, rationale, and
acceptance criteria. This module implements `AtomicFileStore` exactly as
specified there: temp-file-in-same-dir + fsync + `os.replace`.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path


class AtomicFileStore:
    """A directory-backed key/value store with crash-safe atomic writes."""

    def __init__(self, root: Path, *, file_mode: int = 0o644) -> None:
        # Resolve to an absolute, symlink-free path up front so every later
        # containment check (`is_relative_to`) compares like-for-like paths.
        # mkdir(parents=True, exist_ok=True) makes the store usable even if
        # the caller hands us a root that doesn't exist yet.
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.file_mode = file_mode

    def _resolve(self, key: str) -> Path:
        """Validate `key` and return the absolute path it maps to.

        Rejects empty keys, absolute paths, and any key whose resolved path
        would land outside `self.root` (path traversal via `..` or a symlink
        hop). Validation happens *before* any filesystem write is attempted.
        """
        if not key:
            raise ValueError("key must not be empty")
        if Path(key).is_absolute():
            raise ValueError(f"key must be relative, got absolute path: {key!r}")

        candidate = (self.root / key).resolve()
        # is_relative_to() correctly rejects "../escape" and "a/../../b"
        # style traversal because .resolve() collapses the ".." components
        # before this check runs.
        if not candidate.is_relative_to(self.root):
            raise ValueError(f"key escapes store root: {key!r}")
        return candidate

    def write_bytes(self, key: str, data: bytes) -> None:
        """Atomically create-or-replace the file for `key` with `data`.

        Sequence: validate -> mkstemp in the *same directory* as the target
        -> write + fsync the temp file's data -> chmod -> os.replace (atomic
        rename) -> fsync the containing directory (so the rename survives a
        crash, not just the data). Any exception before the rename cleans up
        the temp file and leaves the target untouched.
        """
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)

        # dir=target.parent is the load-bearing part: it guarantees the temp
        # file and the target share a filesystem, which is what makes the
        # final os.replace() a single atomic rename instead of a cross-device
        # copy+delete (or an outright OSError).
        fd, tmp_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                # fsync the *data* before the rename — without this, a crash
                # between close() and replace() can leave the post-crash
                # file pointing at content that never left the page cache.
                os.fsync(f.fileno())

            # mkstemp() creates the file mode 0600 regardless of umask (it's
            # deliberately restrictive since it may hold sensitive staging
            # data) — chmod explicitly to get the caller's requested mode.
            os.chmod(tmp_path, self.file_mode)

            # Atomic on POSIX (rename(2)) and on Windows too (unlike
            # os.rename, which raises there if the destination exists).
            os.replace(tmp_path, target)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                tmp_path.unlink()
            raise
        else:
            # fsync the directory entry itself so the rename is durable, not
            # just the file's bytes. Skipped on platforms without a
            # directory-fd-fsync story (e.g. Windows raises here).
            self._fsync_dir(target.parent)

    @staticmethod
    def _fsync_dir(dir_path: Path) -> None:
        with contextlib.suppress(OSError):
            dir_fd = os.open(dir_path, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

    def write_text(self, key: str, text: str, *, encoding: str = "utf-8") -> None:
        """Same as write_bytes but for str content."""
        self.write_bytes(key, text.encode(encoding))

    def read_bytes(self, key: str) -> bytes:
        """Read and return the file contents for `key`."""
        return self._resolve(key).read_bytes()

    def read_text(self, key: str, *, encoding: str = "utf-8") -> str:
        """Read and decode the file contents for `key`."""
        return self.read_bytes(key).decode(encoding)

    def delete(self, key: str) -> None:
        """Remove the file for `key`. Missing key raises FileNotFoundError."""
        self._resolve(key).unlink()

    def exists(self, key: str) -> bool:
        """Return whether a file exists for `key`."""
        return self._resolve(key).exists()


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Validate untrusted input (the key) *before* touching the filesystem —
#   fail closed, not after a partial side effect.
# - `os.replace` over `shutil.move`/`os.rename` for atomic same-filesystem
#   overwrite semantics on both POSIX and Windows.
# - fsync data before the rename, fsync the directory after — durability has
#   two independent gaps (data-to-disk, and rename-to-disk) and skipping
#   either one reopens a crash-consistency hole.
# - `contextlib.suppress` for best-effort cleanup that must not mask the
#   original exception (note the `except BaseException: ... ; raise` — we
#   clean up and then re-raise the real error, not the cleanup's).
#
# Alternative approaches
# -----------------------
# - `pathlib.Path` has no native atomic-write API; a small wrapper like this
#   one (or the third-party `atomicwrites` package) is the idiomatic fix.
# - For multi-file atomicity, write a manifest file atomically and have
#   readers resolve indirection through it (a poor man's MVCC), or reach for
#   an embedded transactional store (sqlite3, LMDB) — see problems 09/10.
# - `os.O_TMPFILE` (Linux-only) can create the temp file with no name at all
#   until linked via `/proc/self/fd/N`, avoiding any temp-name collision risk
#   entirely, at the cost of portability.
