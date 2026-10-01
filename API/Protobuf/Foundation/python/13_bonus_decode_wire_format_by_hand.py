"""
FOUNDATION BONUS - What IS a protobuf message, really? (optional, read last)
=============================================================================
Level 00 encoded a message with SerializeToString and never asked what the
library did. This file answers that, completely, by decoding a real encoded
message BY HAND - no protobuf import anywhere. Check the imports: there are
none. Everything below is arithmetic on bytes.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is the library actually doing for me?" once you are curious.

THE ENTIRE FORMAT, in three rules
  1. A message is a flat sequence of (tag, value) records. No header, no
     footer, no field count, no length for the message as a whole. That is
     why level 09 needed framing.
  2. Each record starts with a TAG, itself a varint:
         tag = (field_number << 3) | wire_type
     Three low bits are the wire type, everything above is the field number.
  3. The wire type says how to read the value that follows:
         0 = VARINT            int32/int64/uint/bool/enum
         1 = I64               fixed 8 bytes (double, fixed64)
         2 = LEN               a varint length, then that many bytes
                               (string, bytes, nested message, packed repeated)
         5 = I32               fixed 4 bytes (float, fixed32)
  Rule 3 is why forward compatibility works (level 06): the wire type tells a
  parser how many bytes to skip even for a field number it has never seen.

VARINTS, the one trick worth knowing
  Small numbers should cost few bytes. So each byte carries 7 bits of the
  value in its low bits, and uses its HIGH bit as "another byte follows".
  Little-endian: the first byte holds the LEAST significant 7 bits.

You will learn
  - to read a tag byte and recover the field number and wire type
  - to decode a varint by hand, and why 300 needs two bytes
  - to read a length-delimited string: tag, length, then raw UTF-8
  - to ENCODE the same message from scratch and match the original bytes
  - why an unknown field can always be skipped safely

Run it   python 13_bonus_decode_wire_format_by_hand.py
"""

# These bytes are real. They were produced by level 06's schema:
#     message Order { int64 id = 1; string sku = 2; int32 qty = 3; }
# holding Order(id=300, sku="WIDGET-1", qty=7). You can verify that yourself
# with:  python 06_schema_evolution_rules.py
ENCODED = bytes.fromhex("08ac0212085749444745542d311807")

WIRE_TYPE_NAMES = {0: "VARINT", 1: "I64", 2: "LEN", 5: "I32"}

# The schema, as a plain dict - this is the ONLY thing the bytes cannot tell
# us. Field NAMES are not on the wire (level 01), so a hand decoder has to be
# told them. This dict is standing in for the generated code.
SCHEMA = {1: ("id", "int64"), 2: ("sku", "string"), 3: ("qty", "int32")}


def read_varint(data: bytes, position: int) -> tuple[int, int, list[str]]:
    """Decode one varint. Returns (value, next_position, per-byte explanation)."""
    value, shift, steps = 0, 0, []
    while True:
        byte = data[position]
        position += 1
        payload = byte & 0x7F            # the 7 data bits
        more = bool(byte & 0x80)         # the high bit: "another byte follows"
        value |= payload << shift        # little-endian: first byte is least significant
        steps.append(
            f"0x{byte:02x} = {byte:08b} -> continuation={int(more)}, "
            f"7 bits {payload:07b} << {shift} = {payload << shift}"
        )
        if not more:
            return value, position, steps
        shift += 7


def write_varint(value: int) -> bytes:
    """The exact inverse of read_varint."""
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)   # low 7 bits + "more follows"
        value >>= 7
    out.append(value)                        # last byte, high bit clear
    return bytes(out)


def decode(data: bytes) -> dict:
    """Walk the whole message, narrating every byte."""
    fields, position = {}, 0
    while position < len(data):
        start = position
        tag, position, tag_steps = read_varint(data, position)

        # Rule 2, undone: split the tag back into its two halves.
        field_number = tag >> 3
        wire_type = tag & 0x07
        name, declared = SCHEMA.get(field_number, (f"<unknown {field_number}>", "?"))

        print(f"  byte {start:>2}: tag varint")
        for step in tag_steps:
            print(f"            {step}")
        print(f"            tag = {tag} = (field {field_number} << 3) | {wire_type}"
              f"  -> field {field_number} ({name}), wire type {wire_type} "
              f"({WIRE_TYPE_NAMES[wire_type]})")

        if wire_type == 0:
            value, position, value_steps = read_varint(data, position)
            for step in value_steps:
                print(f"            value: {step}")
            print(f"            => {name} = {value}   ({declared})")
        elif wire_type == 2:
            length, position, length_steps = read_varint(data, position)
            for step in length_steps:
                print(f"            length: {step}")
            raw = data[position:position + length]
            position += length
            value = raw.decode("utf-8")      # a protobuf string is UTF-8 (level 10)
            print(f"            {length} bytes follow: {raw.hex()}")
            print(f"            as UTF-8 -> {value!r}")
            print(f"            => {name} = {value!r}   ({declared})")
        else:
            raise AssertionError(f"wire type {wire_type} not needed for this message")

        fields[name] = value
        print()
    return fields


