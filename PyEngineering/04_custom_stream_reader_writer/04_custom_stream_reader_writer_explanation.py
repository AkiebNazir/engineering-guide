"""
04 · Custom Stream Reader Writer
================================

WHAT WE'RE BUILDING
--------------------
A custom Python file-like object that implements `read()`, `write()`, and `close()`.
It acts as a wrapper around another stream, performing on-the-fly transformations
(such as compression, encryption, or chunked reading).

WHY THIS MATTERS
----------------
In real systems, you don't load a 10GB file into memory to compress it. You stream
it chunk by chunk. Implementing the `io.RawIOBase` or `io.TextIOBase` interfaces
allows your custom stream to be used anywhere standard Python file objects are
expected.
"""

import io

class TransformingReader(io.IOBase):
    def __init__(self, underlying_stream):
        self._stream = underlying_stream

    def read(self, size=-1):
        data = self._stream.read(size)
        return data.upper() if isinstance(data, bytes) else data

    def readable(self):
        return True
