from __future__ import annotations

import io
import threading
import tracemalloc
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

# The module name starts with a digit, so it can't appear in an `import`
# statement; pytest puts this directory on sys.path, so import it by string.
_solution = import_module("05_large_file_line_processor_solution")
iter_lines: Any = _solution.iter_lines
scan_lines: Any = _solution.scan_lines
count_lines: Any = _solution.count_lines
iter_lines_unbounded: Any = _solution.iter_lines_unbounded
count_by_field: Any = _solution.count_by_field
process_file: Any = _solution.process_file
LineError: Any = _solution.LineError
LineTooLongError: Any = _solution.LineTooLongError
ProcessingCancelled: Any = _solution.ProcessingCancelled

MiB = 1024 * 1024


class RepeatStream(io.RawIOBase):
    """A lazily generated stream: `size` copies of `fill`, then `tail`.

    Nothing is materialised, so any large peak memory measured while
    reading it comes from the code under test, not from the fixture.
    """

    def __init__(self, size: int, fill: bytes = b"a", tail: bytes = b"") -> None:
        self._left = size
        self._fill = fill
        self._tail = io.BytesIO(tail)

    def readable(self) -> bool:
        return True

    def readinto(self, b: Any) -> int:
        if self._left > 0:
            n = min(len(b), self._left)
            b[:n] = self._fill * n
            self._left -= n
            return n
        chunk = self._tail.read(len(b))
        b[: len(chunk)] = chunk
        return len(chunk)


def lazy(size: int, tail: bytes = b"") -> io.BufferedReader:
    return io.BufferedReader(RepeatStream(size, tail=tail))


def peak_bytes(fn: Callable[[], object]) -> int:
    tracemalloc.start()
    try:
        fn()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def collect(data: bytes, max_line_bytes: int = 1024) -> list[bytes]:
    return list(iter_lines(io.BytesIO(data), max_line_bytes))


# --- iter_lines ---------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"", []),
        (b"one\ntwo\n", [b"one", b"two"]),
        (b"one\ntwo", [b"one", b"two"]),  # unterminated final line is kept
        (b"crlf\r\nline\r\n", [b"crlf", b"line"]),
        (b"\n\n", [b"", b""]),
        (b"lone\rcr\n", [b"lone\rcr"]),  # \r mid-line is data
        (b"tail\r", [b"tail\r"]),  # \r without \n is data too
    ],
)
def test_iter_lines_table(data: bytes, expected: list[bytes]) -> None:
    assert collect(data) == expected


@pytest.mark.parametrize("eol", [b"\n", b"\r\n", b""])
def test_line_exactly_at_limit_passes(eol: bytes) -> None:
    assert collect(b"x" * 8 + eol, max_line_bytes=8) == [b"x" * 8]


@pytest.mark.parametrize("eol", [b"\n", b"\r\n", b""])
def test_line_one_over_limit_fails_with_line_number(eol: bytes) -> None:
    data = b"ok\nfine\n" + b"x" * 9 + eol + b"never reached\n"
    with pytest.raises(LineError) as info:
        collect(data, max_line_bytes=8)
    assert info.value.line_num == 3
    assert isinstance(info.value.__cause__, LineTooLongError)


def test_large_line_within_configured_limit() -> None:
    big = b"y" * MiB
    assert collect(b"a\n" + big + b"\nb\n", max_line_bytes=2 * MiB) == [b"a", big, b"b"]


def test_rejecting_huge_line_is_memory_bounded() -> None:
    stream = lazy(32 * MiB, tail=b"\n")

    def run() -> None:
        with pytest.raises(LineError):
            list(iter_lines(stream, 1024))

    assert peak_bytes(run) < MiB


def test_invalid_max_line_bytes() -> None:
    with pytest.raises(ValueError):
        collect(b"a\n", max_line_bytes=0)


# --- scan_lines ---------------------------------------------------------


def test_scan_lines_calls_fn_with_one_indexed_numbers() -> None:
    seen: list[tuple[int, bytes]] = []
    n = scan_lines(io.BytesIO(b"a\nb\nc"), 16, lambda i, line: seen.append((i, line)))
    assert n == 3
    assert seen == [(1, b"a"), (2, b"b"), (3, b"c")]


