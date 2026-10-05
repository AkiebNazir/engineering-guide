"""
LEVEL 09 (advanced) - production traps: duplicate keys, and NaN/Infinity
===========================================================================
You will learn
  * duplicate object keys in JSON text silently keep only the LAST value --
    no error, no warning, data quietly disappears
  * Python's json accepts/emits NaN, Infinity, -Infinity by default -- valid
    Python float literals, but NOT valid per the JSON spec (RFC 8259)
  * how to catch both: object_pairs_hook to detect duplicates, allow_nan=False
    to enforce strict, spec-compliant JSON

Run: python level_09_duplicate_keys_and_nan.py
"""
import json


def main() -> None:
    # --- gotcha 1: duplicate keys, last one wins, silently ---
    text = '{"role": "viewer", "name": "temp", "role": "admin"}'
    result = json.loads(text)
    assert result == {"role": "admin", "name": "temp"}    # "viewer" vanished with no error

    # Fix: object_pairs_hook sees every key-value pair BEFORE de-duplication happens,
    # so you can detect (and reject, or log) the collision yourself.
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError(f"duplicate key detected: {key!r}")
            seen[key] = value
        return seen

    try:
        json.loads(text, object_pairs_hook=reject_duplicates)
        raise AssertionError("expected ValueError for duplicate key")
    except ValueError as e:
        assert "role" in str(e)

    clean_text = '{"role": "admin", "name": "temp"}'
    assert json.loads(clean_text, object_pairs_hook=reject_duplicates) == {
        "role": "admin", "name": "temp",
    }

    # --- gotcha 2: NaN/Infinity are accepted by default -- not valid strict JSON ---
    payload = {"score": float("nan"), "limit": float("inf")}
    text2 = json.dumps(payload)
    assert "NaN" in text2 and "Infinity" in text2   # this is NOT valid per RFC 8259

    round_tripped = json.loads(text2)
    assert round_tripped["limit"] == float("inf")
    assert round_tripped["score"] != round_tripped["score"]   # NaN != NaN, even itself

    # A strict, spec-compliant JSON consumer elsewhere would reject this text outright.
    # allow_nan=False makes OUR OWN encoder refuse to produce it in the first place.
    try:
        json.dumps(payload, allow_nan=False)
        raise AssertionError("expected ValueError with allow_nan=False")
    except ValueError as e:
        assert "not JSON compliant" in str(e) or "NaN" in str(e)

    # And on the decode side, parse_constant lets you refuse to accept it too.
    def reject_constant(name: str):
        raise ValueError(f"non-standard JSON constant encountered: {name}")

    try:
        json.loads(text2, parse_constant=reject_constant)
        raise AssertionError("expected ValueError decoding NaN strictly")
    except ValueError as e:
        assert "NaN" in str(e)

    print("OK")


if __name__ == "__main__":
    main()
