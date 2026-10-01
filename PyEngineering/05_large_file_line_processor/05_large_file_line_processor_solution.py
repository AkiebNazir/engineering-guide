"""
05 — Large File Line Processor — Reference Solution
====================================================

See `05_large_file_line_processor_explanation.py` for the full spec,
rationale and acceptance criteria. Summary of the design:

    - Every reader works on `bytes` from a binary stream, never on the whole
      file. Memory per call is bounded by a number the caller chose
      (`max_line_bytes`, `chunk_size`), except in `iter_lines_unbounded`,
      which says so in its name.
    - Errors carry the line number (`LineError.line_num`) and chain the
      original exception with `raise ... from`, so callers can branch on
      `err.__cause__` without parsing messages.
    - Cancellation is cooperative: a `threading.Event` checked once per line
      or per chunk. Blocking file I/O can't be interrupted from outside in
      Python, so the only honest guarantee is "stops within one unit".
"""

from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from os import PathLike
from typing import BinaryIO, Protocol

LineFunc = Callable[[int, bytes], None]


class ReadIntoStream(Protocol):
    """Anything with readinto(): open(..., "rb"), io.BytesIO, sockets'
    makefile("rb"), gzip.open(...). typing.BinaryIO doesn't declare it."""

    def readinto(self, buffer: memoryview, /) -> int | None: ...


class LineTooLongError(Exception):
    """Cause attached to a LineError when a line exceeds max_line_bytes."""


class ProcessingCancelled(Exception):
    """Raised when the caller's cancel event is set."""


class LineError(Exception):
    """A failure while processing a specific (1-indexed) line.

    The underlying failure is available as `__cause__` because every raise
    site uses `raise LineError(n, exc) from exc`. That is the Python version
    of Go's `fmt.Errorf("...: %w", err)` + `errors.As`: the wrapper adds
    context (which line), the cause keeps its type (what went wrong).
    """

    def __init__(self, line_num: int, cause: BaseException) -> None:
        super().__init__(f"line {line_num}: {cause}")
        self.line_num = line_num


def _strip_eol(raw: bytes) -> tuple[bytes, bool]:
    """Drop one trailing b"\\n" and, only then, one preceding b"\\r".

    A lone trailing b"\\r" on an unterminated final line is data, not a line
    ending, so it is left alone.
    """
    if raw.endswith(b"\n"):
        raw = raw[:-1]
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        return raw, True
    return raw, False


def _too_long(line_num: int, max_line_bytes: int) -> LineError:
    cause = LineTooLongError(f"line exceeds {max_line_bytes} bytes")
    err = LineError(line_num, cause)
    err.__cause__ = cause
    return err


def iter_lines(stream: BinaryIO, max_line_bytes: int) -> Iterator[bytes]:
    """Yield line contents (no terminator), refusing lines over the limit.

    `readline(limit)` is the load-bearing call: it returns as soon as it
    finds b"\\n" OR has collected `limit` bytes, so one call never holds
    more than `limit` bytes of a line, however long the line is.

    Why `max_line_bytes + 2`: a line whose *content* is exactly at the limit
    arrives as content + b"\\r\\n" in the worst case, i.e. limit + 2 bytes.
    If we read limit + 2 bytes and still haven't seen b"\\n", the content is
    at least limit + 1 bytes (the extra byte may be a b"\\r" whose b"\\n"
    hasn't arrived, but then the content before it is limit + 1 bytes) --
    over the limit either way, without reading another byte of it.
    """
    if max_line_bytes < 1:
        raise ValueError("max_line_bytes must be >= 1")
    read_size = max_line_bytes + 2
    line_num = 0
    while True:
        raw = stream.readline(read_size)
        if not raw:
            return
        line_num += 1
        content, had_newline = _strip_eol(raw)
        if (not had_newline and len(raw) == read_size) or len(content) > max_line_bytes:
            # Stop here: we can't resynchronise to the next line without
            # reading (and discarding) the rest of this one, which is exactly
            # the unbounded work the limit exists to prevent. A caller that
            # wants skip-and-continue can implement it explicitly (read and
            # discard in bounded chunks until b"\\n").
            raise _too_long(line_num, max_line_bytes)
        yield content


def scan_lines(
    stream: BinaryIO,
    max_line_bytes: int,
    fn: LineFunc,
    *,
    cancel: threading.Event | None = None,
) -> int:
    """Run `fn(line_num, line)` for every line; stop on the first failure.

    Returns the number of lines `fn` completed successfully.
    """
    if cancel is not None and cancel.is_set():
        raise ProcessingCancelled("cancelled before start")
    processed = 0
    for line_num, line in enumerate(iter_lines(stream, max_line_bytes), start=1):
        # Per-line check: lines are the natural unit of work here, and
        # Event.is_set() is a cheap attribute read, so the overhead is tiny.
        if cancel is not None and cancel.is_set():
            raise ProcessingCancelled(f"cancelled after {processed} lines")
        try:
            fn(line_num, line)
        except Exception as exc:  # BaseException (KeyboardInterrupt...) passes through
            raise LineError(line_num, exc) from exc
        processed += 1
    return processed


