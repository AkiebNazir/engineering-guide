"""
04 — Custom Stream Reader/Writer
=================================

WHAT
----
A small library of composable, constant-memory streaming primitives built
on Python's `io` class hierarchy -- the Python counterpart of wrapping Go's
`io.Reader`/`io.Writer`:

    - `UpperReader`: an `io.RawIOBase` that wraps any binary stream and
      uppercases ASCII bytes as they flow through `readinto`, never holding
      more than one caller-sized chunk.
    - `CountingWriter`: an `io.RawIOBase` that forwards writes to another
      binary stream and counts bytes, with a count that is safe to read
      from a metrics thread while writes happen on another.
    - `LineSplitWriter`: a writable stream that accepts arbitrary chunks and
      calls `on_line(str)` once per complete line, even when a line (or a
      multi-byte UTF-8 character, or a CRLF pair) is split across writes.
    - `upper_chunks`: the same transform as a *generator* -- the most
      Pythonic streaming shape, with natural pull-based backpressure.
    - `stream_pipeline`: a producer thread and a consumer joined by a
      *bounded* `queue.Queue`, so a slow consumer blocks a fast producer
      instead of letting memory grow without limit, with errors from
      either side re-raised in the caller and no leaked thread.

WHY THIS MATTERS
-----------------
Files, sockets, `gzip.GzipFile`, `zipfile` members, HTTP bodies,
`io.BytesIO`, `sys.stdout.buffer` -- everything that moves bytes in Python
speaks the file-object protocol (`read`/`readinto`/`write`). A wrapper
that implements the same protocol drops into all of them: you can put
`UpperReader` under `io.BufferedReader` and call `readline()` on it, pass
`CountingWriter` to `shutil.copyfileobj`, or wrap it in
`io.TextIOWrapper`. The skill is staying *streaming*: transform chunk by
chunk in O(chunk) memory, instead of `data = f.read(); dst.write(f(data))`,
which works on a 10 KB test fixture and dies on a 10 GB production file.

Backpressure is the other half. Connecting a producer and a consumer with
an unbounded buffer (a plain list, `queue.Queue()` with no maxsize,
`asyncio.Queue()` with no maxsize) just moves the problem: if the consumer
is slower, the buffer grows until the process is OOM-killed. A bounded
queue makes the producer wait -- which is what Go's `io.Pipe` does with a
zero-size buffer.

CONCEPTS EXERCISED
-------------------
    - The `io` hierarchy: `RawIOBase` (implement `readinto`/`write`, get
      `read`, `readall`, iteration and context management for free),
      `BufferedReader`/`BufferedWriter` on top for efficient small reads.
    - The raw-read contract: `readinto(b)` may return fewer bytes than
      `len(b)` even when more data exists, returns 0 only at EOF, and
      returns None only for non-blocking streams with no data yet.
    - The raw-write contract: `write(b)` returns how many bytes it actually
      consumed; a caller that ignores a short count silently drops data.
    - Memory-safe buffers: `memoryview` slices instead of `bytes` copies.
    - Thread safety of `+=` on an attribute (it isn't atomic) and why a
      `threading.Lock` is needed even under the GIL.
    - Incremental decoding: why you split on b"\\n" *before* decoding UTF-8.
    - Generators as lazy stream transforms.
    - Producer/consumer with a bounded queue, a sentinel, error hand-off
      and a stop `Event`, so neither side can hang the other.

SPEC
----
    class UpperReader(io.RawIOBase):
        def __init__(self, raw: BinaryIO) -> None
        def readable(self) -> bool
        def readinto(self, b: WriteableBuffer) -> int
            "Read into b from the wrapped stream, uppercase ASCII a-z in the
             bytes actually read, return the count. EOF -> 0. Errors from
             the wrapped stream propagate unchanged."

    class CountingWriter(io.RawIOBase):
        def __init__(self, raw: BinaryIO) -> None
        def writable(self) -> bool
        def write(self, b: ReadableBuffer) -> int
            "Forward b, add the number of bytes the wrapped stream accepted
             to the count, return that number."
        @property
        def count(self) -> int   # safe to read from another thread

    class LineSplitWriter(io.RawIOBase):
        def __init__(self, on_line: Callable[[str], None], encoding: str = "utf-8") -> None
        def writable(self) -> bool
        def write(self, b: ReadableBuffer) -> int
            "Buffer b; for each complete b'\\n'-terminated line, strip the
             terminator (and one preceding b'\\r'), decode, call on_line."
        def close(self) -> None
            "Deliver a trailing partial line (no final newline) exactly once,
             then close. Idempotent."
        (flush() keeps io's meaning -- 'push what you can' -- and must NOT
         deliver a partial line: see the Hints for why.)

    def upper_chunks(chunks: Iterable[bytes]) -> Iterator[bytes]
        "Lazily yield each chunk uppercased."

    def stream_pipeline(src: BinaryIO, dst: BinaryIO, *,
                        chunk_size: int = 64 * 1024, max_pending: int = 4) -> int
        "Producer thread: read src through UpperReader in chunk_size pieces
         into a queue.Queue(maxsize=max_pending). Consumer (the calling
         thread): write every chunk to dst. Returns bytes written. An
         exception on either side is re-raised in the caller, and the
         producer thread has exited by the time the function returns."

ACCEPTANCE CRITERIA
--------------------
    - UpperReader output equals `data.upper()` for any bytes (non-ASCII
      bytes unchanged), including when read through tiny buffers, and works
      under `io.BufferedReader` (`readline`, iteration).
    - CountingWriter's count is exact after many concurrent writes from
      several threads.
    - LineSplitWriter handles: one line per write, a line split across
      writes, several lines in one write, CRLF (including '\\r' and '\\n'
      arriving in different writes), a UTF-8 character split across writes,
      and a trailing partial line delivered on close() exactly once.
    - stream_pipeline copies correctly, re-raises a src read error and a
      dst write error, and never lets the producer get more than
      `max_pending` chunks (+ the one in hand) ahead of a slow consumer.

Everything below is a stub. Fill in the `# TODO:` markers. Full type hints
are already in place -- match them.
"""

