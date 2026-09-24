"""
LAB 01 (basic) - How Protobuf works on the wire: encode and decode by hand
===========================================================================
You will learn
  * a message is just a sequence of  [tag][value]  pairs - there are NO field names on the wire
      tag = (field_number << 3) | wire_type
  * the 4 wire types you need:   0 varint | 1 fixed64 | 2 length-delimited | 5 fixed32
  * VARINT: 7 bits per byte, the top bit says "more bytes follow"   (300 -> AC 02)
  * ZigZag (sint32/sint64): maps -1,1,-2,2 ... to 1,2,3,4 so small negatives stay small
  * why negative int32 costs 10 bytes and sint32 costs 1
  * why field numbers 1-15 are "cheap" (one-byte tag) and 16+ cost two
  * you will write an encoder, check it against the real library byte for byte,
    then write a decoder like `protoc --decode_raw` that needs NO schema

Needs   pip install protobuf     (generated code: demo_pb2.py, made by ../generate.sh)
Run it  python 01_wire_format_by_hand.py
"""
import json

import demo_pb2

VARINT, FIXED64, LEN, FIXED32 = 0, 1, 2, 5


# ----------------------------------------------------------- primitives -----
def enc_varint(n: int) -> bytes:
    if n < 0:
        n &= (1 << 64) - 1                     # negatives are sign-extended to 64 bits => 10 bytes
    out = bytearray()
    while True:
        low7 = n & 0x7F
        n >>= 7
        if n:
            out.append(low7 | 0x80)            # continuation bit set: more coming
        else:
            out.append(low7)
            return bytes(out)


def dec_varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def zigzag(n: int, bits: int = 32) -> int:
    return ((n << 1) ^ (n >> (bits - 1))) & ((1 << bits) - 1)


