"""
LEVEL 05 (advanced) - default= for encoding custom objects, object_hook for decoding
======================================================================================
You will learn
  * json can't serialize arbitrary objects (datetime, set, ...) out of the box
  * default= is called for anything the encoder doesn't know how to handle
  * object_hook is called on every decoded JSON object -- you can reconstruct
    custom types on the way back in, using a marker key you invented

Run: python level_05_custom_objects.py
"""
import json
from datetime import datetime, timezone


def main() -> None:
    event = {"name": "deploy", "at": datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)}

    # Without help, dumps() has no idea how to encode a datetime.
    try:
        json.dumps(event)
        raise AssertionError("expected TypeError")
    except TypeError as e:
        assert "not JSON serializable" in str(e)

    def encode_datetime(obj):
        """Called by dumps() for any object it doesn't recognize."""
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "iso": obj.isoformat()}
        raise TypeError(f"cannot serialize {type(obj)!r}")

    text = json.dumps(event, default=encode_datetime)
    assert '"__type__": "datetime"' in text
    assert "2026-01-15T12:30:00+00:00" in text

    # default= is one-way: loads() gives back a plain dict, not a datetime,
    # unless we tell it how to recognize our marker.
    plain = json.loads(text)
    assert isinstance(plain["at"], dict)          # NOT a datetime -- default= doesn't help here

    def decode_datetime(obj):
        """Called for every JSON object as it's decoded, innermost first."""
        if obj.get("__type__") == "datetime":
            return datetime.fromisoformat(obj["iso"])
        return obj

    restored = json.loads(text, object_hook=decode_datetime)
    assert isinstance(restored["at"], datetime)
    assert restored["at"] == event["at"]

    # object_hook fires on every nested object, not just the top level.
    nested_text = json.dumps(
        {"events": [event, {"name": "rollback", "at": event["at"]}]},
        default=encode_datetime,
    )
    nested_restored = json.loads(nested_text, object_hook=decode_datetime)
    assert all(isinstance(e["at"], datetime) for e in nested_restored["events"])

    print("OK")


if __name__ == "__main__":
    main()
