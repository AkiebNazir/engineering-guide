"""
06 — Atomic File Store
=======================

WHAT
----
Build `AtomicFileStore`, a small on-disk key/value store where every write is
*atomic from the reader's point of view*: a concurrent reader (or a crash)
must never observe a partially-written file. Callers get either the old
content or the fully-written new content — never a truncated or torn mix of
both.

WHY THIS MATTERS
----------------
`open(path, "w")` truncates the file *before* your first byte is written.
Anyone who opens that path between your `open()` and your final `close()`
sees a zero-length or half-written file. A crash (power loss, OOM-killer,
`kill -9`, the containerd sidecar getting rescheduled mid-deploy) at that
moment leaves the file corrupted *on disk*, not just in a buffer — there is
no "undo" on restart.

This is not a hypothetical: config files, checkpoint files, on-disk caches,
lock/state files for daemons, and single-file "poor man's databases" all rely
on this pattern in real systems. `sqlite3` itself uses a close cousin of it
(WAL / rollback journal) for the same reason problem 09/10 need transactions
at all: torn writes are unacceptable.

THE CORE TRICK
---------------
1. Write the *new* content to a temporary file **in the same directory** as
   the target (same filesystem/mount — required, see PITFALLS).
2. `flush()` + `os.fsync(tmp_fd)` the temp file's contents to durable
   storage — without this, `os.replace` durably renames a file whose
   *contents* may still only exist in the OS page cache.
3. `os.replace(tmp_path, target_path)` — on POSIX this is `rename(2)`, which
   is guaranteed atomic: any concurrent `open()` on `target_path` either
   sees the fully-old file or the fully-new file, never a mix, because a
   directory-entry swap is a single filesystem operation. `os.replace` is
   also atomic on Windows (unlike `os.rename`, which raises if the
   destination exists there) — that's precisely why the stdlib docs
   recommend `os.replace` over `shutil.move` (which may fall back to a
   non-atomic copy+delete across filesystems) or `os.rename` (platform-
   dependent overwrite semantics) for this use case.
4. (Optional but recommended for "survive a real crash, not just a
   process crash") `os.fsync` the *directory* file descriptor after the
   rename, so the rename itself is durable and not just the file's data.

WHAT ATOMIC RENAME DOES **NOT** GIVE YOU
-----------------------------------------
- It does not make multi-file updates atomic (only a single rename is
  atomic; if you need N files to change together, that's a mini-transaction
  problem — write a manifest file atomically instead, or see problem 10).
- It does not survive the temp file and target being on different
  filesystems/mounts (`os.replace` across devices raises `OSError` — this is
  why the temp file MUST be created in the same directory as the target).
- It does not remove the *durability* gap between "data written" and "fsync
  called" — you must fsync the temp file's data before the rename, or a
  crash between `close()` and the rename can still leave the *new* file
  (post-crash) with zero bytes because the rename itself is fine but the
  data it points to was never flushed from cache to disk.

SPEC
----
Implement `AtomicFileStore`:

    class AtomicFileStore:
        def __init__(self, root: Path, *, file_mode: int = 0o644) -> None: ...

        def write_bytes(self, key: str, data: bytes) -> None:
            "Atomically create-or-replace `root/key` with `data`."

        def write_text(self, key: str, text: str, *, encoding: str = "utf-8") -> None:
            "Same as write_bytes but for str content."

        def read_bytes(self, key: str) -> bytes: ...
        def read_text(self, key: str, *, encoding: str = "utf-8") -> str: ...

        def delete(self, key: str) -> None:
            "Remove the file for `key`. Missing key -> FileNotFoundError."

        def exists(self, key: str) -> bool: ...

Rules the implementation must satisfy:

- `key` must not escape `root` (no `..`, no absolute paths, no symlink
  traversal out of `root`) — validate and raise `ValueError` on a bad key.
  This is the same class of bug as a path-traversal vulnerability in a web
  upload handler; a "local file store" often becomes exactly that handler.
- The temp file used for staging must live in the *same directory* as the
  target file (use `tempfile.mkstemp(dir=root, ...)` or equivalent) — never
  `tempfile.gettempdir()` — otherwise the final `os.replace` can silently
  become non-atomic (cross-device) or outright fail.
- On any exception during the write (encode error, disk full, etc.) the temp
  file must be cleaned up — the target file must be left untouched.
- `file_mode` should be applied to the final file (accounting for the
  process `umask`, which `mkstemp` applies restrictively by default — note
  in your solution's comments what `mkstemp`'s default mode is and why you
  must `os.chmod` explicitly if you want anything looser).
- Must work correctly if called from multiple threads/processes targeting
  *different* keys concurrently (no shared mutable state beyond the
  filesystem itself).

ACCEPTANCE CRITERIA
--------------------
- Writing then reading a key round-trips exactly.
- Overwriting an existing key never leaves a truncated/partial file visible
  — this is what the test suite exercises by simulating a failure mid-write
  and asserting the *original* content is still intact afterward.
- No leftover `tmp*` files remain in `root` after a successful OR a failed
  write.
- Path-traversal keys (`"../escape"`, `"/etc/passwd"`, `"a/../../b"`) are
  rejected with `ValueError` before any filesystem write is attempted.
- Correct file permissions on the resulting file.
"""