if __name__ == "__main__":
    print("== 1. the varint trick, in isolation ==")
    # Why 300 costs two bytes but 127 costs one.
    for number in (0, 1, 7, 127, 128, 300, 16384):
        encoded = write_varint(number)
        back, _, _ = read_varint(encoded, 0)
        print(f"  {number:>6} -> {encoded.hex():<10} ({len(encoded)} byte(s))  "
              f"-> decodes to {back}")
        assert back == number
    print("  127 = 1111111 fits in one byte's 7 data bits. 128 needs an eighth bit,")
    print("  so it spills: 0x80 0x01 = (0000000) + (0000001 << 7) = 128.")
    # Prove the little-endian ordering explicitly on 300.
    assert write_varint(300) == bytes([0xAC, 0x02])
    assert (0xAC & 0x7F) | (0x02 << 7) == 300
    print("  300 = 0xac 0x02: (0xac & 0x7f) | (0x02 << 7) = 44 + 256 = 300")

    print("\n== 2. decoding the real message, byte by byte ==")
    print(f"  input: {len(ENCODED)} bytes  {ENCODED.hex()}")
    print()
    fields = decode(ENCODED)

    print("== 3. the result ==")
    print(f"  {fields}")
    assert fields == {"id": 300, "sku": "WIDGET-1", "qty": 7}
    print("  decoded with zero protobuf code - just shifts, masks and a UTF-8 decode.")

    print("\n== 4. now ENCODE it again from scratch ==")
    # Build the same message the way the library does: for each field, emit a
    # tag, then the value in the form its wire type demands.
    parts = []
    parts.append(write_varint((1 << 3) | 0) + write_varint(300))          # id
    sku = b"WIDGET-1"
    parts.append(write_varint((2 << 3) | 2) + write_varint(len(sku)) + sku)  # sku
    parts.append(write_varint((3 << 3) | 0) + write_varint(7))            # qty
    rebuilt = b"".join(parts)
    print(f"  field 1 (id=300)        : {parts[0].hex()}")
    print(f"  field 2 (sku='WIDGET-1'): {parts[1].hex()}")
    print(f"  field 3 (qty=7)         : {parts[2].hex()}")
    print(f"  joined                  : {rebuilt.hex()}")
    print(f"  original                : {ENCODED.hex()}")
    assert rebuilt == ENCODED, "a hand-built message matches the library's output exactly"
    print("  IDENTICAL. There is no hidden header, checksum or padding - a protobuf")
    print("  message is exactly the concatenation of its encoded fields.")

    print("\n== 5. why unknown fields can always be skipped ==")
    # Append a field number 99 the SCHEMA dict has never heard of, with a
    # wire type we can nonetheless measure. This is level 06's forward
    # compatibility, seen from underneath.
    unknown = write_varint((99 << 3) | 2) + write_varint(4) + b"\xde\xad\xbe\xef"
    extended = ENCODED + unknown
    print(f"  appended field 99 as LEN with 4 bytes -> {len(extended)} bytes total")
    position, skipped = 0, []
    while position < len(extended):
        tag, position, _ = read_varint(extended, position)
        number, wire_type = tag >> 3, tag & 0x07
        if wire_type == 0:
            _, position, _ = read_varint(extended, position)
        elif wire_type == 2:
            length, position, _ = read_varint(extended, position)
            position += length
        elif wire_type == 1:
            position += 8
        elif wire_type == 5:
            position += 4
        if number not in SCHEMA:
            skipped.append(number)
    print(f"  walked the whole message without error; unknown field numbers: {skipped}")
    assert skipped == [99] and position == len(extended)
    print("  The parser never needed to know what field 99 MEANS - only how long")
    print("  it is, and the wire type in the tag always says that. Preserving")
    print("  those skipped bytes is what makes level 06's round trip lossless.")

    print("\n== 6. what you just did ==")
    print("  You implemented a protobuf decoder and encoder. The real one adds")
    print("  zigzag (sint32/sint64), fixed-width types, packed repeated fields,")
    print("  maps and unknown-field retention - but not a single new concept.")
    print("  Tag, wire type, value. That is the format.")

    print("\nOK")
