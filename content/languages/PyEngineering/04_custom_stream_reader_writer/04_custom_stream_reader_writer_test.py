from __future__ import annotations

import io
import shutil
import threading
import time
from functools import partial
from importlib import import_module
from typing import Any

import pytest

# The module name starts with a digit, so it can't appear in an `import`
# statement; pytest puts this directory on sys.path, so import it by string.
_solution = import_module("04_custom_stream_reader_writer_solution")
UpperReader: Any = _solution.UpperReader
CountingWriter: Any = _solution.CountingWriter
LineSplitWriter: Any = _solution.LineSplitWriter
upper_chunks: Any = _solution.upper_chunks
stream_pipeline: Any = _solution.stream_pipeline

SAMPLE = b"Hello, World!\nstreaming caf\xc3\xa9 \x00\xff bytes\nlast"


class TrickleReader(io.RawIOBase):
    """Returns at most `step` bytes per read, like a slow socket, to force
    many short reads through the wrapper."""

    def __init__(self, data: bytes, step: int) -> None:
        self._src = io.BytesIO(data)
        self._step = step

    def readable(self) -> bool:
        return True

    def readinto(self, b: Any) -> int:
        chunk = self._src.read(min(self._step, len(b)))
        b[: len(chunk)] = chunk
        return len(chunk)


class FailingReader(io.RawIOBase):
    def __init__(self, good: bytes) -> None:
        self._good = good

    def readable(self) -> bool:
        return True

    def readinto(self, b: Any) -> int:
        if self._good:
            n = min(len(b), len(self._good))
            b[:n], self._good = self._good[:n], self._good[n:]
            return n
        raise OSError("disk read failed")


class FailingWriter(io.RawIOBase):
    def writable(self) -> bool:
        return True

    def write(self, b: Any) -> int:
        raise OSError("disk full")


# ------------------------------------------------------------------ UpperReader


@pytest.mark.parametrize("buffer_size", [1, 3, 7, 64, 4096])
def test_upper_reader_matches_bytes_upper(buffer_size: int) -> None:
    reader = UpperReader(io.BytesIO(SAMPLE))
    out = bytearray()
    buf = bytearray(buffer_size)
    while n := reader.readinto(buf):
        out += buf[:n]
    assert bytes(out) == SAMPLE.upper()  # ASCII-only: non-ASCII bytes untouched


def test_upper_reader_handles_short_reads_from_source() -> None:
    reader = UpperReader(TrickleReader(SAMPLE, step=2))
    assert reader.read() == SAMPLE.upper()


def test_upper_reader_composes_with_buffered_reader() -> None:
    buffered = io.BufferedReader(UpperReader(io.BytesIO(b"one\ntwo\nthree\n")))
    assert buffered.readline() == b"ONE\n"
    assert list(buffered) == [b"TWO\n", b"THREE\n"]


def test_upper_reader_propagates_source_errors() -> None:
    reader = UpperReader(FailingReader(b"abc"))
    assert reader.read(3) == b"ABC"
    with pytest.raises(OSError, match="disk read failed"):
        reader.read(3)


def test_upper_reader_only_transforms_bytes_actually_read() -> None:
    reader = UpperReader(io.BytesIO(b"ab"))
    buf = bytearray(b"zzzz")
    assert reader.readinto(buf) == 2
    assert buf == b"ABzz"  # the stale tail is left alone


# --------------------------------------------------------------- CountingWriter


def test_counting_writer_counts_and_forwards() -> None:
    sink = io.BytesIO()
    writer = CountingWriter(sink)
    shutil.copyfileobj(io.BytesIO(SAMPLE), writer, length=5)
    assert sink.getvalue() == SAMPLE
    assert writer.count == len(SAMPLE)


def test_counting_writer_is_thread_safe() -> None:
    writer = CountingWriter(io.BytesIO())
    threads, per_thread = 8, 5_000

    def hammer() -> None:
        for _ in range(per_thread):
            writer.write(b"xy")

    workers = [threading.Thread(target=hammer) for _ in range(threads)]
    for t in workers:
        t.start()
    polled = [writer.count for _ in range(100)]  # concurrent reads must not break
    for t in workers:
        t.join()
    assert writer.count == threads * per_thread * 2
    assert polled == sorted(polled)


