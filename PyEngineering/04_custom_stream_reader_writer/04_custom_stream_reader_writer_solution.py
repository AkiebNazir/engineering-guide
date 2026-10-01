"""
04 — Custom Stream Reader/Writer — solution.

See `04_custom_stream_reader_writer_explanation.py` for the full spec,
rationale and acceptance criteria. Every type here is an `io.RawIOBase`
subclass, so it plugs into anything that accepts a binary file object.
"""

from __future__ import annotations

import io
import queue
import threading
from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from collections.abc import Buffer

    ReadableBuffer = Buffer
    WriteableBuffer = Buffer

# A 256-entry byte map: a-z -> A-Z, every other byte to itself. translate()
# with a table runs in C with no per-byte Python work.
_UPPER_TABLE = bytes(range(256)).upper()


class UpperReader(io.RawIOBase):
    """Uppercases ASCII bytes as they are read. Memory use is whatever buffer
    the caller passes to `readinto`, independent of the stream's length."""

    def __init__(self, raw: BinaryIO) -> None:
        super().__init__()
        self._raw = raw

    def readable(self) -> bool:
        return True

    def readinto(self, b: WriteableBuffer) -> int:
        view = memoryview(b).cast("B")
        readinto = getattr(self._raw, "readinto", None)
        if readinto is not None:
            # Read straight into the caller's buffer: no intermediate bytes.
            n = readinto(view)
        else:
            chunk = self._raw.read(len(view))
            n = len(chunk)
            view[:n] = chunk
        if n is None:
            # Non-blocking source with no data yet. Pass it through: turning
            # it into 0 would tell the caller "EOF" and truncate the stream.
            return None  # type: ignore[return-value]
        if n == 0:
            return 0  # EOF
        # Transform only the bytes actually read, never the whole buffer: a
        # short read leaves stale data in view[n:].
        view[:n] = view[:n].tobytes().translate(_UPPER_TABLE)
        return int(n)


class CountingWriter(io.RawIOBase):
    """Forwards writes and counts bytes accepted. `count` can be polled from
    another thread (a metrics exporter) while writes happen here."""

    def __init__(self, raw: BinaryIO) -> None:
        super().__init__()
        self._raw = raw
        self._count = 0
        # `self._count += n` is load/add/store: under the GIL a thread switch
        # can land between them and lose an update. The lock makes it atomic.
        # (Python has no user-level atomic int; itertools.count() tricks rely
        # on CPython implementation details.)
        self._lock = threading.Lock()

    def writable(self) -> bool:
        return True

    def write(self, b: ReadableBuffer) -> int:
        n = self._raw.write(b)  # type: ignore[arg-type]
        if n is None:
            # Non-blocking stream that would block: nothing was written.
            return None  # type: ignore[return-value]
        # Count what the wrapped stream reports it accepted, not len(b): a raw
        # (unbuffered) stream is allowed to do a short write, and the caller
        # (e.g. BufferedWriter) retries the rest based on this return value.
        with self._lock:
            self._count += n
        return n

    def flush(self) -> None:
        super().flush()
        self._raw.flush()

    @property
    def count(self) -> int:
        with self._lock:
            return self._count


class LineSplitWriter(io.RawIOBase):
    """Accepts arbitrary chunks and calls `on_line` once per complete line."""

    def __init__(self, on_line: Callable[[str], None], encoding: str = "utf-8") -> None:
        super().__init__()
        self._on_line = on_line
        self._encoding = encoding
        self._pending = bytearray()

    def writable(self) -> bool:
        return True

    def _emit(self, line: bytes | bytearray) -> None:
        if line.endswith(b"\r"):
            line = line[:-1]
        self._on_line(line.decode(self._encoding))

    def write(self, b: ReadableBuffer) -> int:
        if self.closed:
            raise ValueError("write to closed LineSplitWriter")
        data = memoryview(b).cast("B")
        self._pending += data
        # Split on raw bytes, decode per complete line: 0x0A never occurs
        # inside a multi-byte UTF-8 sequence, so a character split across two
        # writes is reassembled in _pending before it is ever decoded. A
        # '\r' that arrives without its '\n' also just waits in _pending.
        start = 0
        while (end := self._pending.find(b"\n", start)) != -1:
            self._emit(self._pending[start:end])
            start = end + 1
        if start:
            # One compaction per write, not one per line: deleting the head of
            # a bytearray is O(remaining), so doing it per line would be
            # quadratic for a write containing many lines.
            del self._pending[:start]
        return len(data)

    # flush() is deliberately inherited unchanged. See the explanation's
    # Hints: wrappers call flush() at arbitrary points, so it must not cut a
    # partial line. End-of-stream is close().

    def close(self) -> None:
        if self.closed:
            return
        try:
            if self._pending:
                pending, self._pending = self._pending, bytearray()
                self._emit(pending)
        finally:
            super().close()


