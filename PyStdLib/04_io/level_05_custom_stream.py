"""
LEVEL 05 (advanced) - subclassing io.RawIOBase for a minimal custom stream
============================================================================
You will learn
  * io.RawIOBase is the base class real files and sockets ultimately sit on
  * you only need to implement readinto()/writable()/readable() for a minimal
    read-only source -- the rest of the io machinery (readline, iteration) comes free
  * wrapping a raw stream in io.BufferedReader gives it efficient chunked reads

Run: python level_05_custom_stream.py
"""
import io


class CountingStream(io.RawIOBase):
    """A read-only raw stream that generates 'N\\n' for N = 0..limit-1, on the fly.

    No backing file or buffer exists anywhere -- bytes are produced lazily inside
    readinto(). This is the minimal contract a custom stream must satisfy.
    """

    def __init__(self, limit: int):
        self._limit = limit
        self._next = 0
        self._pending = b""

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def _refill(self) -> None:
        if not self._pending and self._next < self._limit:
            self._pending = f"{self._next}\n".encode("ascii")
            self._next += 1

    def readinto(self, b: bytearray) -> int:
        """The one method RawIOBase truly requires: fill buffer b, return bytes written."""
        self._refill()
        if not self._pending:
            return 0                      # 0 == EOF
        n = min(len(b), len(self._pending))
        b[:n] = self._pending[:n]
        self._pending = self._pending[n:]
        return n


def main() -> None:
    raw = CountingStream(limit=5)
    assert raw.readable() is True
    assert raw.writable() is False

    # readinto() on its own only fills whatever buffer size you give it.
    small_raw = CountingStream(limit=5)
    chunk = bytearray(2)
    n = small_raw.readinto(chunk)
    assert n == 2
    assert bytes(chunk[:n]) == b"0\n"

    # Wrap in BufferedReader to get read()/readline()/iteration for free, buffered.
    buffered = io.BufferedReader(CountingStream(limit=5))
    assert buffered.readline() == b"0\n"
    assert buffered.readline() == b"1\n"
    remaining = buffered.read()
    assert remaining == b"2\n3\n4\n"
    assert buffered.read() == b""     # EOF reached, further reads return empty

    # Full iteration from scratch, line by line, using nothing but our custom stream.
    lines = list(io.BufferedReader(CountingStream(limit=3)))
    assert lines == [b"0\n", b"1\n", b"2\n"]

    # Writing to a read-only stream is refused, exactly like a real read-only file.
    try:
        io.BufferedReader(CountingStream(limit=1)).write(b"x")
        raise AssertionError("expected an error writing to a read-only stream")
    except (io.UnsupportedOperation, AttributeError):
        pass

    print("OK")


if __name__ == "__main__":
    main()