def count_lines(
    stream: ReadIntoStream,
    *,
    chunk_size: int = 64 * 1024,
    cancel: threading.Event | None = None,
) -> int:
    """Count b"\\n" bytes with O(chunk_size) memory (`wc -l` semantics).

    One `bytearray` is allocated up front and refilled by `readinto`; no
    per-chunk or per-line objects are created. `f.read(n)` in a loop would
    allocate a fresh `bytes` for every chunk -- still O(chunk) peak memory,
    but constant allocator churn for a function whose only job is counting.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if cancel is not None and cancel.is_set():
        raise ProcessingCancelled("cancelled before start")
    buf = bytearray(chunk_size)
    view = memoryview(buf)
    total = 0
    try:
        while True:
            n = stream.readinto(view)
            if n is None:
                raise BlockingIOError("count_lines needs a blocking stream")
            if n == 0:
                return total
            # Only the first n bytes are this chunk; the rest are stale.
            total += buf.count(b"\n", 0, n)
            if cancel is not None and cancel.is_set():
                raise ProcessingCancelled(f"cancelled after {total} lines")
    finally:
        # Release the export so `buf` could be resized/freed; leaving a live
        # memoryview around is a classic "BufferError: Existing exports"
        # source in code that reuses buffers.
        view.release()


def iter_lines_unbounded(stream: BinaryIO) -> Iterator[bytes]:
    """Yield every line with no length limit (memory grows to fit a line).

    Iterating a binary file is `readline()` with no size, i.e. exactly the
    unbounded behaviour `iter_lines` guards against. Use it only when huge
    lines are legitimate AND the input is trusted or pre-validated in size.
    """
    for raw in stream:
        content, _ = _strip_eol(raw)
        yield content


def count_by_field(
    lines: Iterable[bytes], field: int, *, sep: bytes | None = None
) -> Counter[bytes]:
    """Count occurrences of the `field`-th column across `lines`.

    `field` indexes like a list (negative counts from the end); lines that
    don't have that column are skipped rather than raising.

    Composed with iter_lines this is a streaming pipeline:
        count_by_field(iter_lines(f, 64 * 1024), field=8)   # nginx status
    Memory is O(distinct keys + one line), independent of file size. The
    generator expression keeps each stage lazy; a list comprehension here
    would materialise every field of every line first.
    """
    return Counter(
        parts[field]
        for parts in (line.split(sep) for line in lines)
        if -len(parts) <= field < len(parts)
    )


def process_file(
    path: str | PathLike[str],
    max_line_bytes: int,
    fn: LineFunc,
    *,
    cancel: threading.Event | None = None,
) -> int:
    """Open `path` (binary), process it with scan_lines, always close it.

    The `with` block is the Python `defer f.Close()`: it closes on return,
    on exception, and on cancellation. For a read-only file a failing
    close() cannot lose data, so there is nothing more to check (contrast
    problem 06, where the close/fsync of a *written* file matters).
    `open()` already puts the path in its OSError message, so no extra
    wrapping is needed for "which file failed".
    """
    with open(path, "rb") as f:
        return scan_lines(f, max_line_bytes, fn, cancel=cancel)


if __name__ == "__main__":
    import io

    demo = io.BytesIO(
        b'10.0.0.1 - - "GET / HTTP/1.1" 200\r\n'
        b'10.0.0.2 - - "GET /x HTTP/1.1" 404\n'
        b'10.0.0.1 - - "GET / HTTP/1.1" 200'
    )
    print("lines (wc -l):", count_lines(demo))
    demo.seek(0)
    print("status counts:", count_by_field(iter_lines(demo, 1024), field=-1))


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Decide the maximum line length as a product decision (what is the
#   longest legitimate record?) and make it a named config value, not a
#   magic number buried in a parser.
# - Fail with *where* (line number, and ideally byte offset via tell()) and
#   *what* (the chained cause). An operator with a 40 GB file needs to be
#   able to `sed -n '1234567p'` the bad line.
# - Keep stages as generators and push decoding/parsing to the consumer:
#   each stage is testable against `io.BytesIO`, and memory stays bounded by
#   the stage with the most state.
# - Reuse buffers in hot read loops (`readinto`), and release memoryviews.
#
# Alternative approaches
# -----------------------
# - `mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)`: lets the OS page
#   the file in and out; `mm.find(b"\n", pos)` scans at C speed. Good for
#   random access (jump to a byte offset, binary-search a sorted log);
#   no benefit for a single sequential pass, and 32-bit/large-file and
#   network-filesystem caveats apply.
# - `csv.reader(open(path, newline=""))` for real CSV (quoted fields may
#   contain newlines, so "one line = one record" is false for CSV). Set
#   `csv.field_size_limit()` deliberately -- its default (131072) is the
#   csv module's version of the line-length limit.
# - Offload to tools built for it when the job is ad-hoc: `wc -l`, `grep
#   -c`, `awk`, DuckDB/Polars `scan_csv` (lazy, columnar, multi-threaded).
# - For CPU-heavy per-line parsing, split into byte ranges and use a
#   ProcessPoolExecutor (see stretch goals), since threads won't parallelise
#   pure-Python parsing under the GIL (problems 33/34).
