"""
LEVEL 08 (advanced) - interop: json + io.StringIO, encoding/decoding in memory
=================================================================================
You will learn
  * json.dump()/json.load() only need "something with .write()/.read()" --
    io.StringIO qualifies, so you can use the file-based API without touching disk
  * this is exactly how you'd unit-test code that "writes JSON to a file" fast

Run: python level_08_stringio_interop.py
"""
import io
import json


def render_report(events: list[dict]) -> str:
    """A function written as if it took a real file -- but it only needs .write()."""
    buf = io.StringIO()
    json.dump({"count": len(events), "events": events}, buf, indent=2, sort_keys=True)
    return buf.getvalue()


def parse_report(text: str) -> dict:
    """Symmetric: json.load() only needs .read()."""
    buf = io.StringIO(text)
    return json.load(buf)


def main() -> None:
    events = [{"type": "start"}, {"type": "stop"}]

    rendered = render_report(events)
    assert '"count": 2' in rendered
    assert rendered.startswith("{\n")   # indent= took effect, same as with a real file

    parsed = parse_report(rendered)
    assert parsed == {"count": 2, "events": events}

    # A StringIO can be written to incrementally with multiple json.dump() calls
    # (JSON Lines style) -- useful for append-only logs without reopening a file.
    log = io.StringIO()
    for event in events:
        json.dump(event, log)
        log.write("\n")
    log_text = log.getvalue()
    lines = log_text.strip().splitlines()
    assert len(lines) == 2
    decoded_lines = [json.loads(line) for line in lines]
    assert decoded_lines == events

    # Reading a StringIO twice needs a seek(0), exactly like a real file.
    log.seek(0)
    assert log.read() == log_text

    print("OK")


if __name__ == "__main__":
    main()