def unzigzag(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


def tag(field: int, wire_type: int) -> bytes:
    return enc_varint((field << 3) | wire_type)


# ------------------------------------------------------------- encoder ------
def encode_user(id_: int, name: str, email: str) -> bytes:
    """Same message as demo.v1.User(id=..., name=..., email=...), by hand."""
    n, e = name.encode(), email.encode()
    return (tag(1, VARINT) + enc_varint(id_)                       # field 1: int64  -> varint
            + tag(2, LEN) + enc_varint(len(n)) + n                 # field 2: string -> length + bytes
            + tag(3, LEN) + enc_varint(len(e)) + e)                # field 3: string


# ------------------------------------------------- schema-less decoder -------
def decode_raw(buf: bytes, indent: int = 0) -> list[str]:
    """Like `protoc --decode_raw`: field numbers and wire types are all the wire tells you."""
    lines, i, pad = [], 0, "  " * indent
    while i < len(buf):
        key, i = dec_varint(buf, i)
        field, wt = key >> 3, key & 7
        if wt == VARINT:
            v, i = dec_varint(buf, i)
            lines.append(f"{pad}{field}: {v}   (varint)")
        elif wt == LEN:
            n, i = dec_varint(buf, i)
            chunk, i = buf[i:i + n], i + n
            try:
                text = chunk.decode("utf-8")
                assert text.isprintable()
                lines.append(f"{pad}{field}: {text!r}   (len={n}: string OR bytes OR nested message OR packed list)")
            except (UnicodeDecodeError, AssertionError):
                lines.append(f"{pad}{field}: <{n} bytes {chunk.hex(' ')}>")
        elif wt == FIXED64:
            lines.append(f"{pad}{field}: {buf[i:i + 8].hex(' ')}   (fixed64)")
            i += 8
        elif wt == FIXED32:
            lines.append(f"{pad}{field}: {buf[i:i + 4].hex(' ')}   (fixed32)")
            i += 4
        else:
            raise ValueError(f"unsupported wire type {wt}")
    return lines


if __name__ == "__main__":
    print("== 1. varints ==")
    for n in (1, 127, 128, 150, 300, 16384):
        print(f"  {n:>6} -> {enc_varint(n).hex(' '):<9} ({len(enc_varint(n))} byte{'s' * (len(enc_varint(n)) > 1)})")
    assert enc_varint(150) == bytes([0x96, 0x01])                  # the classic textbook example
    assert enc_varint(300) == bytes([0xAC, 0x02])
    assert all(dec_varint(enc_varint(n), 0)[0] == n for n in (0, 1, 127, 128, 300, 2**40))
    print("  150 = 0b10010110 -> low 7 bits 0010110 (+continuation bit) = 0x96, then 0b1 = 0x01")

    print("\n== 2. our encoder vs the real library, byte for byte ==")
    mine = encode_user(150, "Ana", "a@x.io")
    real = demo_pb2.User(id=150, name="Ana", email="a@x.io").SerializeToString()
    print("  mine:", mine.hex(" "))
    print("  real:", real.hex(" "))
    assert mine == real

    print("\n== 3. the tag byte is (field << 3) | wire_type ==")
    print("  field 1 varint -> 0x%02x ;  field 2 len -> 0x%02x ;  field 3 len -> 0x%02x" % (
        tag(1, VARINT)[0], tag(2, LEN)[0], tag(3, LEN)[0]))
    assert tag(1, VARINT) == b"\x08" and tag(2, LEN) == b"\x12"
    print(f"  field 15 tag: {len(tag(15, VARINT))} byte ; field 16 tag: {len(tag(16, VARINT))} bytes  <- why 1-15 are precious")
    assert len(tag(15, VARINT)) == 1 and len(tag(16, VARINT)) == 2

    print("\n== 4. decode with NO schema ==")
    for line in decode_raw(real):
        print("  ", line)
    print("   (the names 'id', 'name', 'email' are not in the bytes - that is why the format is small,")
    print("    and why you must NEVER change a field number)")

    print("\n== 5. negative numbers: int32 vs sint32 (ZigZag) ==")
    a = demo_pb2.User(legacy_score=-1).SerializeToString()
    b = demo_pb2.User(balance_delta=-1).SerializeToString()
    print(f"  int32  -1 -> {len(a):>2} bytes  {a.hex(' ')}")
    print(f"  sint32 -1 -> {len(b):>2} bytes  {b.hex(' ')}")
    assert len(a) == 11 and len(b) == 2 and b[1] == zigzag(-1) == 1
    print("  zigzag:", {n: zigzag(n) for n in (0, -1, 1, -2, 2, -3)}, "  back:", [unzigzag(zigzag(n)) for n in (-1, 1, -2)])

    print("\n== 6. repeated scalars are PACKED: one tag, one length, then all the values ==")
    packed = demo_pb2.User(scores=[3, 270]).SerializeToString()
    print("  scores=[3, 270]      ->", packed.hex(" "))
    print("  = tag(17, LEN)=8a 01 | length=3 | varint 3 = 03 | varint 270 = 8e 02")
    assert packed == bytes([0x8A, 0x01, 3, 0x03, 0x8E, 0x02])
    unpacked = demo_pb2.User(tags=["a", "b"]).SerializeToString()      # strings/messages are NEVER packed
    print("  tags=['a','b']       ->", unpacked.hex(" "), "(strings repeat the tag for every element)")
    assert unpacked == bytes([0x2A, 1, 0x61, 0x2A, 1, 0x62])

    print("\n== 7. defaults cost nothing: unset (or zero) fields are simply absent ==")
    empty = demo_pb2.User(id=0, name="", role=demo_pb2.ROLE_UNSPECIFIED, active=False).SerializeToString()
    print(f"  all-defaults message -> {len(empty)} bytes")
    assert empty == b""

    print("\n== 8. size vs JSON for the same data ==")
    js = json.dumps({"id": 150, "name": "Ana", "email": "a@x.io"}, separators=(",", ":"))
    print(f"  JSON {len(js)} bytes   Protobuf {len(real)} bytes   ({len(js) / len(real):.1f}x smaller)")
    print("\nOK")
