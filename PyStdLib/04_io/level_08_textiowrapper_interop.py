"""
LEVEL 08 (advanced) - io.TextIOWrapper: putting a text face on a binary stream
================================================================================
You will learn
  * open(path, 'r') is really: open a raw/buffered binary stream, then wrap it in
    a TextIOWrapper that handles decoding
  * you can do that wrapping yourself, over ANY binary stream -- including io.BytesIO
  * detach() lets you peel the text layer back off, recovering the raw binary stream

Run: python level_08_textiowrapper_interop.py
"""
import io


def main() -> None:
    # A binary-only source: no concept of str, just bytes.
    binary_source = io.BytesIO("hola, ñoño ☃".encode("utf-8"))

    # Wrap it in a TextIOWrapper to read it as decoded text, same as a real text file.
    text_view = io.TextIOWrapper(binary_source, encoding="utf-8")
    assert text_view.read() == "hola, ñoño ☃"

    # Writing works the same way: encode Python str -> bytes on the underlying stream.
    sink = io.BytesIO()
    writer = io.TextIOWrapper(sink, encoding="utf-8", newline="")
    writer.write("line one\n")
    writer.write("line two\n")
    writer.flush()                      # TextIOWrapper buffers too -- flush before reading sink
    assert sink.getvalue() == b"line one\nline two\n"

    # detach() separates the text wrapper from its binary stream, handing the
    # binary stream back untouched -- useful when a library gives you text but you
    # need to pass the raw bytes on to something else (e.g. a hash function).
    sink2 = io.BytesIO()
    writer2 = io.TextIOWrapper(sink2, encoding="utf-8")
    writer2.write("payload")
    writer2.flush()
    raw_stream = writer2.detach()
    assert raw_stream is sink2
    assert raw_stream.getvalue() == b"payload"
    # the wrapper is now unusable -- it no longer owns a buffer
    try:
        writer2.write("more")
        raise AssertionError("expected ValueError after detach()")
    except ValueError:
        pass

    # This is exactly how sys.stdin/sys.stdout work: a TextIOWrapper over a
    # binary buffer, exposed as .buffer.
    import sys
    assert isinstance(sys.stdout, io.TextIOWrapper) or hasattr(sys.stdout, "buffer")

    print("OK")


if __name__ == "__main__":
    main()