from __future__ import annotations

from pathlib import Path


class AtomicFileStore:
    """A directory-backed key/value store with crash-safe atomic writes."""

    def __init__(self, root: Path, *, file_mode: int = 0o644) -> None:
        # TODO: store root (resolved to an absolute path), create it if
        # missing, store file_mode.
        raise NotImplementedError

    def _resolve(self, key: str) -> Path:
        """Validate `key` and return the absolute path it maps to.

        TODO: reject empty keys, absolute-path keys, and any key whose
        resolved path escapes `self.root` (use Path.resolve() + a
        relative_to() check, or is_relative_to() on 3.9+/3.12).
        """
        raise NotImplementedError

    def write_bytes(self, key: str, data: bytes) -> None:
        """Atomically create-or-replace the file for `key` with `data`.

        TODO:
        - resolve/validate key
        - mkstemp() in the same directory
        - write + flush + fsync the temp file
        - chmod to self.file_mode
        - os.replace(tmp, target)
        - fsync the containing directory
        - clean up the temp file on any exception path
        """
        raise NotImplementedError

    def write_text(self, key: str, text: str, *, encoding: str = "utf-8") -> None:
        """TODO: encode and delegate to write_bytes."""
        raise NotImplementedError

    def read_bytes(self, key: str) -> bytes:
        """TODO: resolve/validate key, read and return file contents."""
        raise NotImplementedError

    def read_text(self, key: str, *, encoding: str = "utf-8") -> str:
        """TODO: decode read_bytes()."""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """TODO: resolve/validate key, unlink. Missing file -> let
        FileNotFoundError propagate (do not swallow it)."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """TODO: resolve/validate key, return whether the file exists."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `tempfile.mkstemp(dir=..., prefix=..., suffix=...)` returns (fd, path);
#   wrap the fd with `os.fdopen(fd, "wb")` so you get a normal file object
#   you can `.write()` to, or use `os.write(fd, data)` + `os.close(fd)`
#   directly — either is fine, just be consistent about who closes what.
# - `Path.is_relative_to()` (3.9+) is the clean way to check containment
#   after `Path.resolve()`.
# - `contextlib.suppress(FileNotFoundError)` is handy when cleaning up a
#   temp file that might already be gone.
# - Directory fsync: `fd = os.open(dir_path, os.O_RDONLY); os.fsync(fd);
#   os.close(fd)` — this is the step people forget; without it the rename
#   itself might not survive a power loss even though the file content did.
#
# Pitfalls
# --------
# - Creating the temp file with `tempfile.NamedTemporaryFile()` (default
#   directory) instead of `dir=root` — breaks atomicity if `/tmp` is a
#   different filesystem/mount than `root` (extremely common on Linux where
#   `/tmp` is tmpfs).
# - Forgetting `os.fsync` on the temp file before `os.replace` — the rename
#   is atomic but the *data* it points to might not be durable yet.
# - Using `shutil.move` — falls back to a non-atomic copy across devices,
#   silently defeating the whole point of this exercise.
# - Not validating keys — a naive `root / key` join lets `key="../../etc/cron.d/x"`
#   write outside the store entirely.
#
# Stretch goals
# -------------
# - Add `write_bytes_if_unchanged(key, data, expected_old: bytes | None)` —
#   an optimistic-concurrency variant that raises if the current on-disk
#   content doesn't match `expected_old` (read-check-write race is still
#   possible without a lock; document that honestly rather than pretending
#   it's solved — true compare-and-swap needs problem 10's techniques or a
#   file lock).
# - Add a `list_keys() -> Iterator[str]` that walks `root`.
# - Make the store survive being handed a `root` that doesn't exist yet by
#   creating parent directories, and reason in a comment about whether that
#   directory-creation step itself needs a directory fsync.
