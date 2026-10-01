"""
05 — Large File Line Processor
===============================

WHAT
----
A small library for processing line-oriented files (logs, CSV exports,
JSON-lines dumps, access logs) that can be far larger than available memory,
without ever loading the whole file -- or even one whole *unbounded* line --
at once:

    - `iter_lines`: a generator that yields one line at a time with an
      explicit, caller-controlled maximum line length, and raises a
      structured error naming the exact line number when a line is longer.
    - `scan_lines`: the callback-style driver on top of `iter_lines`, with
      cooperative cancellation and per-line error wrapping.
    - `count_lines`: a `wc -l`-style counter using fixed-size chunked
      `readinto` calls into ONE reused buffer -- O(1) memory no matter how
      long the file or any single line is.
    - `iter_lines_unbounded`: the "no cap" variant (plain `readline()`), for
      when individual lines may legitimately be huge and you have decided
      that trading a memory ceiling for flexibility is right.
    - `count_by_field`: an iterator-pipeline aggregation (parse -> select ->
      count) whose memory is bounded by the number of *distinct keys*, not
      by the file size.
    - `process_file`: the real-world entry point -- opens the file, always
      closes it, and wires everything together.

WHY THIS MATTERS
-----------------
The idiomatic Python loop `for line in open(path)` is streaming -- it does
not read the whole file -- so it *looks* memory-safe. It has one sharp edge
that bites production systems: **there is no maximum line length**. A single
line with no newline (a minified 3 GB JSON blob someone dropped into the log
directory, a binary file matched by a glob, a corrupted upload, an attacker
sending an endless header line) makes `readline()` keep growing one `bytes`
object until the process is OOM-killed. Nothing raises; the container just
dies and restarts, and the next run dies on the same file.

Go's `bufio.Scanner` has the opposite trap (a hard 64 KiB default cap that
silently ends the loop unless you check `Err()`); Python's default is "no
cap at all". Both lead to the same engineering decision this problem is
about: **choose a maximum line length deliberately, enforce it with a
bounded read, and fail loudly with the line number when it's exceeded** --
or, if you genuinely need unbounded lines, choose that on purpose and
document the missing memory ceiling.

The other half of the problem is that "line-oriented" work is often not
per-line at all: counting lines, finding the byte offset of line N, or
checksumming a file need no line objects. Allocating a `bytes` per line for
a 50 GB file is pure garbage-collector and allocator churn; a chunked
`readinto` loop over one preallocated `bytearray` does the same job with
constant memory and runs close to disk speed.

CONCEPTS EXERCISED
-------------------
    - `BufferedReader.readline(size)`: the bounded read that caps how many
      bytes a single call may return -- the Python equivalent of
      `Scanner.Buffer(buf, max)`.
    - Distinguishing "line exactly at the limit" from "line over the limit"
      (off-by-one around the terminator, and `\\r\\n` vs `\\n`).
    - `readinto` + `memoryview` + one reused `bytearray` for O(1)-memory
      chunked reads, and why `f.read(n)` in a loop allocates a new object
      per call.
    - Generators as lazy pipeline stages: memory is bounded by the stage
      with the most state (here the `Counter` of distinct keys), not by
      the input size.
    - Structured errors: `LineError` carries `line_num`; the original
      failure is attached with `raise ... from err` so callers can inspect
      `err.__cause__` (the Python analogue of Go's `%w` + `errors.As/Is`).
    - Cooperative cancellation of a long, blocking, CPU+I/O loop with a
      `threading.Event` checked once per natural unit of work (per line,
      per chunk) -- the analogue of checking `ctx.Err()`.
    - Bytes first, decode later: lines are yielded as `bytes`, so an
      invalid UTF-8 sequence in one line can't kill the whole scan; decode
      at the consumer with an explicit `errors=` policy.

SPEC
----
    class LineTooLongError(Exception):
        "The cause attached to a LineError when a line exceeds the limit."

    class ProcessingCancelled(Exception):
        "Raised when the cancel event is set before/while processing."

    class LineError(Exception):
        line_num: int      # 1-indexed line where processing failed
        # str(err) -> "line {line_num}: {cause}"
        # err.__cause__ is the underlying exception (LineTooLongError, or
        # whatever the per-line callback raised)

    LineFunc = Callable[[int, bytes], None]

    def iter_lines(stream: BinaryIO, max_line_bytes: int) -> Iterator[bytes]:
        "Yield each line's content without its '\\n' / '\\r\\n' terminator.
         A final line with no trailing newline IS yielded. If a line's
         content exceeds max_line_bytes, raise LineError(line_num) from
         LineTooLongError -- having read at most max_line_bytes + 2 bytes
         of that line (never the whole line). max_line_bytes < 1 ->
         ValueError."

    def scan_lines(stream, max_line_bytes, fn, *, cancel=None) -> int:
        "Call fn(line_num, line) for each line from iter_lines. Return the
         number of lines fn processed successfully. If fn raises, wrap it
         in LineError(line_num) (chained with `from`) and stop immediately.
         If `cancel` (a threading.Event) is set before or during the scan,
         raise ProcessingCancelled promptly (checked once per line)."

    def count_lines(stream, *, chunk_size=64 * 1024, cancel=None) -> int:
        "Count b'\\n' bytes using readinto() into one reused buffer. `wc -l`
         semantics: an unterminated final line is NOT counted. Check
         `cancel` once per chunk."

    def iter_lines_unbounded(stream: BinaryIO) -> Iterator[bytes]:
        "Like iter_lines but with no maximum: a single line may use as much
         memory as it needs. Strip '\\n' and a preceding '\\r'. Yield an
         unterminated final line."

    def count_by_field(lines: Iterable[bytes], field: int, *,
                       sep: bytes | None = None) -> Counter[bytes]:
        "Split each line on `sep` (whitespace when None), count field
         number `field` (list-style indexing, so -1 is the last field).
         Lines that don't have that field are skipped."

    def process_file(path, max_line_bytes, fn, *, cancel=None) -> int:
        "Open `path` in binary mode, guarantee it is closed on every exit
         path, and run scan_lines over it."

ACCEPTANCE CRITERIA
--------------------
    - iter_lines/scan_lines handle a 1 MiB line when max_line_bytes allows
      it, and raise LineError with the correct 1-indexed line_num (and a
      LineTooLongError cause) when it doesn't -- including a line exactly
      one byte over the limit, while a line exactly AT the limit passes
      (with both '\\n' and '\\r\\n' endings).
    - Rejecting an oversized line is memory-bounded: scanning a stream that
      is one 32 MiB line with a 1 KiB limit fails fast with peak traced
      memory well under 1 MiB.
    - count_lines returns 0 for an empty stream, does not count an
      unterminated final line, and counts a stream that is a single 32 MiB
      line plus '\\n' as 1 with peak traced memory well under 1 MiB.
    - iter_lines_unbounded yields a 200 KiB line intact.
    - A callback that raises stops processing at once; the LineError has the
      right line_num and `__cause__` is the callback's original exception.
    - A pre-set cancel event processes zero lines; an event set during the
      scan stops it within one line / one chunk.
    - CRLF endings never leave a trailing b'\\r' in yielded lines.
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
    """A failure while processing a specific (1-indexed) line."""

    def __init__(self, line_num: int, cause: BaseException) -> None:
        # TODO: call super().__init__ with a message like
        #  f"line {line_num}: {cause}" and store line_num.
        #  (The caller attaches `cause` via `raise LineError(...) from cause`.)
        raise NotImplementedError


def _strip_eol(raw: bytes) -> tuple[bytes, bool]:
    """Return (content, had_newline): drop one trailing b"\\n" and then one
    trailing b"\\r" if present."""
    # TODO
    raise NotImplementedError


def iter_lines(stream: BinaryIO, max_line_bytes: int) -> Iterator[bytes]:
    # TODO:
    #  - validate max_line_bytes >= 1
    #  - loop: raw = stream.readline(max_line_bytes + 2)
    #      (+2 leaves room for b"\r\n" on a line whose content is exactly
    #       max_line_bytes -- work through the off-by-one on paper)
    #  - b"" -> EOF, return
    #  - no trailing b"\n" AND len(raw) == max_line_bytes + 2 -> the line
    #    is longer than the limit: raise LineError(n) from LineTooLongError
    #  - strip the terminator; content longer than max_line_bytes -> same
    #    error
    #  - yield content
    raise NotImplementedError


def scan_lines(
    stream: BinaryIO,
    max_line_bytes: int,
    fn: LineFunc,
    *,
    cancel: threading.Event | None = None,
) -> int:
    # TODO:
    #  - raise ProcessingCancelled up front if cancel is already set
    #  - for line_num, line in enumerate(iter_lines(...), start=1):
    #      check cancel; call fn inside try/except Exception, re-raise as
    #      `raise LineError(line_num, exc) from exc`; count successes
    #  - return the count
    raise NotImplementedError


def count_lines(
    stream: ReadIntoStream,
    *,
    chunk_size: int = 64 * 1024,
    cancel: threading.Event | None = None,
) -> int:
    # TODO:
    #  - allocate ONE bytearray(chunk_size) and a memoryview over it,
    #    outside the loop
    #  - loop: n = stream.readinto(view); n == 0 -> done
    #    (None means "non-blocking stream, no data yet": treat as an error
    #    here -- this function is for regular files and pipes in blocking
    #    mode)
    #  - total += buf.count(b"\n", 0, n)   # only the n valid bytes!
    #  - check cancel once per chunk
    raise NotImplementedError


def iter_lines_unbounded(stream: BinaryIO) -> Iterator[bytes]:
    # TODO: `for raw in stream:` (which is readline() with no limit), strip
    #  the terminator, yield. An unterminated final line is still yielded.
    raise NotImplementedError


def count_by_field(
    lines: Iterable[bytes], field: int, *, sep: bytes | None = None
) -> Counter[bytes]:
    # TODO: a Counter fed by a generator expression; skip short lines.
    raise NotImplementedError


def process_file(
    path: str | PathLike[str],
    max_line_bytes: int,
    fn: LineFunc,
    *,
    cancel: threading.Event | None = None,
) -> int:
    # TODO: `with open(path, "rb") as f: return scan_lines(...)`
    raise NotImplementedError


if __name__ == "__main__":
    print("Implement the TODOs, then run the tests: pytest 05_large_file_line_processor/")


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `open(path, "rb")` returns an `io.BufferedReader`; its `readline(size)`
#   stops after `size` bytes even if no newline was found, and never
#   allocates more than that for the returned object. That single argument
#   is the whole memory-safety story of iter_lines.
# - `bytearray.count(sub, start, end)` counts inside the valid prefix of a
#   reused buffer without slicing (slicing a bytearray copies).
# - `readinto` on a `BufferedReader` with a large destination bypasses the
#   internal buffer and reads straight into yours -- the fastest pure-Python
#   read loop available.
# - Keep lines as bytes. If the consumer needs text, decode per line with
#   `line.decode("utf-8", errors="replace")` (or "strict" and handle the
#   error), so one bad byte sequence doesn't end a 12-hour batch job.
# - Text mode (`open(path)`) uses universal newlines: '\r\n' and lone '\r'
#   become '\n'. Binary mode does no translation, which is why you strip
#   '\r' yourself. Pass `newline=""` in text mode (as the csv module
#   requires) to see the raw endings.
#
# Pitfalls
# --------
# - `f.read()` / `f.readlines()` / `list(f)` / `Path.read_text()` on an
#   input whose size you don't control: loads everything.
# - `for line in f` on untrusted input: no maximum line length (see WHY).
# - `stream.readline(max_line_bytes)` (without the +2): a line whose content
#   is exactly at the limit comes back without its newline and looks
#   "too long"; a CRLF line at the limit needs two extra bytes.
# - Forgetting that `readinto` returns how many bytes are valid -- counting
#   newlines in the whole buffer re-counts stale bytes from the previous
#   chunk.
# - Catching the exception from `fn` and continuing: the caller asked to
#   stop on the first failure. Collect-and-continue is a different API
#   (return a list of (line_num, error), and bound its size).
# - Wrapping with `raise LineError(...)` but no `from exc`: the traceback
#   still shows the original, but `err.__cause__` is None and callers can't
#   inspect it programmatically.
#
# Stretch goals
# -------------
# - Parallel processing: split a file into N byte ranges, move each start
#   forward to just after the next b"\n", and process ranges in a
#   `ProcessPoolExecutor` (CPU-bound parsing needs processes; see 12/33).
#   Merge per-range Counters with `sum(counters, Counter())`.
# - An `mmap`-based count_lines (`mm.find(b"\n", pos)` in a loop, or
#   `mm[:].count` on slices) and an honest benchmark against readinto.
# - Progress reporting: a callback every N bytes, using `stream.tell()`.
# - Transparent decompression: accept `.gz`/`.zst` by wrapping the file in
#   `gzip.open(path, "rb")` -- still a BinaryIO, so iter_lines works as-is.
# - A "soft" limit: log lines over a warning threshold but only fail over a
#   hard one.
