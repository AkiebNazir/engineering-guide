"""
FOUNDATION LEVEL 00 (start here) - A single Protobuf message, end to end
=========================================================================
If someone says "build me a basic Protobuf message", THIS is what they mean:
one .proto file describing one message, compiled into real code, then a value
built, encoded to bytes, and decoded back. Four steps, one field. Everything
later in this folder is "add one more piece" instead of "understand it all".

THE MENTAL MODEL (read this before the code)
  Protobuf is two things bolted together:
    1. a SCHEMA language  - ../proto/l00_ping.proto says a Ping has one
       string called `text`, numbered 1. You write this once, by hand.
    2. a BINARY ENCODING  - a compact byte layout for values of that schema.
  A compiler (protoc) reads #1 and writes you a class. The class knows how to
  turn itself into #2 and back.

  The trade-off, stated plainly: protobuf gives up being human-readable to
  become small and fast to parse. JSON ships the field NAME with every value
  ("text" costs 6 bytes every single time) and every number as ASCII digits;
  protobuf ships a one-byte tag instead of the name, and packs numbers as raw
  bytes. You cannot read the result in a text editor, and you cannot decode it
  at all without the schema - that is the price. In exchange you get a payload
  that is typically 20-60% smaller and parses several times faster, plus a
  schema the compiler can check for you in every language at once.

You will learn
  * the four steps of every protobuf program: schema -> generate -> encode -> decode
  * that the generated class is ordinary code you import like any other module
  * what the encoded bytes actually look like, and why they are not text
  * why protobuf is smaller than the equivalent JSON, measured, not asserted
  * that decoding is exact: what goes in comes back out unchanged

Run it   python 00_single_message_end_to_end.py
"""
import json

# STEP 2 of 4 happened before you ran this: ../generate.sh ran protoc over
# ../proto/l00_ping.proto and wrote l00_ping_pb2.py next to this file. That
# generated module is checked in, so there is nothing to build right now.
# Open it if you are curious - but you never edit generated code by hand.
import l00_ping_pb2 as pb

if __name__ == "__main__":
    print("== step 3: build a value ==")
    # The generated class behaves like a normal Python object, except it is
    # strictly typed: only the fields the schema declared exist, and only
    # with the declared types.
    ping = pb.Ping(text="hello, protobuf")
    print(f"  in python : {ping!r}".replace("\n", " "))

    # Strict typing is a feature, not a nuisance - the schema is the contract,
    # so a typo is caught here rather than in production on another continent.
    try:
        pb.Ping(txet="typo")
        raise AssertionError("expected the typo to be rejected")
    except ValueError:
        print('  pb.Ping(txet="typo") -> ValueError (the schema has no field `txet`)')

    print("\n== step 4a: encode to bytes ==")
    # SerializeToString is badly named: it returns `bytes`, not `str`. These
    # bytes are the whole point of protobuf - they are what you would write to
    # a file, put on a queue, or hand to gRPC.
    data = ping.SerializeToString()
    print(f"  {len(data)} bytes, as hex : {data.hex()}")
    print(f"  the same bytes, raw       : {data!r}")
    print("  notice: the field NAME 'text' is nowhere in there. Byte 0x0a is a")
    print("  one-byte tag meaning 'field number 1, length-delimited'. Level 13")
    print("  decodes all of this by hand if you want to see every byte.")

    print("\n== step 4b: decode it back ==")
    # Parsing needs the schema - specifically, the same message type. The bytes
    # alone do not say what they are; that knowledge lives in the .proto.
    decoded = pb.Ping()
    decoded.ParseFromString(data)
    print(f"  decoded.text = {decoded.text!r}")

    # The round trip is exact. This is the claim the whole format rests on.
    assert decoded.text == "hello, protobuf"
    assert decoded == ping, "a decoded message equals the one that was encoded"

    print("\n== why bother? the size trade-off, measured ==")
    as_json = json.dumps({"text": "hello, protobuf"}).encode()
    print(f"  protobuf : {len(data):>3} bytes  {data.hex()}")
    print(f"  JSON     : {len(as_json):>3} bytes  {as_json.decode()}")
    saved = 100 - round(100 * len(data) / len(as_json))
    print(f"  -> {saved}% smaller on a message with ONE short field. The gap widens")
    print("     with more fields and with numbers, because JSON re-sends every")
    print("     field name as text and every number as ASCII digits.")
    assert len(data) < len(as_json)

    # ... and the cost, stated honestly: without l00_ping_pb2 these bytes are
    # unreadable noise. JSON is self-describing; protobuf is not. That is the
    # deal you are making, and levels 01 and 06 are about living with it well.
    print("\n== the cost ==")
    print("  JSON can be read by anyone with a text editor. These 17 bytes cannot")
    print("  be decoded by anyone who does not also have l00_ping.proto. Protobuf")
    print("  trades self-description for size; the schema becomes a hard dependency.")

    print("\nOK")