class Boom(Exception):
    pass


def test_fn_error_stops_and_is_chained() -> None:
    seen: list[int] = []

    def fn(i: int, line: bytes) -> None:
        seen.append(i)
        if i == 2:
            raise Boom("bad record")

    with pytest.raises(LineError) as info:
        scan_lines(io.BytesIO(b"1\n2\n3\n4\n"), 16, fn)
    assert seen == [1, 2]
    assert info.value.line_num == 2
    assert isinstance(info.value.__cause__, Boom)
    assert "line 2" in str(info.value)


def test_scan_cancelled_before_start_processes_nothing() -> None:
    cancel = threading.Event()
    cancel.set()
    seen: list[int] = []
    with pytest.raises(ProcessingCancelled):
        scan_lines(io.BytesIO(b"a\nb\n"), 16, lambda i, _: seen.append(i), cancel=cancel)
    assert seen == []


def test_scan_cancelled_mid_way_stops_within_one_line() -> None:
    cancel = threading.Event()
    seen: list[int] = []

    def fn(i: int, line: bytes) -> None:
        seen.append(i)
        if i == 3:
            cancel.set()

    data = b"".join(b"%d\n" % i for i in range(1000))
    with pytest.raises(ProcessingCancelled):
        scan_lines(io.BytesIO(data), 16, fn, cancel=cancel)
    assert seen == [1, 2, 3]


# --- count_lines --------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"", 0),
        (b"no newline", 0),  # wc -l semantics
        (b"a\nb\n", 2),
        (b"a\nb", 1),
        (b"\n" * 10, 10),
        (b"x\r\ny\r\n", 2),
    ],
)
def test_count_lines_table(data: bytes, expected: int) -> None:
    assert count_lines(io.BytesIO(data)) == expected


@pytest.mark.parametrize("chunk_size", [1, 3, 7, 64 * 1024])
def test_count_lines_chunk_boundaries(chunk_size: int) -> None:
    data = b"".join(b"line %d\n" % i for i in range(500))
    assert count_lines(io.BytesIO(data), chunk_size=chunk_size) == 500


def test_count_lines_huge_single_line_is_memory_bounded() -> None:
    stream = lazy(32 * MiB, tail=b"\n")
    result: list[int] = []
    peak = peak_bytes(lambda: result.append(count_lines(stream)))
    assert result == [1]
    assert peak < MiB


def test_count_lines_cancel_checked_per_chunk() -> None:
    cancel = threading.Event()

    class CancelAfterFirstRead(io.BytesIO):
        def readinto(self, b: Any) -> int:
            n = super().readinto(b)
            cancel.set()
            return n

    with pytest.raises(ProcessingCancelled):
        count_lines(CancelAfterFirstRead(b"a\n" * 10_000), chunk_size=16, cancel=cancel)


# --- iter_lines_unbounded / pipeline / process_file ---------------------


def test_unbounded_handles_line_bigger_than_any_limit() -> None:
    big = b"z" * (200 * 1024)
    lines = list(iter_lines_unbounded(io.BytesIO(big + b"\r\nend")))
    assert lines == [big, b"end"]


def test_count_by_field_pipeline() -> None:
    log = (
        b"GET /a 200\n"
        b"GET /b 404\n"
        b"\n"  # blank line: skipped, not an IndexError
        b"POST /a 200\r\n"
    )
    counts = count_by_field(iter_lines(io.BytesIO(log), 64), field=-1)
    assert counts == {b"200": 2, b"404": 1}
    methods = count_by_field(iter_lines(io.BytesIO(log), 64), field=0)
    assert methods == {b"GET": 2, b"POST": 1}


def test_process_file_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "data.log"
    p.write_bytes(b"alpha\nbeta\n")
    seen: list[bytes] = []
    assert process_file(p, 64, lambda _, line: seen.append(line)) == 2
    assert seen == [b"alpha", b"beta"]


def test_process_file_missing_path_names_it(tmp_path: Path) -> None:
    missing = tmp_path / "nope.log"
    with pytest.raises(FileNotFoundError, match="nope.log"):
        process_file(missing, 64, lambda *_: None)
