"""
FOUNDATION LEVEL 04 - Presence: the proto3 gotcha worth knowing before you ship
================================================================================
This is the level that saves you a production incident.

proto3 has no null. Every scalar field always has a value, and if that value
is the type's default (0, "", false) the encoder SKIPS it entirely to save
space. The consequence: for a plain `int32`, "I never set this" and "I
deliberately set this to zero" produce byte-for-byte IDENTICAL output. The
information that you meant zero is not compressed - it is destroyed.

That is fine for a counter. It is a disaster for a PATCH request ("set the
discount to 0%"), a boolean flag ("disable this"), or any field where zero is
a meaningful choice rather than an absence.

The fix is one keyword: mark the field `optional`. proto3 then tracks
presence for it, emits it even when zero, and gives you HasField().

You will learn
  * the proto3 default for every scalar type, and that there is no null
  * PROOF: an unset plain int32 and an explicit 0 encode to the same bytes
  * what `optional` changes - on the wire and in the generated API
  * that HasField() raises on a non-optional scalar, on purpose
  * which field kinds already had presence all along (message, oneof, optional)
  * the practical rule for when to reach for `optional`

Run it   python 04_presence_and_defaults.py
"""
import l04_presence_pb2 as pb

if __name__ == "__main__":
    print("== 1. proto3 defaults: there is no null ==")
    blank = pb.Reading()
    print(f"  sensor_id (string) = {blank.sensor_id!r}")
    print(f"  celsius   (int32 ) = {blank.celsius!r}")
    print(f"  humidity  (int32 ) = {blank.humidity!r}   <- optional, but still reads as 0")
    assert (blank.sensor_id, blank.celsius, blank.humidity) == ("", 0, 0)
    print("  a fresh message is never 'empty' - it is fully populated with defaults.")
    print(f"  ...yet it encodes to {len(blank.SerializeToString())} bytes: defaults are not sent.")
    assert blank.SerializeToString() == b""

    print("\n== 2. THE GOTCHA: unset vs explicit zero, on a PLAIN int32 ==")
    never_set = pb.Reading(sensor_id="s1")
    set_to_zero = pb.Reading(sensor_id="s1", celsius=0)   # deliberately zero!
    a, b = never_set.SerializeToString(), set_to_zero.SerializeToString()
    print(f"  Reading(sensor_id='s1')            -> {len(a)} bytes: {a.hex()}")
    print(f"  Reading(sensor_id='s1', celsius=0) -> {len(b)} bytes: {b.hex()}")
    assert a == b, "this is the whole point: they are indistinguishable"
    print("  IDENTICAL. The `celsius=0` never made it onto the wire, so no reader")
    print("  anywhere - in any language - can tell these two apart. Ever.")

    # And the generated API refuses to lie to you about it: asking "was it set?"
    # for a field that cannot answer raises instead of guessing.
    try:
        never_set.HasField("celsius")
        raise AssertionError("expected HasField to reject a non-optional scalar")
    except ValueError as e:
        print(f"  HasField('celsius') -> ValueError: {str(e)[:58]}...")
        print("  (the library would rather raise than return a meaningless answer)")

    print("\n== 3. what `optional` changes ==")
    # Same type, same zero value - but presence is tracked now.
    no_hum = pb.Reading(sensor_id="s1")
    zero_hum = pb.Reading(sensor_id="s1", humidity=0)      # deliberately zero!
    c, d = no_hum.SerializeToString(), zero_hum.SerializeToString()
    print(f"  Reading(sensor_id='s1')             -> {len(c)} bytes: {c.hex()}")
    print(f"  Reading(sensor_id='s1', humidity=0) -> {len(d)} bytes: {d.hex()}")
    assert c != d, "optional makes the explicit zero visible"
    print("  DIFFERENT - the optional field emitted `18 00` = 'field 3, value 0'.")
    print(f"  HasField('humidity'): unset -> {no_hum.HasField('humidity')}, "
          f"explicit 0 -> {zero_hum.HasField('humidity')}")
    assert not no_hum.HasField("humidity")
    assert zero_hum.HasField("humidity")

    # Crucially, presence survives the round trip. It is carried by the bytes,
    # not by some flag that only exists in the sender's memory.
    reread = pb.Reading()
    reread.ParseFromString(d)
    assert reread.HasField("humidity") and reread.humidity == 0
    print(f"  after a full encode/decode, HasField('humidity') is still "
          f"{reread.HasField('humidity')} -> presence is ON THE WIRE, not in RAM")

    # ClearField takes it back to genuinely absent.
    reread.ClearField("humidity")
    assert not reread.HasField("humidity") and reread.humidity == 0
    print("  ClearField('humidity') -> absent again (and reads as 0 once more)")

    print("\n== 4. which field kinds have presence already? ==")
    rows = [
        ("plain scalar  (celsius)",     "NO  - 0 and unset are the same bytes"),
        ("optional scalar (humidity)",  "YES - HasField works"),
        ("message field",               "YES - always had it (see level 02)"),
        ("oneof member",                "YES - WhichOneof tells you (see level 07)"),
        ("repeated field",              "NO  - and it does not need it: empty IS the empty state"),
    ]
    for kind, has in rows:
        print(f"  {kind:<27} {has}")

    print("\n== 5. the practical rule ==")
    print("  Ask: 'is the zero value a MEANINGFUL choice a user could make?'")
    print("    retry_count, bytes_sent, error_total   -> plain scalar. 0 means nothing happened.")
    print("    discount_percent, temperature_c, limit -> `optional`. 0 is a real, chosen value.")
    print("  Any PATCH/update API needs `optional` almost everywhere, because there")
    print("  the whole question is 'did the caller mention this field or not?'.")
    print("  Cost of being wrong later: adding `optional` to a shipped plain scalar")
    print("  is wire-compatible, so it is a safe fix - but every already-stored")
    print("  zero is gone for good, and no migration can recover it.")

    print("\nOK")