def upper_chunks(chunks: Iterable[bytes]) -> Iterator[bytes]:
    # A generator is pull-based: nothing is read from `chunks` until the
    # consumer asks for the next item, so backpressure is automatic and
    # memory is one chunk. Chain them: upper_chunks(iter(partial(f.read, n), b"")).
    for chunk in chunks:
        yield chunk.translate(_UPPER_TABLE)


_EOF = None


def stream_pipeline(
    src: BinaryIO,
    dst: BinaryIO,
    *,
    chunk_size: int = 64 * 1024,
    max_pending: int = 4,
) -> int:
    if chunk_size < 1 or max_pending < 1:
        raise ValueError("chunk_size and max_pending must be >= 1")

    # Bounded: when max_pending chunks are waiting, put() blocks the producer
    # until the consumer catches up. That is the backpressure.
    q: queue.Queue[bytes | BaseException | None] = queue.Queue(maxsize=max_pending)
    stop = threading.Event()

    def put(item: bytes | BaseException | None) -> bool:
        # A blocking put() with no timeout could wait forever if the consumer
        # died. Poll with a short timeout and give up once `stop` is set.
        while not stop.is_set():
            try:
                q.put(item, timeout=0.05)
                return True
            except queue.Full:
                continue
        return False

    def producer() -> None:
        reader = UpperReader(src)
        try:
            while chunk := reader.read(chunk_size):
                if not put(chunk):
                    return  # consumer gave up
            put(_EOF)
        except BaseException as exc:  # noqa: BLE001 - handed to the consumer
            put(exc)

    thread = threading.Thread(target=producer, name="stream-pipeline-producer", daemon=True)
    thread.start()
    written = 0
    try:
        while True:
            item = q.get()
            if item is _EOF:
                break
            if isinstance(item, BaseException):
                raise item
            view = memoryview(item)
            while view:  # honour short writes
                n = dst.write(view)
                if n is None:  # only a non-blocking dst does this
                    raise BlockingIOError("stream_pipeline needs a blocking dst")
                view = view[n:]
                written += n
        dst.flush()
        return written
    finally:
        # Runs on success and on either side's failure: unblocks a producer
        # stuck in put(), then waits for it, so no thread outlives the call.
        # (A producer blocked inside src.read() on a socket can't be
        # interrupted this way; that needs a timeout on the socket itself.)
        stop.set()
        thread.join()


if __name__ == "__main__":
    out = io.BytesIO()
    lines: list[str] = []
    n = stream_pipeline(io.BytesIO(b"hello\nstreaming world\n"), out, chunk_size=4)
    with LineSplitWriter(lines.append) as splitter:
        splitter.write(out.getvalue())
    print(f"{n} bytes -> {lines}")


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Implement the *raw* layer (`readinto`/`write`) and let `io.BufferedReader`
#   / `io.BufferedWriter` / `io.TextIOWrapper` add buffering and text. That
#   gives callers `readline()`, iteration, `peek()`, encodings and newline
#   translation without you writing any of it.
# - Transform in place in a caller-provided buffer (`readinto`) to keep the
#   memory profile flat; use `memoryview` slicing, which does not copy.
# - Put the lock only around the shared counter, never around the I/O call:
#   holding it across `raw.write` would serialise all writers on the slowest
#   disk/socket operation.
# - Every thread you start has an owner that joins it. The try/finally with a
#   stop Event is the thread equivalent of Go's `CloseWithError`.
#
# Alternative approaches
# -----------------------
# - `asyncio`: `asyncio.Queue(maxsize=n)` gives the same bounded hand-off
#   between coroutines, and `StreamWriter.drain()` is asyncio's built-in
#   backpressure point for sockets (it waits while the transport buffer is
#   above its high-water mark).
# - `os.pipe()` + two threads is the literal equivalent of `io.Pipe`, with
#   the kernel pipe buffer (64 KiB by default on Linux) as the bound.
# - For pure transforms, a generator chain (`upper_chunks(read_chunks(f))`)
#   is simpler than any class and has backpressure built in; reach for
#   RawIOBase subclasses when the consumer insists on a file object (e.g.
#   `tarfile.open(fileobj=...)`, `csv.reader(io.TextIOWrapper(...))`).
# - `io.BytesIO` is fine for tests and small payloads, and is exactly the
#   "load it all into memory" design to avoid for unbounded streams.