from __future__ import annotations

import io
from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from collections.abc import Buffer

    ReadableBuffer = Buffer
    WriteableBuffer = Buffer


class UpperReader(io.RawIOBase):
    def __init__(self, raw: BinaryIO) -> None:
        super().__init__()
        self._raw = raw

    def readable(self) -> bool:
        return True

    def readinto(self, b: WriteableBuffer) -> int:
        # TODO:
        #  - view = memoryview(b).cast("B")
        #  - n = self._raw.readinto(view) if the raw stream supports it,
        #    else read(len(view)) and copy into view[:n]
        #  - uppercase view[:n] in place (bytes.upper() is ASCII-only)
        raise NotImplementedError


class CountingWriter(io.RawIOBase):
    def __init__(self, raw: BinaryIO) -> None:
        super().__init__()
        self._raw = raw
        # TODO: a count field and a threading.Lock guarding it.

    def writable(self) -> bool:
        return True

    def write(self, b: ReadableBuffer) -> int:
        # TODO: forward, count what was actually accepted, return it.
        raise NotImplementedError

    @property
    def count(self) -> int:
        # TODO
        raise NotImplementedError


class LineSplitWriter(io.RawIOBase):
    def __init__(self, on_line: Callable[[str], None], encoding: str = "utf-8") -> None:
        super().__init__()
        self._on_line = on_line
        self._encoding = encoding
        self._pending = bytearray()

    def writable(self) -> bool:
        return True

    def write(self, b: ReadableBuffer) -> int:
        # TODO:
        #  - raise ValueError if closed
        #  - append b to self._pending
        #  - while b"\n" in pending: cut the line, strip one trailing b"\r",
        #    decode, call on_line
        #  - return len(b) (in bytes)
        raise NotImplementedError

    def close(self) -> None:
        # TODO: if not already closed and pending is non-empty, deliver it
        #  (strip a trailing b"\r"), clear it, then super().close().
        raise NotImplementedError


def upper_chunks(chunks: Iterable[bytes]) -> Iterator[bytes]:
    # TODO: a one-line generator.
    raise NotImplementedError


def stream_pipeline(
    src: BinaryIO,
    dst: BinaryIO,
    *,
    chunk_size: int = 64 * 1024,
    max_pending: int = 4,
) -> int:
    # TODO:
    #  - q: queue.Queue[bytes | BaseException | None] = queue.Queue(max_pending)
    #  - stop = threading.Event()
    #  - producer(): read UpperReader(src) chunk by chunk; put each chunk
    #    (use put(timeout=...) in a loop that checks `stop`, so a failed
    #    consumer can't leave the producer blocked forever); put None at
    #    EOF; on exception, put the exception instead
    #  - consumer (this thread): get; None -> done; exception -> raise it;
    #    bytes -> dst.write
    #  - finally: stop.set(); thread.join()
    raise NotImplementedError


if __name__ == "__main__":
    print("Implement the TODOs, then run the tests: pytest 04_custom_stream_reader_writer/")


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - Subclass `io.RawIOBase` and implement only `readinto` (reading) or
#   `write` (writing) plus `readable()`/`writable()`. The base class
#   supplies `read(n)`, `readall()`, `readline()`, iteration, `with`
#   support and `closed`. Wrap the result in `io.BufferedReader(...)` when
#   callers make many small reads.
# - In-place uppercase without allocating a whole new buffer:
#   `view[:n] = view[:n].tobytes().upper()` copies n bytes once, which is
#   bounded by the chunk size, not the stream size. `bytes.translate` with a
#   prebuilt 256-byte table is the fastest general byte-mapping tool.
# - Why not deliver a partial line in `flush()`? Because `flush()` in the io
#   world means "push buffered data downstream", and wrappers call it
#   whenever they like: `io.BufferedWriter` calls it, `TextIOWrapper` with
#   `line_buffering` calls it, `print(..., flush=True)` calls it. If flush
#   emitted partial lines, one logical line could be delivered as two.
#   End-of-stream is `close()`, which is also what a `with` block calls.
# - Buffer bytes and split on b"\n" *before* decoding: in UTF-8 the byte
#   0x0A never appears inside a multi-byte character, so every split point
#   is safe, whereas decoding each write separately fails when a character
#   straddles two writes.
#
# Pitfalls
# --------
# - `self.count += n` from several threads loses updates: it's a read, an
#   add and a store, and the GIL can switch threads between them.
# - A producer that exits on error without putting anything leaves the
#   consumer blocked in `q.get()` forever. Always put either the sentinel or
#   the exception.
# - A consumer that raises without telling the producer leaves the producer
#   blocked in `q.put()` forever (a leaked thread, and `join()` hangs).
# - Returning `len(b)` from a writer's `write()` when the wrapped stream
#   accepted fewer bytes.
#
# Stretch goals
# -------------
# - An asyncio version with `asyncio.Queue(maxsize=...)` and
#   `asyncio.StreamReader`, and compare it with the thread version.
# - A `TeeReader` that copies everything it reads into a writer (hashing a
#   download while saving it).
# - Replace the queue with `os.pipe()` and compare: the kernel pipe buffer
#   (typically 64 KiB on Linux) becomes the backpressure bound.