def test_counting_writer_counts_short_writes_honestly() -> None:
    class HalfWriter(io.RawIOBase):
        def writable(self) -> bool:
            return True

        def write(self, b: Any) -> int:
            return max(1, len(b) // 2)

    writer = CountingWriter(HalfWriter())
    assert writer.write(b"12345678") == 4
    assert writer.count == 4


def test_counting_writer_propagates_errors() -> None:
    writer = CountingWriter(FailingWriter())
    with pytest.raises(OSError, match="disk full"):
        writer.write(b"x")
    assert writer.count == 0


# -------------------------------------------------------------- LineSplitWriter


@pytest.mark.parametrize(
    ("writes", "expected"),
    [
        ([b"one line\n"], ["one line"]),
        ([b"abc", b"def\n"], ["abcdef"]),
        ([b"a\nb\nc\n"], ["a", "b", "c"]),
        ([b"crlf\r\n", b"two\r\n"], ["crlf", "two"]),
        ([b"split\r", b"\nnext\n"], ["split", "next"]),
        ([b"caf\xc3", b"\xa9\n"], ["café"]),  # UTF-8 char split across writes
        ([b"\n\n"], ["", ""]),
        ([b"x"] * 50 + [b"\n"], ["x" * 50]),
    ],
)
def test_line_split_writer(writes: list[bytes], expected: list[str]) -> None:
    lines: list[str] = []
    writer = LineSplitWriter(lines.append)
    for chunk in writes:
        assert writer.write(chunk) == len(chunk)
    assert lines == expected


def test_line_split_writer_close_delivers_trailing_line_once() -> None:
    lines: list[str] = []
    writer = LineSplitWriter(lines.append)
    writer.write(b"full\npartial")
    writer.flush()  # must NOT cut the partial line
    assert lines == ["full"]
    writer.close()
    writer.close()
    assert lines == ["full", "partial"]


def test_line_split_writer_close_on_empty_buffer_is_noop() -> None:
    lines: list[str] = []
    with LineSplitWriter(lines.append) as writer:
        writer.write(b"done\n")
    assert lines == ["done"]


def test_line_split_writer_rejects_writes_after_close() -> None:
    writer = LineSplitWriter(lambda _line: None)
    writer.close()
    with pytest.raises(ValueError):
        writer.write(b"late\n")


def test_line_split_writer_under_text_wrapper() -> None:
    lines: list[str] = []
    raw = LineSplitWriter(lines.append)
    with io.TextIOWrapper(io.BufferedWriter(raw, buffer_size=4), encoding="utf-8") as text:
        print("printed", "line", file=text)
        text.write("no newline")
    assert lines == ["printed line", "no newline"]


# ------------------------------------------------------------ generator version


def test_upper_chunks_is_lazy() -> None:
    pulled: list[bytes] = []

    def source() -> Any:
        for chunk in (b"ab", b"cd", b"ef"):
            pulled.append(chunk)
            yield chunk

    gen = upper_chunks(source())
    assert next(gen) == b"AB"
    assert pulled == [b"ab"]  # nothing read ahead
    assert list(gen) == [b"CD", b"EF"]


def test_upper_chunks_over_a_file() -> None:
    f = io.BytesIO(SAMPLE)
    assert b"".join(upper_chunks(iter(partial(f.read, 4), b""))) == SAMPLE.upper()


# -------------------------------------------------------------- stream_pipeline


def test_stream_pipeline_copies_and_transforms() -> None:
    data = SAMPLE * 1000
    dst = io.BytesIO()
    assert stream_pipeline(io.BytesIO(data), dst, chunk_size=100) == len(data)
    assert dst.getvalue() == data.upper()


def test_stream_pipeline_empty_source() -> None:
    dst = io.BytesIO()
    assert stream_pipeline(io.BytesIO(b""), dst) == 0
    assert dst.getvalue() == b""


def test_stream_pipeline_propagates_source_error() -> None:
    before = threading.active_count()
    with pytest.raises(OSError, match="disk read failed"):
        stream_pipeline(FailingReader(b"x" * 100), io.BytesIO(), chunk_size=10)
    assert threading.active_count() == before  # producer thread gone


def test_stream_pipeline_propagates_destination_error_without_leaking() -> None:
    before = threading.active_count()
    started = time.monotonic()
    with pytest.raises(OSError, match="disk full"):
        # Large source + tiny queue: the producer is blocked in put() when the
        # consumer fails, so this only returns if the stop signal works.
        stream_pipeline(io.BytesIO(b"x" * 100_000), FailingWriter(), chunk_size=10, max_pending=1)
    assert time.monotonic() - started < 2
    assert threading.active_count() == before


def test_stream_pipeline_applies_backpressure() -> None:
    max_pending = 2
    reads = 0
    max_lead = 0
    writes = 0

    class CountingSource(io.RawIOBase):
        def __init__(self) -> None:
            self._left = 40

        def readable(self) -> bool:
            return True

        def readinto(self, b: Any) -> int:
            nonlocal reads
            if not self._left:
                return 0
            self._left -= 1
            reads += 1
            b[:1] = b"a"
            return 1

    class SlowSink(io.RawIOBase):
        def writable(self) -> bool:
            return True

        def write(self, b: Any) -> int:
            nonlocal writes, max_lead
            time.sleep(0.002)
            writes += 1
            max_lead = max(max_lead, reads - writes)
            return len(b)

    stream_pipeline(CountingSource(), SlowSink(), chunk_size=1, max_pending=max_pending)
    assert writes == 40
    # queued chunks + the one the producer holds + the one being written
    assert max_lead <= max_pending + 2
